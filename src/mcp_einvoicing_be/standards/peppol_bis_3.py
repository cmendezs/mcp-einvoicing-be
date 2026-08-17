"""Peppol BIS Billing 3.0 constants for Belgium."""

# UBL customizationID values (BT-24)
CUSTOMIZATION_IDS: dict[str, str] = {
    "peppol-bis-3": ("urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"),
    "pint-eu": ("urn:peppol:pint:billing-1@en16931-2017@eu-3"),
}

# UBL profileID values (BT-23)
PROFILE_IDS: dict[str, str] = {
    "peppol-bis-3": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
    "pint-eu": "urn:peppol:pint:billing-1",
}

# Peppol BIS 3.0 business rules subset relevant to Belgium.
# Each entry has: id, severity, xpath (tested element), message.
#
# IDs and content below were verified against the OpenPeppol 3.0.20 release
# artefacts (specs/peppol_bis_3/CEN-EN16931-UBL.sch, PEPPOL-EN16931-UBL.sch).
# The previous revision paired real CEN/Peppol rule IDs with the wrong rule
# content (e.g. its "BR-02" tested ProfileID/BT-23, but the real BR-02 tests
# the Invoice number/BT-1; the real BT-23 check is the Peppol-specific rule
# PEPPOL-EN16931-R001, not a CEN BR-* id at all) — every entry from the old
# "BR-02" onward was shifted by one against the real rule set. This is only a
# fallback layer: when the bundled Schematron XSLT loads (see
# tools/validation.py), that engine runs the full official ruleset instead.
PEPPOL_BIS3_RULES: list[dict[str, str]] = [
    {
        "id": "BR-01",
        "severity": "error",
        "xpath": "/Invoice/cbc:CustomizationID",
        "message": "An Invoice shall have a Specification identifier (BT-24).",
    },
    {
        "id": "PEPPOL-EN16931-R001",
        "severity": "error",
        "xpath": "/Invoice/cbc:ProfileID",
        "message": "Business process (Profile identifier, BT-23) MUST be provided.",
    },
    {
        "id": "BR-02",
        "severity": "error",
        "xpath": "/Invoice/cbc:ID",
        "message": "An Invoice shall have an Invoice number (BT-1).",
    },
    {
        "id": "BR-03",
        "severity": "error",
        "xpath": "/Invoice/cbc:IssueDate",
        "message": "An Invoice shall have an Invoice issue date (BT-2).",
    },
    {
        "id": "BR-04",
        "severity": "error",
        "xpath": "/Invoice/cbc:InvoiceTypeCode",
        "message": "An Invoice shall have an Invoice type code (BT-3).",
    },
    {
        "id": "BR-05",
        "severity": "error",
        "xpath": "/Invoice/cbc:DocumentCurrencyCode",
        "message": "An Invoice shall have an Invoice currency code (BT-5).",
    },
    {
        "id": "BR-06",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
        "message": "An Invoice shall contain the Seller name (BT-27).",
    },
    {
        "id": "BR-07",
        "severity": "error",
        "xpath": "/Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
        "message": "An Invoice shall contain the Buyer name (BT-44).",
    },
    {
        "id": "BR-15",
        "severity": "error",
        "xpath": "/Invoice/cac:LegalMonetaryTotal/cbc:PayableAmount",
        "message": "An Invoice shall have the Amount due for payment (BT-115).",
    },
    # BR-CO-15 fallback presence check dropped in v0.5.0 (BE-SC-13) — it only
    # verified the element was present and non-empty, not that the total VAT
    # amount actually equals the sum of category tax amounts, which was
    # misleading. Real arithmetic enforcement is deferred to the Peppol
    # Schematron XSLT once BE-SC-11's bundling gap is resolved.
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
            "pint-eu": {
                "customization_id": CUSTOMIZATION_IDS["pint-eu"],
                "profile_id": PROFILE_IDS["pint-eu"],
            },
        },
    },
    {
        "code": "381",
        "name": "Credit note",
        "name_fr": "Note de credit",
        "name_nl": "Creditnota",
        "profiles": {
            "peppol-bis-3": {
                "customization_id": CUSTOMIZATION_IDS["peppol-bis-3"],
                "profile_id": PROFILE_IDS["peppol-bis-3"],
            },
            "pint-eu": {
                "customization_id": CUSTOMIZATION_IDS["pint-eu"],
                "profile_id": PROFILE_IDS["pint-eu"],
            },
        },
    },
    {
        "code": "383",
        "name": "Debit note",
        "name_fr": "Note de debit",
        "name_nl": "Debietnota",
        "profiles": {
            "peppol-bis-3": {
                "customization_id": CUSTOMIZATION_IDS["peppol-bis-3"],
                "profile_id": PROFILE_IDS["peppol-bis-3"],
            },
        },
    },
]
