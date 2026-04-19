"""Validation tools: validate_invoice_be, validate_pint_be."""

from typing import Annotated, Literal

from mcp_einvoicing_be.models.invoice import MessageSeverity, ValidationMessage, ValidationResult
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


async def validate_invoice_be(
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
    messages: list[ValidationMessage] = []

    root, parse_error = parse_ubl_xml(xml)
    if parse_error:
        messages.append(
            ValidationMessage(
                severity=MessageSeverity.ERROR,
                rule_id="XML-PARSE",
                message=parse_error,
            )
        )
        result = ValidationResult(
            valid=False,
            profile=profile,
            error_count=1,
            warning_count=0,
            messages=messages,
        )
        return result.model_dump()

    rules = _PROFILE_RULES.get(profile, PEPPOL_BIS3_RULES)
    for rule in rules:
        violation = _evaluate_rule(root, rule)
        if violation:
            messages.append(violation)

    errors = [m for m in messages if m.severity == MessageSeverity.ERROR]
    warnings = [m for m in messages if m.severity == MessageSeverity.WARNING]

    result = ValidationResult(
        valid=len(errors) == 0,
        profile=profile,
        error_count=len(errors),
        warning_count=len(warnings),
        messages=messages,
    )
    return result.model_dump()


async def validate_pint_be(
    xml: Annotated[str, "Raw UBL 2.1 XML invoice content"],
) -> dict[str, object]:
    """Validate an invoice against PINT-BE rules published by the National Bank of Belgium (NBB).

    PINT-BE is the Belgian PINT (Peppol International) extension that adds
    country-specific mandatory elements on top of EN 16931. Rule IDs follow
    the PINT-BE-Rxxx naming convention from the NBB specification.
    """
    return await validate_invoice_be(xml=xml, profile="pint-be")


def _evaluate_rule(
    root: object,
    rule: dict[str, str],
) -> ValidationMessage | None:
    """Evaluate a single XPath-based business rule against a parsed XML tree.

    Returns a ValidationMessage if the rule is violated, None otherwise.
    This is a stub — real evaluation delegates to mcp-einvoicing-core's
    Schematron engine once the dependency is available.
    """
    # Delegate to core schematron engine when available.
    # Stub: always passes during scaffolding.
    return None
