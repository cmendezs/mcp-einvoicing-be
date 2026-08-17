"""Belgian invoice validation — subclasses BaseDocumentValidator from mcp-einvoicing-core.

Two validation paths, and one explicit non-path:
1. Schematron XSLT (if downloaded via specs/download.py): delegates to core's
   load_schematron_validator() for full Peppol BIS 3.0 rule coverage. Used for
   peppol-bis-3/pint-eu when a real compiled Schematron is loaded.
2. XPath overlay: evaluates hand-coded rules for the mercurius profile only
   (MERCURIUS_RULES — Mercurius-specific checks, not a Peppol/EN16931 base
   ruleset; see standards/mercurius.py).
3. peppol-bis-3/pint-eu with no Schematron loaded: returns an explicit
   "unavailable" result (valid=False, an error explaining why) rather than a
   partial pass/fail. v0.7.0 removed the package's own hand-rolled Peppol
   BIS 3.0 base-rule approximation (PEPPOL_BIS3_RULES) — it covered ~10 of the
   ~50+ real CEN/Peppol rules, no arithmetic checks, and had carried a rule-ID
   mislabeling bug (fixed in v0.6.0) before removal. A package-local partial
   approximation of rules that are identical across every Peppol-BIS3-consuming
   country is exactly the kind of drift context-library/roadmap-2026.md
   [CORE-PEPPOL-SCHEMATRON-1] exists to close — see that entry before adding
   a replacement fallback here or in any other package.

BE-SC-1 (resolved): _evaluate_rule uses real lxml XPath evaluation.

[GAP id=core.schematron.be_bundled_xslt] (still open): no compiled,
SVRL-producing Peppol BIS 3.0 Schematron XSLT is bundled or downloadable via
``specs/download.py``. specs/peppol_bis_3/ currently ships only
CEN-EN16931-UBL.sch (an uncompiled Schematron *source*, EUPL 1.2 licensed).
The OpenPeppol 3.0.20 (2025 November) release bundle used to verify this
package's former rules also contained PEPPOL-EN16931-UBL.sch and a
stylesheet-ubl.xslt — the latter was verified (2026-08-17) to be a
UBL-invoice-to-HTML *viewer* stylesheet, not a Schematron/SVRL validator
(running it against a test invoice returns an HTML document, not SVRL
findings). Neither file is bundled here: PEPPOL-EN16931-UBL.sch's license is
unclear ("reproduced with permission from CEN", no redistribution terms
stated) and stylesheet-ubl.xslt carries no license at all — both are pending
explicit confirmation before shipping in a published wheel. Turning the .sch
sources into a working SVRL-producing XSLT also still requires a Trang/Saxon
Schematron-compilation build step this package does not yet have.
``_find_schematron_xslt`` excludes any stylesheet-ubl.xslt found under
specs/peppol_bis_3/ by name as a defensive guard, so it is never mistaken for
a compiled Schematron if one is added back later.
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

# Emitted for peppol-bis-3/pint-eu when no compiled Schematron is loaded.
_PEPPOL_VALIDATION_UNAVAILABLE = (
    "PEPPOL-VALIDATION-UNAVAILABLE: no compiled Peppol BIS 3.0 Schematron "
    "validator is available in this environment. This package no longer "
    "carries a hand-rolled approximation (removed in v0.7.0 after a rule-ID "
    "mislabeling bug — see CHANGELOG.md). See "
    "[GAP id=core.schematron.be_bundled_xslt] and "
    "context-library/roadmap-2026.md [CORE-PEPPOL-SCHEMATRON-1]. Install "
    "mcp-einvoicing-core[xslt2] and provide a properly licensed, compiled "
    "SVRL-producing Schematron XSLT under specs/peppol_bis_3/ to enable "
    "real validation."
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
            if self._schematron:
                xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml
                result = self._schematron.validate(xml_bytes, profile=profile)
                return DocumentValidationResult(
                    valid=result.is_valid,
                    errors=[f"{m.rule_id}: {m.text}" for m in result.errors],
                    warnings=[f"{m.rule_id}: {m.text}" for m in result.warnings],
                    metadata={"profile": profile, "engine": "schematron-xslt"},
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

        Applies EN 16931 syntax and semantic checks plus the selected Belgian
        profile overlay (Peppol BIS Billing 3.0, EU PINT v1.0.1, or Mercurius).
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
