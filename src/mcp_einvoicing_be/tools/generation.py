"""Generation tool: generate_invoice_be."""

from typing import Annotated, Any, Literal

from mcp_einvoicing_be.models.invoice import InvoiceInput
from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS, PROFILE_IDS
from mcp_einvoicing_be.standards.ubl import UBL_NAMESPACES, render_ubl_invoice

ProfileLiteral = Literal["peppol-bis-3", "pint-be"]


async def generate_invoice_be(
    invoice_data: Annotated[dict[str, Any], "Invoice fields matching the InvoiceInput schema"],
    profile: Annotated[
        ProfileLiteral,
        "Target profile: 'peppol-bis-3' (default) or 'pint-be'",
    ] = "peppol-bis-3",
) -> dict[str, object]:
    """Generate a valid UBL 2.1 Belgian e-invoice XML document from structured data.

    Applies the correct customizationID and profileID for the selected Belgian
    Peppol profile. The output XML is ready for submission to the Peppol network
    or the Mercurius platform.

    Returns a dict with keys:
    - ``xml``: the generated UBL 2.1 XML string
    - ``customization_id``: the UBL customizationID applied
    - ``profile_id``: the UBL profileID applied
    """
    invoice = InvoiceInput.model_validate(invoice_data)

    customization_id = CUSTOMIZATION_IDS.get(profile, CUSTOMIZATION_IDS["peppol-bis-3"])
    profile_id = PROFILE_IDS.get(profile, PROFILE_IDS["peppol-bis-3"])

    xml_string = render_ubl_invoice(
        invoice=invoice,
        customization_id=customization_id,
        profile_id=profile_id,
        namespaces=UBL_NAMESPACES,
    )

    return {
        "xml": xml_string,
        "customization_id": customization_id,
        "profile_id": profile_id,
    }
