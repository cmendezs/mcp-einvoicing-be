"""MCP server entry point — registers all Belgian e-invoicing tools."""

from typing import Any

from mcp_einvoicing_core import EInvoicingMCPServer

from mcp_einvoicing_be.tools.generation import BEDocumentGenerator
from mcp_einvoicing_be.tools.lookup import (
    check_peppol_participant_be,
    get_invoice_types_be,
    lookup_vat_be,
)
from mcp_einvoicing_be.tools.transformation import transform_to_ubl
from mcp_einvoicing_be.tools.validation import BEDocumentValidator

_generator = BEDocumentGenerator()
_validator = BEDocumentValidator()


def _register_be_tools(mcp: Any) -> None:
    """Register all Belgian e-invoicing tools onto the shared FastMCP instance."""
    mcp.tool()(_validator.validate_invoice_be)
    mcp.tool()(_validator.validate_pint_be)
    mcp.tool()(_generator.generate_invoice_be)
    mcp.tool()(transform_to_ubl)
    mcp.tool()(lookup_vat_be)
    mcp.tool()(check_peppol_participant_be)
    mcp.tool()(get_invoice_types_be)


mcp = EInvoicingMCPServer(
    "mcp-einvoicing-be",
    instructions=(
        "Tools for Belgian electronic invoicing: validation, generation, and lookups "
        "for Peppol BIS Billing 3.0, PINT-BE (NBB), UBL 2.1, and Mercurius."
    ),
)
mcp.register_plugin(_register_be_tools, "be")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
