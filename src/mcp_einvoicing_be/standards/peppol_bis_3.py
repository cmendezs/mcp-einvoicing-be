"""Peppol BIS Billing 3.0 constants for Belgium."""

# UBL customizationID values (BT-24)
CUSTOMIZATION_IDS: dict[str, str] = {
    "peppol-bis-3": ("urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"),
    "pint-be": (
        "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
        "#conformant#urn:fdc:www.nbb.be:2020:pintbe"
    ),
}

# UBL profileID values (BT-23)
PROFILE_IDS: dict[str, str] = {
    "peppol-bis-3": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
    "pint-be": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
}

# Peppol BIS 3.0 business rules subset relevant to Belgium.
# Each entry has: id, severity, xpath (tested element), message.
PEPPOL_BIS3_RULES: list[dict[str, str]] = [
    {
        "id": "BR-01",
        "severity": "error",
        "xpath": "/Invoice/cbc:CustomizationID",
        "message": "An Invoice shall have a Specification identifier (BT-24).",
    },
    {
        "id": "BR-02",
        "severity": "error",
        "xpath": "/Invoice/cbc:ProfileID",
        "message": "An Invoice shall have a Profile identifier (BT-23).",
    },
    {
        "id": "BR-03",
        "severity": "error",
        "xpath": "/Invoice/cbc:ID",
        "message": "An Invoice shall have an Invoice number (BT-1).",
    },
    {
        "id": "BR-04",
        "severity": "error",
        "xpath": "/Invoice/cbc:IssueDate",
        "message": "An Invoice shall have an Invoice issue date (BT-2).",
    },
    {
        "id": "BR-05",
        "severity": "error",
        "xpath": "/Invoice/cbc:InvoiceTypeCode",
        "message": "An Invoice shall have an Invoice type code (BT-3).",
    },
    {
        "id": "BR-06",
        "severity": "error",
        "xpath": "/Invoice/cbc:DocumentCurrencyCode",
        "message": "An Invoice shall have an Invoice currency code (BT-5).",
    },
    {
        "id": "BR-07",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingSupplierParty",
        "message": "An Invoice shall have a Seller (BG-4).",
    },
    {
        "id": "BR-08",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingCustomerParty",
        "message": "An Invoice shall have a Buyer (BG-7).",
    },
    {
        "id": "BR-09",
        "severity": "error",
        "xpath": "/Invoice/cac:LegalMonetaryTotal/cbc:PayableAmount",
        "message": "An Invoice shall have an Amount due for payment (BT-115).",
    },
    {
        "id": "BR-CO-15",
        "severity": "error",
        "xpath": "/Invoice/cac:TaxTotal/cbc:TaxAmount",
        "message": "Invoice total VAT amount shall equal the sum of VAT category tax amounts.",
    },
    {
        "id": "BR-BE-01",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
        "message": "Belgian invoices shall contain the supplier's VAT number (BTW/TVA).",
    },
]

# Supported Belgian e-invoice document types
INVOICE_TYPES: list[dict[str, object]] = [
    {
        "code": "380",
        "name": "Invoice",
        "name_fr": "Facture",
        "name_nl": "Factuur",
        "profiles": {
            "peppol-bis-3": {
                "customization_id": CUSTOMIZATION_IDS["peppol-bis-3"],
                "profile_id": PROFILE_IDS["peppol-bis-3"],
            },
            "pint-be": {
                "customization_id": CUSTOMIZATION_IDS["pint-be"],
                "profile_id": PROFILE_IDS["pint-be"],
            },
        },
    },
    {
        "code": "381",
        "name": "Credit note",
        "name_fr": "Note de crédit",
        "name_nl": "Creditnota",
        "profiles": {
            "peppol-bis-3": {
                "customization_id": CUSTOMIZATION_IDS["peppol-bis-3"],
                "profile_id": PROFILE_IDS["peppol-bis-3"],
            },
            "pint-be": {
                "customization_id": CUSTOMIZATION_IDS["pint-be"],
                "profile_id": PROFILE_IDS["pint-be"],
            },
        },
    },
    {
        "code": "383",
        "name": "Debit note",
        "name_fr": "Note de débit",
        "name_nl": "Debietnota",
        "profiles": {
            "peppol-bis-3": {
                "customization_id": CUSTOMIZATION_IDS["peppol-bis-3"],
                "profile_id": PROFILE_IDS["peppol-bis-3"],
            },
        },
    },
]
