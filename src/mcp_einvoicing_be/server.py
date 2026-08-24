"""MCP server entry point — registers all Belgian e-invoicing tools."""

from typing import Any

from mcp_einvoicing_core import EInvoicingMCPServer
from mcp_einvoicing_core.en16931_codelist_tools import register_en16931_codelist_tools
from mcp_einvoicing_core.peppol.mls_tools import register_peppol_mls_tools
from mcp_einvoicing_core.peppol.reporting_tools import register_peppol_reporting_tools
from mcp_einvoicing_core.peppol.tools import register_peppol_tools

from mcp_einvoicing_be.tools.generation import BEDocumentGenerator
from mcp_einvoicing_be.tools.lookup import get_invoice_types_be, lookup_vat_be
from mcp_einvoicing_be.tools.parsing import parse_ubl_invoice_be
from mcp_einvoicing_be.tools.transformation import transform_to_ubl
from mcp_einvoicing_be.tools.validation import BEDocumentValidator
from mcp_einvoicing_be.utils.helpers import normalize_vat_be

_generator = BEDocumentGenerator()
_validator = BEDocumentValidator()


def _be_id_adapter(identifier: str) -> str:
    """Normalize a bare Belgian VAT number to a Peppol participant ID.

    Scheme 0208 is the Belgian enterprise number (KBO/BCE). Already
    scheme-qualified identifiers (containing ':') pass through unchanged.
    """
    if ":" in identifier:
        return identifier
    return f"0208:{normalize_vat_be(identifier)[2:]}"


def _register_be_tools(mcp: Any) -> None:
    """Register all Belgian e-invoicing tools onto the shared FastMCP instance."""
    mcp.tool()(_validator.validate_invoice_be)
    mcp.tool()(_generator.generate_invoice_be)
    mcp.tool()(transform_to_ubl)
    mcp.tool()(parse_ubl_invoice_be)
    mcp.tool()(lookup_vat_be)
    mcp.tool()(get_invoice_types_be)


mcp = EInvoicingMCPServer(
    "mcp-einvoicing-be",
    instructions=(
        "Tools for Belgian electronic invoicing: validation, generation, parsing, "
        "and lookups for Peppol BIS Billing 3.0, UBL 2.1, and Mercurius. "
        "B2G invoices route via Mercurius (Peppol receiver, scheme 0208); "
        "see README for details."
    ),
)
mcp.register_plugin(_register_be_tools, "be")
mcp.register_plugin(lambda m: register_peppol_tools(m, id_adapter=_be_id_adapter), "peppol")
mcp.register_plugin(register_peppol_reporting_tools, "peppol-reporting")
mcp.register_plugin(register_peppol_mls_tools, "peppol-mls")
mcp.register_plugin(register_en16931_codelist_tools, "en16931-codelists")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
