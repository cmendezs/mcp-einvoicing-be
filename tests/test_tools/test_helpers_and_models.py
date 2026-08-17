"""Tests covering BE-TL-1, BE-TL-2, BE-SC-2, BE-SC-1 fixes."""

import pytest
from mcp_einvoicing_core.en16931 import EN16931Invoice

from mcp_einvoicing_be.models.invoice import BEInvoice, VatCategory
from mcp_einvoicing_be.tools.validation import BEDocumentValidator
from mcp_einvoicing_be.utils.helpers import normalize_vat_be

# ---------------------------------------------------------------------------
# BE-TL-1 — modulo-97 check-digit validation
# ---------------------------------------------------------------------------


class TestNormalizeVatBe:
    """normalize_vat_be — format normalisation and check-digit enforcement."""

    def test_accepts_valid_with_be_prefix(self):
        # BE0123456749: first 8 = 01234567, 97 - (1234567 % 97) = ?
        # Use a known-good number: BE0428759497
        result = normalize_vat_be("BE0428759497")
        assert result == "BE0428759497"

    def test_accepts_valid_without_prefix(self):
        result = normalize_vat_be("0428759497")
        assert result == "BE0428759497"

    def test_accepts_formatted_with_dots(self):
        result = normalize_vat_be("BE 0428.759.497")
        assert result == "BE0428759497"

    def test_rejects_wrong_length(self):
        with pytest.raises(ValueError, match="10 digits"):
            normalize_vat_be("BE012345678")  # only 9 digits

    def test_rejects_invalid_check_digit(self):
        # BE0123456789 has check digits 89. Real check should be something else.
        # Compute: first_8 = 01234567 = 1234567; 97 - (1234567 % 97) = ?
        # 1234567 % 97 = 1234567 - 97*12727 = 1234567 - 1234519 = 48; 97 - 48 = 49
        # So valid would be BE0123456749; 89 is wrong.
        with pytest.raises(ValueError, match="[Cc]heck digit"):
            normalize_vat_be("BE0123456789")

    def test_builds_correct_check_digit(self):
        # Verify: BE0428759497 is correct.
        # first_8 = 04287594 = 4287594; 4287594 % 97 = 4287594 - 97*44201 = 4287594 - 4287497 = 97
        # edge case: remainder == 97 means check digits = 97 (not 0)
        result = normalize_vat_be("BE0428759497")
        assert result.endswith("97")


# ---------------------------------------------------------------------------
# BE-TL-2 — VatCategory AA and AB
# ---------------------------------------------------------------------------


class TestVatCategory:
    def test_standard_is_s(self):
        assert VatCategory.STANDARD == "S"

    def test_reduced_12_is_aa(self):
        assert VatCategory.REDUCED_12 == "AA"

    def test_reduced_6_is_ab(self):
        assert VatCategory.REDUCED_6 == "AB"

    def test_zero_rated_is_z(self):
        assert VatCategory.ZERO_RATED == "Z"

    def test_exempt_is_e(self):
        assert VatCategory.EXEMPT == "E"

    def test_reverse_charge_is_ae(self):
        assert VatCategory.REVERSE_CHARGE == "AE"


# ---------------------------------------------------------------------------
# BE-SC-2 — BEInvoice is-a EN16931Invoice
# ---------------------------------------------------------------------------


class TestBEInvoiceIsEN16931:
    def test_beinvoice_inherits_en16931invoice(self):
        assert issubclass(BEInvoice, EN16931Invoice)

    def test_beinvoice_instance_is_en16931invoice(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert isinstance(invoice, EN16931Invoice)

    def test_totals_auto_computed(self, minimal_invoice_data):
        # 8 units * EUR 125 = EUR 1000 + 21% VAT = EUR 210 tax
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        from decimal import Decimal

        assert invoice.sum_of_line_net_amounts == Decimal("1000.00")
        assert invoice.tax_total == Decimal("210.00")
        assert invoice.tax_inclusive_amount == Decimal("1210.00")
        assert invoice.amount_due == Decimal("1210.00")

    def test_tax_lines_populated(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert len(invoice.tax_lines) == 1
        assert invoice.tax_lines[0].category == "S"

    def test_line_items_populated(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert len(invoice.line_items) == 1
        assert invoice.line_items[0].name == "Consulting services"

    def test_number_alias_works(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert invoice.invoice_number == "TEST-2024-001"

    def test_date_alias_works(self, minimal_invoice_data):
        from datetime import date

        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert invoice.invoice_date == date(2024, 1, 15)

    def test_currency_alias_works(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert invoice.currency_code == "EUR"

    def test_berparty_is_en16931party(self, minimal_invoice_data):
        from mcp_einvoicing_core.en16931 import EN16931Party

        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert isinstance(invoice.seller, EN16931Party)
        assert isinstance(invoice.buyer, EN16931Party)

    def test_beaddress_is_en16931address(self, minimal_invoice_data):
        from mcp_einvoicing_core.en16931 import EN16931Address

        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert isinstance(invoice.seller.address, EN16931Address)
        assert invoice.seller.address.line_one == "Rue de la Loi 1"
        assert invoice.seller.address.postcode == "1000"

    def test_vat_id_synced_from_tax_id(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert invoice.seller.vat_id == "BE0428759497"


# ---------------------------------------------------------------------------
# ARCH-VALID-1c — model-level BCE/KBO modulo-97 enforcement on BEParty.tax_id
# ---------------------------------------------------------------------------


class TestBEPartyTaxIdValidation:
    """BEParty.tax_id must reject invalid mod-97 numbers at model construction."""

    def test_invalid_check_digit_raises(self, minimal_invoice_data):
        from pydantic import ValidationError

        data = {
            **minimal_invoice_data,
            "seller": {**minimal_invoice_data["seller"], "tax_id": "BE0123456789"},
        }
        with pytest.raises(ValidationError, match="Belgian VAT"):
            BEInvoice.model_validate(data)

    def test_none_tax_id_allowed(self, minimal_invoice_data):
        data = {
            **minimal_invoice_data,
            "buyer": {**minimal_invoice_data["buyer"], "tax_id": None},
        }
        invoice = BEInvoice.model_validate(data)
        assert invoice.buyer.tax_id is None


# ---------------------------------------------------------------------------
# BE-SC-2 — reduced-rate category in invoice totals
# ---------------------------------------------------------------------------


class TestReducedRateInvoice:
    def test_12pct_category_aa_in_tax_lines(self, minimal_invoice_data):
        data = {
            **minimal_invoice_data,
            "lines": [
                {
                    "description": "Restaurant service",
                    "quantity": 1.0,
                    "unit_price": 100.00,
                    "vat_rate": 12.0,
                    "vat_category": "AA",
                }
            ],
        }
        invoice = BEInvoice.model_validate(data)
        assert invoice.tax_lines[0].category == "AA"

    def test_6pct_category_ab_in_tax_lines(self, minimal_invoice_data):
        data = {
            **minimal_invoice_data,
            "lines": [
                {
                    "description": "Food",
                    "quantity": 1.0,
                    "unit_price": 50.00,
                    "vat_rate": 6.0,
                    "vat_category": "AB",
                }
            ],
        }
        invoice = BEInvoice.model_validate(data)
        assert invoice.tax_lines[0].category == "AB"


# ---------------------------------------------------------------------------
# BE-SC-1 — _evaluate_rule uses real lxml XPath
# ---------------------------------------------------------------------------


class TestEvaluateRule:
    """v0.7.0: PEPPOL_BIS3_RULES was removed (see standards/peppol_bis_3.py
    and roadmap-2026.md [CORE-PEPPOL-SCHEMATRON-1]), so validate_invoice_be's
    peppol-bis-3 profile no longer runs _evaluate_rule at all — it reports an
    explicit "unavailable" result instead (see test_validation.py). This class
    now exercises _evaluate_rule directly against synthetic rule dicts to keep
    covering the underlying lxml XPath evaluation mechanism (BE-SC-1)."""

    _val = BEDocumentValidator()

    _ID_RULE = {
        "id": "TEST-ID",
        "severity": "error",
        "xpath": "/Invoice/cbc:ID",
        "message": "An Invoice shall have an Invoice number.",
    }
    _SUPPLIER_NAME_RULE = {
        "id": "TEST-SUPPLIER-NAME",
        "severity": "error",
        "xpath": (
            "/Invoice/cac:AccountingSupplierParty/cac:Party"
            "/cac:PartyLegalEntity/cbc:RegistrationName"
        ),
        "message": "An Invoice shall contain the Seller name.",
    }

    VALID_UBL = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
  <cbc:ID>INV-001</cbc:ID>
  <cbc:IssueDate>2024-01-15</cbc:IssueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyLegalEntity><cbc:RegistrationName>Acme NV</cbc:RegistrationName></cac:PartyLegalEntity>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>BE0428759497</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyLegalEntity><cbc:RegistrationName>Client SPRL</cbc:RegistrationName></cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">210.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal><cbc:PayableAmount currencyID="EUR">1210.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>"""

    MISSING_ID_UBL = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
</Invoice>"""

    def _root(self, xml: str):
        from mcp_einvoicing_be.utils.helpers import parse_ubl_xml

        root, parse_error = parse_ubl_xml(xml)
        assert parse_error is None, parse_error
        return root

    def test_valid_xml_passes_rules(self):
        root = self._root(self.VALID_UBL)
        assert self._val._evaluate_rule(root, self._ID_RULE) is None
        assert self._val._evaluate_rule(root, self._SUPPLIER_NAME_RULE) is None

    def test_missing_invoice_id_produces_violation(self):
        root = self._root(self.MISSING_ID_UBL)
        violation = self._val._evaluate_rule(root, self._ID_RULE)
        assert violation is not None
        assert "Invoice number" in violation

    def test_missing_supplier_name_produces_violation(self):
        root = self._root(self.MISSING_ID_UBL)
        violation = self._val._evaluate_rule(root, self._SUPPLIER_NAME_RULE)
        assert violation is not None
        assert "Seller name" in violation
