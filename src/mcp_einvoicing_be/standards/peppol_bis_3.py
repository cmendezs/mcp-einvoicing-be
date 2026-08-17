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

# PEPPOL_BIS3_RULES (a hand-rolled ~10-of-50+ rule XPath approximation of the
# real CEN/Peppol Schematron) was removed in v0.7.0. It was the source of a
# real bug (every rule ID from "BR-02" onward was paired with the wrong rule
# content, fixed in v0.6.0) and, more fundamentally, a package-local partial
# duplication of rules that are identical across every Peppol-BIS3-consuming
# country — see context-library/roadmap-2026.md [CORE-PEPPOL-SCHEMATRON-1].
# Rather than keep maintaining an incomplete, easy-to-mismatch approximation
# per country package, mcp_einvoicing_be.tools.validation now reports
# "unavailable" for peppol-bis-3/pint-eu when no real compiled Schematron is
# loaded, instead of a partial pass/fail. See [GAP id=core.schematron.be_bundled_xslt].

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
