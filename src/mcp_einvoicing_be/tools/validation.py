"""Belgian invoice validation — subclasses BaseDocumentValidator from mcp-einvoicing-core.

BE-SC-1 (resolved): _evaluate_rule now performs real lxml XPath evaluation
against the parsed document tree, so every invoice is checked against the
hand-coded rule set rather than unconditionally passing.

BE-SH-1 (resolved via core serializer): XML escaping is handled by lxml in the
EN16931UBLSerializer used by BEUBLSerializer; no manual escaping is needed here.
"""

from typing import Annotated, Any, Literal, cast

from mcp_einvoicing_core import (
    BaseDocumentValidator,
    DocumentValidationResult,
    ValidationError,
)

from mcp_einvoicing_be.standards.mercurius import MERCURIUS_RULES
from mcp_einvoicing_be.standards.peppol_bis_3 import PEPPOL_BIS3_RULES
from mcp_einvoicing_be.utils.helpers import parse_ubl_xml

# UBL 2.1 namespace map for lxml XPath evaluation.
# Rules in PEPPOL_BIS3_RULES use absolute XPath starting with /Invoice/…;
# the evaluator strips the /Invoice/ prefix and evaluates relative to the
# Invoice root element to handle both namespace-qualified and unqualified roots.
_UBL_NSMAP: dict[str, str] = {
    "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

ProfileLiteral = Literal["peppol-bis-3", "mercurius"]

_PROFILE_RULES: dict[str, list[dict[str, str]]] = {
    "peppol-bis-3": PEPPOL_BIS3_RULES,
    "mercurius": MERCURIUS_RULES,
}


class BEDocumentValidator(BaseDocumentValidator):
    """Belgian document validator.

    Subclasses ``BaseDocumentValidator`` and implements ``validate()`` for UBL 2.1
    documents against the three Belgian profiles using lxml XPath rule evaluation.
    """

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
        """Core validation logic — parses the document then evaluates each rule."""
        root, parse_error = parse_ubl_xml(xml)
        if parse_error:
            return DocumentValidationResult(
                valid=False,
                errors=[f"XML-PARSE: {parse_error}"],
                warnings=[],
                metadata={"profile": profile},
            )

        rules = _PROFILE_RULES.get(profile, PEPPOL_BIS3_RULES)
        errors: list[str] = []
        warnings: list[str] = []

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
            metadata={"profile": profile},
        )

    async def validate_invoice_be(
        self,
        xml: Annotated[str, "Raw UBL 2.1 XML invoice content"],
        profile: Annotated[
            ProfileLiteral,
            "Validation profile: 'peppol-bis-3' (default) or 'mercurius'",
        ] = "peppol-bis-3",
    ) -> dict[str, object]:
        """Validate a UBL 2.1 XML invoice against Belgian business rules.

        Applies EN 16931 syntax and semantic checks plus the selected Belgian
        profile overlay (Peppol BIS Billing 3.0 or Mercurius).
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
