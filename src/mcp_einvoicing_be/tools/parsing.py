"""UBL 2.1 invoice parsing tool for Belgian e-invoices.

BE-LC-5: mandatory reception capability required by Art. 13quater of Royal
Decree no. 1 (inserted by the Royal Decree of 8 July 2025, MB/BS N. 157).
"""

from typing import Annotated

from mcp_einvoicing_be.standards.ubl import BEUBLParser


async def parse_ubl_invoice_be(
    xml_content: Annotated[str, "Raw UBL 2.1 XML invoice content (Peppol BIS 3.0)"],
) -> dict[str, object]:
    """Parse a UBL 2.1 XML invoice into a structured dict.

    Accepts a Peppol BIS Billing 3.0 UBL 2.1 document and extracts the EN 16931
    core field set (header, parties, lines, tax breakdown, totals). Returns a
    structured dict on success or an error dict on parse failure.
    """
    from lxml import etree  # noqa: PLC0415

    try:
        raw = xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        parser = BEUBLParser()
        invoice = parser.parse(raw)
        return {
            "success": True,
            "invoice": invoice.model_dump(mode="json"),
            "warnings": [],
        }
    except etree.XMLSyntaxError as exc:
        return {
            "success": False,
            "error": f"XML parse error: {exc}",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
