"""PINT-BE business rules published by the National Bank of Belgium (NBB).

PINT-BE is the Belgian extension of the Peppol International (PINT) billing
specification. It adds country-specific mandatory elements on top of EN 16931
and Peppol BIS Billing 3.0.

Source: NBB specification available at https://www.nbb.be/en/payments-and-securities/
payment-standards/billing-standards/pint-be
"""

from mcp_einvoicing_be.standards.peppol_bis_3 import PEPPOL_BIS3_RULES

# PINT-BE rules extend the Peppol BIS 3.0 base rules.
PINT_BE_RULES: list[dict[str, str]] = [
    *PEPPOL_BIS3_RULES,
    {
        "id": "PINT-BE-R001",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
        "message": (
            "The supplier VAT identification number shall be present and conform to "
            "the Belgian BTW/TVA format (BExxxxxxxxxx)."
        ),
    },
    {
        "id": "PINT-BE-R002",
        "severity": "error",
        "xpath": "/Invoice/cbc:CustomizationID",
        "message": (
            "The CustomizationID shall contain the PINT-BE conformant identifier "
            "as published by the NBB."
        ),
    },
    {
        "id": "PINT-BE-R003",
        "severity": "warning",
        "xpath": "/Invoice/cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID",
        "message": (
            "For credit transfer (PaymentMeansCode 30), the IBAN of the payee "
            "financial account should be provided."
        ),
    },
    {
        "id": "PINT-BE-R004",
        "severity": "warning",
        "xpath": "/Invoice/cac:PaymentMeans/cbc:PaymentID",
        "message": (
            "A structured payment reference (OGM/VCS) is recommended for "
            "automated reconciliation in Belgian banking."
        ),
    },
    {
        "id": "PINT-BE-R005",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
        "message": (
            "For B2B transactions, the buyer's Belgian VAT number shall be present."
        ),
    },
]
