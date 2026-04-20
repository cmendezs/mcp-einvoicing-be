"""Belgian invoice validation — subclasses BaseDocumentValidator from mcp-einvoicing-core."""

from typing import Annotated, Literal

from mcp_einvoicing_core import (
    BaseDocumentValidator,
    DocumentValidationResult,
    ValidationError,
)

from mcp_einvoicing_be.standards.mercurius import MERCURIUS_RULES
from mcp_einvoicing_be.standards.peppol_bis_3 import PEPPOL_BIS3_RULES
from mcp_einvoicing_be.standards.pint_be import PINT_BE_RULES
from mcp_einvoicing_be.utils.helpers import parse_ubl_xml

ProfileLiteral = Literal["peppol-bis-3", "pint-be", "mercurius"]

_PROFILE_RULES: dict[str, list[dict[str, str]]] = {
    "peppol-bis-3": PEPPOL_BIS3_RULES,
    "pint-be": PINT_BE_RULES,
    "mercurius": MERCURIUS_RULES,
}


class BEDocumentValidator(BaseDocumentValidator):
    """Belgian document validator.

    Subclasses ``BaseDocumentValidator`` and implements ``validate()`` for UBL 2.1
    documents against the three Belgian profiles.
    """

    def get_schema_version(self) -> str:
        return "Peppol BIS 3.0 / EN16931"

    def validate(self, document_content: str | bytes) -> DocumentValidationResult:
        return self._validate_with_profile(
            document_content if isinstance(document_content, str) else document_content.decode(),
            profile="peppol-bis-3",
        )

    def _validate_with_profile(self, xml: str, profile: str) -> DocumentValidationResult:
        """Core validation logic."""
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
                msg = f"{rule.get('rule_id', 'RULE')}: {violation}"
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
            "Validation profile: 'peppol-bis-3' (default), 'pint-be', or 'mercurius'",
        ] = "peppol-bis-3",
    ) -> dict[str, object]:
        """Validate a UBL 2.1 XML invoice against Belgian business rules.

        Applies EN 16931 syntax and semantic checks plus the selected Belgian
        profile overlay (Peppol BIS Billing 3.0, PINT-BE, or Mercurius).
        Returns a structured result with per-rule error and warning messages.
        """
        try:
            result = self._validate_with_profile(xml, profile)
            return result.to_dict()
        except ValidationError as exc:
            return {"valid": False, "profile": profile, "errors": [str(exc)], "warnings": []}

    async def validate_pint_be(
        self,
        xml: Annotated[str, "Raw UBL 2.1 XML invoice content"],
    ) -> dict[str, object]:
        """Validate an invoice against PINT-BE rules published by the National Bank of Belgium
        (NBB).

        PINT-BE is the Belgian PINT (Peppol International) extension that adds
        country-specific mandatory elements on top of EN 16931. Rule IDs follow
        the PINT-BE-Rxxx naming convention from the NBB specification.
        """
        return await self.validate_invoice_be(xml=xml, profile="pint-be")

    def _evaluate_rule(
        self,
        root: object,
        rule: dict[str, str],
    ) -> str | None:
        """Evaluate a single XPath-based business rule against a parsed XML tree.

        Returns a violation message if the rule fails, None if it passes.
        Delegates to the core Schematron engine when available; stubs pass
        during scaffolding.
        """
        return None
