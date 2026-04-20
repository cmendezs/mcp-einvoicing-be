"""Belgian invoice generation — subclasses DocumentGenerator from mcp-einvoicing-core."""

from typing import Annotated, Any, Literal

from mcp_einvoicing_core import BaseDocumentGenerator, DocumentGenerationError

from mcp_einvoicing_be.models.invoice import BEInvoice
from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS, PROFILE_IDS
from mcp_einvoicing_be.standards.ubl import UBL_NAMESPACES, render_ubl_invoice

ProfileLiteral = Literal["peppol-bis-3", "pint-be"]


class BEDocumentGenerator(BaseDocumentGenerator):  # type: ignore[misc]
    """Belgian UBL 2.1 document generator.

    Subclasses ``DocumentGenerator`` and implements ``generate()`` for the
    Peppol BIS Billing 3.0 and PINT-BE profiles. Tools are exposed as instance
    methods so they can be registered on ``EInvoicingMCPServer``.
    """

    def get_format_name(self) -> str:
        return "UBL-2.1"

    def get_country_code(self) -> str:
        return "BE"

    def generate(self, invoice: BEInvoice) -> str:
        """Serialize a ``BEInvoice`` to a UBL 2.1 XML string."""
        return render_ubl_invoice(
            invoice=invoice,
            customization_id=CUSTOMIZATION_IDS[invoice.profile],
            profile_id=PROFILE_IDS[invoice.profile],
            namespaces=UBL_NAMESPACES,
        )

    async def generate_invoice_be(
        self,
        invoice_data: Annotated[dict[str, Any], "Invoice fields matching the BEInvoice schema"],
        profile: Annotated[
            ProfileLiteral,
            "Target profile: 'peppol-bis-3' (default) or 'pint-be'",
        ] = "peppol-bis-3",
    ) -> dict[str, object]:
        """Generate a valid UBL 2.1 Belgian e-invoice XML document from structured data.

        Applies the correct customizationID and profileID for the selected Belgian
        Peppol profile. The output XML is ready for submission to the Peppol network
        or the Mercurius platform.

        Returns a dict with:
        - ``xml``: the generated UBL 2.1 XML string
        - ``customization_id``: the UBL customizationID applied (BT-24)
        - ``profile_id``: the UBL profileID applied (BT-23)
        """
        try:
            invoice = BEInvoice.model_validate({**invoice_data, "profile": profile})
            xml_string = self.generate(invoice)
        except DocumentGenerationError:
            raise
        except Exception as exc:
            raise DocumentGenerationError(str(exc)) from exc

        return {
            "xml": xml_string,
            "customization_id": CUSTOMIZATION_IDS[profile],
            "profile_id": PROFILE_IDS[profile],
        }
