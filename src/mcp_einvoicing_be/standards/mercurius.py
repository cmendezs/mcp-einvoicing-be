"""Mercurius network configuration and overlay rules for Belgian public-sector invoicing.

Mercurius is the Belgian public-sector e-invoicing platform operated by the
Federal Service of ICT (Fedict/DG DT). It is the mandatory channel for
submitting electronic invoices to Belgian federal public authorities and is
interconnected with the Peppol network.

Specification: https://www.mercurius.be
"""

from mcp_einvoicing_be.standards.peppol_bis_3 import PEPPOL_BIS3_RULES

MERCURIUS_ACCESS_POINT = "https://ap.mercurius.be"

MERCURIUS_CUSTOMIZATION_ID = (
    "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
    "#extended#urn:www.mercurius.be:1.0"
)

MERCURIUS_PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

# Mercurius requires a specific endpoint scheme for Belgian public authorities.
MERCURIUS_PARTICIPANT_SCHEME = "0208"

# Mercurius overlay rules on top of Peppol BIS 3.0.
MERCURIUS_RULES: list[dict[str, str]] = [
    *PEPPOL_BIS3_RULES,
    {
        "id": "MER-001",
        "severity": "error",
        "xpath": "/Invoice/cbc:CustomizationID",
        "message": ("Invoices submitted to Mercurius shall use the Mercurius CustomizationID."),
    },
    {
        "id": "MER-002",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingCustomerParty/cac:Party/cac:EndpointID[@schemeID='0208']",
        "message": (
            "The buyer endpoint shall be a Belgian KBO/BCE number (scheme 0208) "
            "registered on the Mercurius platform."
        ),
    },
    {
        "id": "MER-003",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingSupplierParty/cac:Party/cac:EndpointID",
        "message": (
            "The supplier shall have a Peppol endpoint registered on the Mercurius network."
        ),
    },
    {
        "id": "MER-004",
        "severity": "warning",
        "xpath": "/Invoice/cac:OrderReference/cbc:ID",
        "message": (
            "Public-sector buyers typically require a purchase order reference. "
            "Verify that the contracting authority has provided one."
        ),
    },
]
