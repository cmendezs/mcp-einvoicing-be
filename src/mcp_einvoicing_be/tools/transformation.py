"""Transformation tool: transform_to_ubl."""

from typing import Annotated, Any

from mcp_einvoicing_be.models.invoice import InvoiceInput
from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS, PROFILE_IDS
from mcp_einvoicing_be.standards.ubl import UBL_NAMESPACES, render_ubl_invoice


async def transform_to_ubl(
    data: Annotated[
        dict[str, Any],
        "Source invoice data matching the InvoiceInput schema",
    ],
) -> dict[str, object]:
    """Convert a structured JSON invoice payload to UBL 2.1 XML.

    Unlike ``generate_invoice_be``, this tool does not run validation after
    transformation. It is intended as a conversion step when the caller will
    validate separately or submit directly to a system that performs its own
    validation.

    Returns a dict with keys:
    - ``xml``: the generated UBL 2.1 XML string
    - ``warnings``: list of non-fatal issues detected during transformation
    """
    invoice = InvoiceInput.model_validate(data)
    warnings: list[str] = []

    if not invoice.customer.vat_number:
        warnings.append(
            "Customer VAT number is absent — acceptable for B2C but required for most B2B profiles."
        )

    if invoice.payment_means_code == "30" and not invoice.iban:
        warnings.append(
            "Payment means is credit transfer (code 30) but no IBAN was provided."
        )

    xml_string = render_ubl_invoice(
        invoice=invoice,
        customization_id=CUSTOMIZATION_IDS["peppol-bis-3"],
        profile_id=PROFILE_IDS["peppol-bis-3"],
        namespaces=UBL_NAMESPACES,
    )

    return {"xml": xml_string, "warnings": warnings}
