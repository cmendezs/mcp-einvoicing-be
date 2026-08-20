"""Belgian invoice validation — subclasses BaseDocumentValidator from mcp-einvoicing-core.

Three validation paths for peppol-bis-3/pint-eu, tried in order, plus one
package-local overlay:
1. Local full Schematron XSLT (if ever downloaded via specs/download.py):
   delegates to core's load_schematron_validator() for full Peppol BIS 3.0
   rule coverage (base + Peppol overlay). Not currently populated — see the
   [GAP id=core.schematron.be_bundled_xslt] note below; this slot stays wired
   for if/when the overlay's licensing question resolves.
2. Core-provided EN 16931 base Schematron (always available — bundled in
   mcp-einvoicing-core >= 1.18.0): delegates to core's
   en16931_base_schematron_validator(). Checks the ~50 CEN EN16931 BR-* rules
   (structural + arithmetic/totals), but NOT the Peppol-specific overlay
   (profile/process ID registration, EndpointID scheme, narrowed code lists).
   Results carry metadata.scope="en16931-base-only" and an explicit warning —
   never presented as full Peppol BIS3 conformance. See
   context-library/decisions/peppol-schematron-artifact.md for why the
   overlay itself cannot ship yet.
3. Neither loaded (e.g. the [xslt2] extra is not installed): returns an
   explicit "unavailable" result (valid=False, an error explaining why)
   rather than a silent pass. v0.7.0 removed the package's own hand-rolled
   Peppol BIS 3.0 base-rule approximation (PEPPOL_BIS3_RULES) — it covered
   ~10 of the ~50+ real CEN/Peppol rules, no arithmetic checks, and had
   carried a rule-ID mislabeling bug (fixed in v0.6.0) before removal. Do not
   reintroduce a package-local hand-rolled subset — see
   context-library/roadmap-2026.md [CORE-PEPPOL-SCHEMATRON-1] and
   [CORE-EN16931-BASE-SCHEMATRON-1].
4. XPath overlay: evaluates hand-coded rules for the mercurius profile only
   (MERCURIUS_RULES — Mercurius-specific checks, not a Peppol/EN16931 base
   ruleset; see standards/mercurius.py).

BE-SC-1 (resolved): _evaluate_rule uses real lxml XPath evaluation.

[GAP id=core.schematron.be_bundled_xslt] (partially resolved, 2026-08-20 —
see [CORE-EN16931-BASE-SCHEMATRON-1]): the CEN EN16931 base rules are now
served from a compiled artifact bundled in mcp-einvoicing-core itself (path 2
above) — this package no longer needs its own copy of that half. What
remains genuinely open is the Peppol-specific overlay
(PEPPOL-EN16931-UBL.sch): its license is unclear ("reproduced with
permission from CEN", no redistribution terms stated, no repo-level LICENSE
either — confirmed against the live OpenPEPPOL/peppol-bis-invoice-3 repo) and
stays unbundled everywhere, per
context-library/decisions/peppol-schematron-artifact.md. specs/peppol_bis_3/
here still only ships CEN-EN16931-UBL.sch as a reference/verification copy
(now redundant with core's own compiled version, but left in place — no
functional harm). ``_find_schematron_xslt`` continues to exclude any
stylesheet-ubl.xslt found under specs/peppol_bis_3/ by name as a defensive
guard (verified 2026-08-17 to be a UBL-invoice-to-HTML viewer, not a
Schematron/SVRL validator), so it is never mistaken for a compiled Schematron
if a genuine one is added back later.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Literal, cast

from mcp_einvoicing_core import (
    BaseDocumentValidator,
    DocumentValidationResult,
    ValidationError,
)

from mcp_einvoicing_be.specs import PEPPOL_BIS3_DIR
from mcp_einvoicing_be.standards.mercurius import MERCURIUS_RULES
from mcp_einvoicing_be.utils.helpers import parse_ubl_xml

_log = logging.getLogger(__name__)

# UBL 2.1 namespace map for lxml XPath evaluation.
# Rules in MERCURIUS_RULES use absolute XPath starting with /Invoice/…;
# the evaluator strips the /Invoice/ prefix and evaluates relative to the
# Invoice root element to handle both namespace-qualified and unqualified roots.
_UBL_NSMAP: dict[str, str] = {
    "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

ProfileLiteral = Literal["peppol-bis-3", "pint-eu", "mercurius"]

# Only mercurius has a package-local XPath rule set. peppol-bis-3/pint-eu
# validation is either the real Schematron (when loaded) or "unavailable" —
# see the module docstring.
_PROFILE_RULES: dict[str, list[dict[str, str]]] = {
    "mercurius": MERCURIUS_RULES,
}

# Emitted for peppol-bis-3/pint-eu when neither the local full Schematron nor
# core's bundled EN16931-base Schematron could be loaded (e.g. the [xslt2]
# extra is missing) — should be rare now that the base validator ships in
# core itself.
_PEPPOL_VALIDATION_UNAVAILABLE = (
    "PEPPOL-VALIDATION-UNAVAILABLE: no Schematron validator could be loaded "
    "in this environment (neither the local full Peppol BIS 3.0 Schematron "
    "nor core's bundled EN16931-base Schematron). Install "
    "mcp-einvoicing-core[xslt2] to enable validation. See "
    "[GAP id=core.schematron.be_bundled_xslt] and "
    "context-library/roadmap-2026.md [CORE-EN16931-BASE-SCHEMATRON-1]."
)

# Added to every peppol-bis-3/pint-eu result served by core's bundled EN16931
# base Schematron (path 2 in the module docstring): it checks the CEN base
# rules only, not the Peppol-specific overlay. A document can pass this and
# still be rejected by a real Peppol Access Point.
_EN16931_BASE_ONLY_SCOPE_WARNING = (
    "EN16931-BASE-ONLY-SCOPE: this validates the CEN EN16931 base rules "
    "(structural + arithmetic/totals) only. Peppol-specific overlay rules "
    "(profile/process ID registration, EndpointID scheme, narrowed code "
    "lists) are NOT checked — this is not a full Peppol BIS3 conformance "
    "result. See context-library/decisions/peppol-schematron-artifact.md."
)

# Added to every mercurius-profile result: MERCURIUS_RULES only covers the
# Mercurius-specific overlay (endpoint scheme, PO reference), not full
# EN16931/Peppol BIS 3.0 base compliance — see standards/mercurius.py.
_MERCURIUS_SCOPE_WARNING = (
    "MERCURIUS-SCOPE: this only checks the Mercurius-specific overlay "
    "(endpoint scheme, PO reference). Base EN16931/Peppol BIS 3.0 invoice "
    "compliance is not verified by this profile."
)


#: Filenames known to be non-Schematron XSLTs that OpenPeppol ships alongside
#: the real Schematron sources in the same release bundle. "stylesheet-ubl.xslt"
#: is a UBL-invoice-to-HTML viewer (verified 2026-08-17: it emits a rendered
#: HTML document, not SVRL) — excluded so it is never mistaken for a compiled
#: Schematron. See [GAP id=core.schematron.be_bundled_xslt].
_NON_SCHEMATRON_XSLT_NAMES = {"stylesheet-ubl.xslt"}


def _find_schematron_xslt(*, allow_fallback: bool = True) -> str | None:
    """Locate the pre-compiled Peppol BIS 3.0 Schematron XSLT in specs/.

    Returns the path to the XSLT file if found, None otherwise.
    Looks for common file patterns from the OpenPeppol release ZIP, excluding
    known non-Schematron XSLTs (see _NON_SCHEMATRON_XSLT_NAMES).

    BE-SC-11 (partial): raises loudly instead of silently degrading when the
    XSLT is absent and ``allow_fallback`` is False, so integrators relying on
    real Schematron validation get an explicit signal rather than a silently
    weaker XPath presence-check pass.
    """
    if PEPPOL_BIS3_DIR.is_dir():
        for pattern in ("*.xslt", "*.xsl"):
            matches = [
                p
                for p in PEPPOL_BIS3_DIR.rglob(pattern)
                if p.name not in _NON_SCHEMATRON_XSLT_NAMES
            ]
            if matches:
                return str(matches[0])
    if not allow_fallback:
        raise FileNotFoundError(
            f"Peppol BIS 3.0 Schematron XSLT not found under {PEPPOL_BIS3_DIR} "
            "and allow_fallback=False. See [GAP id=core.schematron.be_bundled_xslt]."
        )
    return None


class BEDocumentValidator(BaseDocumentValidator):
    """Belgian document validator.

    peppol-bis-3/pint-eu: uses the pre-compiled Peppol BIS 3.0 Schematron XSLT
    from specs/ when available (downloaded via ``specs/download.py``); returns
    an explicit "unavailable" result when it is not present, rather than a
    partial hand-coded approximation (see module docstring).
    mercurius: always uses the hand-coded Mercurius-specific overlay rules.
    """

    def __init__(self, *, allow_fallback: bool = True) -> None:
        self._schematron = None
        xslt_path = _find_schematron_xslt(allow_fallback=allow_fallback)
        if xslt_path:
            try:
                from mcp_einvoicing_core.schematron import (  # noqa: PLC0415
                    load_schematron_validator,
                )

                self._schematron = load_schematron_validator(xslt_path)
                _log.info("Loaded Peppol BIS 3.0 Schematron from %s", xslt_path)
            except ImportError as exc:
                _log.warning(
                    "Peppol BIS 3.0 Schematron at %s requires XSLT 2.0 (Saxon-HE); "
                    "install mcp-einvoicing-core[xslt2] to enable it. Falling back "
                    "to hand-coded XPath rules. %s",
                    xslt_path,
                    exc,
                )
            except Exception as exc:
                _log.warning("Failed to load Schematron XSLT %s: %s", xslt_path, exc)

        # Core's bundled EN16931-base Schematron (base rules only, no Peppol
        # overlay — see module docstring). Used when the local full-overlay
        # slot above is empty, which is the case for every install today.
        self._base_schematron = None
        try:
            from mcp_einvoicing_core.schematron_artifacts import (  # noqa: PLC0415
                en16931_base_schematron_validator,
            )

            self._base_schematron = en16931_base_schematron_validator()
            _log.info("Loaded core's bundled EN16931-base Schematron.")
        except ImportError as exc:
            _log.warning(
                "Core's bundled EN16931-base Schematron requires XSLT 2.0/3.0 "
                "(Saxon-HE); install mcp-einvoicing-core[xslt2] to enable it. %s",
                exc,
            )
        except Exception as exc:
            _log.warning("Failed to load core's bundled EN16931-base Schematron: %s", exc)

    def get_schema_version(self) -> str:
        return "Peppol BIS 3.0 / EN16931"

    def validate(self, document_content: str | bytes) -> DocumentValidationResult:
        xml = (
            document_content
            if isinstance(document_content, str)
            else document_content.decode("utf-8", errors="replace")
        )
        return self._validate_with_profile(xml, profile="peppol-bis-3")

    def _validate_with_profile(self, xml: str, profile: str) -> DocumentValidationResult:
        """Core validation logic.

        - peppol-bis-3/pint-eu: real Schematron XSLT when loaded, otherwise an
          explicit "unavailable" result (see module docstring).
        - mercurius: XPath overlay rules (MERCURIUS_RULES) plus a scope warning.
        - any other profile: explicit error, no silent default.
        """
        if profile in ("peppol-bis-3", "pint-eu"):
            xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml

            if self._schematron:
                result = self._schematron.validate(xml_bytes, profile=profile)
                return DocumentValidationResult(
                    valid=result.is_valid,
                    errors=[f"{m.rule_id}: {m.text}" for m in result.errors],
                    warnings=[f"{m.rule_id}: {m.text}" for m in result.warnings],
                    metadata={"profile": profile, "engine": "schematron-xslt", "scope": "full"},
                )

            if self._base_schematron:
                result = self._base_schematron.validate(xml_bytes, profile=profile)
                return DocumentValidationResult(
                    valid=result.is_valid,
                    errors=[f"{m.rule_id}: {m.text}" for m in result.errors],
                    warnings=[
                        _EN16931_BASE_ONLY_SCOPE_WARNING,
                        *[f"{m.rule_id}: {m.text}" for m in result.warnings],
                    ],
                    metadata={
                        "profile": profile,
                        "engine": "schematron-xslt",
                        "scope": "en16931-base-only",
                    },
                )

            return DocumentValidationResult(
                valid=False,
                errors=[_PEPPOL_VALIDATION_UNAVAILABLE],
                warnings=[],
                metadata={"profile": profile, "engine": "unavailable"},
            )

        rules = _PROFILE_RULES.get(profile)
        if rules is None:
            return DocumentValidationResult(
                valid=False,
                errors=[f"UNKNOWN-PROFILE: {profile!r} is not a supported validation profile."],
                warnings=[],
                metadata={"profile": profile, "engine": "unavailable"},
            )

        root, parse_error = parse_ubl_xml(xml)
        if parse_error:
            return DocumentValidationResult(
                valid=False,
                errors=[f"XML-PARSE: {parse_error}"],
                warnings=[],
                metadata={"profile": profile},
            )

        errors: list[str] = []
        warnings: list[str] = [_MERCURIUS_SCOPE_WARNING] if profile == "mercurius" else []

        for rule in rules:
            violation = self._evaluate_rule(root, rule)
            if violation:
                msg = f"{rule.get('id', 'RULE')}: {violation}"
                if rule["severity"] == "error":
                    errors.append(msg)
                else:
                    warnings.append(msg)

        return DocumentValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={"profile": profile, "engine": "xpath-fallback"},
        )

    async def validate_invoice_be(
        self,
        xml: Annotated[str, "Raw UBL 2.1 XML invoice content"],
        profile: Annotated[
            ProfileLiteral,
            "Validation profile: 'peppol-bis-3' (default), 'pint-eu', or 'mercurius'",
        ] = "peppol-bis-3",
    ) -> dict[str, object]:
        """Validate a UBL 2.1 XML invoice against Belgian business rules.

        For 'peppol-bis-3'/'pint-eu': checks the CEN EN16931 base rules
        (structural + arithmetic/totals, ~50 BR-* rules) via a compiled
        Schematron. Does NOT check the Peppol-specific overlay (profile ID
        registration, EndpointID scheme, narrowed code lists) — the result's
        metadata.scope is "en16931-base-only", and a warning is included. This
        is not a full Peppol BIS3 conformance check; a document that passes
        may still be rejected by a real Peppol Access Point. See
        context-library/decisions/peppol-schematron-artifact.md for why.
        For 'mercurius': applies the Mercurius-specific overlay rules only
        (endpoint scheme, PO reference) — also not full EN16931/Peppol base
        compliance.
        Returns a structured result with per-rule error and warning messages.
        """
        try:
            result = self._validate_with_profile(xml, profile)
            return cast(dict[str, object], result.to_dict())
        except ValidationError as exc:
            return {"valid": False, "profile": profile, "errors": [str(exc)], "warnings": []}

    def _evaluate_rule(
        self,
        root: Any,
        rule: dict[str, str],
    ) -> str | None:
        """Evaluate a single XPath-based business rule against a parsed lxml element tree.

        BE-SC-1 (resolved): real lxml XPath evaluation replaces the unconditional
        None stub.  A rule fails when the required element is absent (empty result
        list) or has no text content.

        Args:
            root:  lxml ``_Element`` returned by ``parse_ubl_xml``.
            rule:  Dict with keys ``id``, ``severity``, ``xpath``, ``message``.

        Returns:
            A violation message string if the rule fails, ``None`` if it passes.
        """
        from lxml import etree  # noqa: PLC0415

        if not isinstance(root, etree._Element):  # noqa: SLF001
            return None

        xpath_expr = rule.get("xpath", "")
        if not xpath_expr:
            return None

        # Rules store absolute paths rooted at /Invoice/…  Convert to a relative
        # XPath evaluated from the Invoice root element so the expression works
        # regardless of whether the document uses a UBL namespace or no namespace.
        rel_xpath = xpath_expr
        if rel_xpath.startswith("/Invoice/"):
            rel_xpath = rel_xpath[len("/Invoice/") :]
        elif rel_xpath == "/Invoice":
            rel_xpath = "."

        try:
            results = root.xpath(rel_xpath, namespaces=_UBL_NSMAP)
        except etree.XPathError as exc:
            return f"XPath evaluation error for rule {rule.get('id', '')}: {exc}"

        if not results:
            return rule.get("message", f"Rule {rule.get('id', '')} failed: element not found")

        # The element exists; check that it is not empty (has text content or children)
        for item in results:  # type: ignore[union-attr]
            if isinstance(item, str):
                if item.strip():
                    return None  # non-empty text node
            elif hasattr(item, "text"):
                if (item.text and item.text.strip()) or len(item):  # type: ignore[arg-type]
                    return None  # element with text or child elements
            else:
                return None  # attribute value or other non-empty XPath result

        # All matched nodes were empty
        return rule.get(
            "message",
            f"Rule {rule.get('id', '')} failed: element present but empty",
        )
