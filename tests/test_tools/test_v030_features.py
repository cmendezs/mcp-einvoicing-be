"""Tests for v0.3.0 sprint features (BE-SC-4/6/8, BE-TL-4, BE-LC-2/3/5)."""

from decimal import Decimal
from xml.etree.ElementTree import fromstring

import pytest

from mcp_einvoicing_be.models.invoice import BEInvoice, BEPaymentTerms
from mcp_einvoicing_be.standards.ubl import BEUBLSerializer
from mcp_einvoicing_be.tools.parsing import parse_ubl_invoice_be
from mcp_einvoicing_be.utils.helpers import validate_belgian_ogm

# ---------------------------------------------------------------------------
# BE-TL-4 — OGM/VCS check-digit validator
# ---------------------------------------------------------------------------


class TestValidateBelgianOgm:
    def test_accepts_formatted_valid(self):
        result = validate_belgian_ogm("+++000/0000/00097+++")
        assert result == "+++000/0000/00097+++"

    def test_accepts_bare_12_digit(self):
        result = validate_belgian_ogm("000000000097")
        assert result == "+++000/0000/00097+++"

    def test_rejects_wrong_check_digit(self):
        with pytest.raises(ValueError, match="check digit"):
            validate_belgian_ogm("000000000099")

    def test_rejects_11_digits(self):
        with pytest.raises(ValueError, match="12 digits"):
            validate_belgian_ogm("00000000097")

    def test_rejects_13_digits(self):
        with pytest.raises(ValueError, match="12 digits"):
            validate_belgian_ogm("0000000000097")

    def test_payment_terms_validates_ogm(self):
        terms = BEPaymentTerms(ogm_reference="+++000/0000/00097+++")
        assert terms.ogm_reference == "+++000/0000/00097+++"

    def test_payment_terms_rejects_invalid_ogm(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="check digit"):
            BEPaymentTerms(ogm_reference="+++000/0000/00099+++")

    def test_payment_terms_allows_none_ogm(self):
        terms = BEPaymentTerms(ogm_reference=None)
        assert terms.ogm_reference is None


# ---------------------------------------------------------------------------
# BE-SC-4 — pint-be removed
# ---------------------------------------------------------------------------


class TestPintBeRemoved:
    def test_profile_only_accepts_peppol_bis_3(self, minimal_invoice_data):
        invoice = BEInvoice.model_validate(minimal_invoice_data)
        assert invoice.profile == "peppol-bis-3"

    def test_profile_rejects_pint_be(self, minimal_invoice_data):
        from pydantic import ValidationError

        data = {**minimal_invoice_data, "profile": "pint-be"}
        with pytest.raises(ValidationError, match="peppol-bis-3"):
            BEInvoice.model_validate(data)


# ---------------------------------------------------------------------------
# BE-SC-6 — buyer_reference round-trip
# ---------------------------------------------------------------------------


class TestBuyerReference:
    def test_buyer_reference_serializes_to_ubl(self, minimal_invoice_data):
        data = {**minimal_invoice_data, "buyer_reference": "PO-12345"}
        invoice = BEInvoice.model_validate(data)
        assert invoice.buyer_reference == "PO-12345"
        xml_str = BEUBLSerializer().serialize_be_str(invoice)
        assert "<cbc:BuyerReference>PO-12345</cbc:BuyerReference>" in xml_str


# ---------------------------------------------------------------------------
# BE-SC-8 — buyer_article_id (BT-156) end-to-end
# ---------------------------------------------------------------------------


class TestBuyerArticleId:
    def test_buyer_article_id_serializes(self, minimal_invoice_data):
        data = {
            **minimal_invoice_data,
            "lines": [
                {
                    **minimal_invoice_data["lines"][0],
                    "buyer_article_id": "BUY-001",
                }
            ],
        }
        invoice = BEInvoice.model_validate(data)
        xml_str = BEUBLSerializer().serialize_be_str(invoice)
        root = fromstring(xml_str)
        ns = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        bid = root.find(".//cac:InvoiceLine/cac:Item/cac:BuyersItemIdentification/cbc:ID", ns)
        assert bid is not None
        assert bid.text == "BUY-001"

    def test_backward_compat_buyer_item_id_alias(self, minimal_invoice_data):
        data = {
            **minimal_invoice_data,
            "lines": [
                {
                    **minimal_invoice_data["lines"][0],
                    "buyer_item_id": "OLD-001",
                }
            ],
        }
        invoice = BEInvoice.model_validate(data)
        assert invoice.lines[0].buyer_article_id == "OLD-001"


# ---------------------------------------------------------------------------
# BE-LC-5 — parse_ubl_invoice_be
# ---------------------------------------------------------------------------


class TestParseUblInvoiceBe:
    @pytest.mark.asyncio
    async def test_round_trip(self, minimal_invoice_data):
        data = {**minimal_invoice_data, "buyer_reference": "PO-7"}
        invoice = BEInvoice.model_validate(data)
        xml_bytes = BEUBLSerializer().serialize_be(invoice)
        xml_str = xml_bytes.decode("utf-8")
        result = await parse_ubl_invoice_be(xml_content=xml_str)
        assert result["success"] is True
        parsed = result["invoice"]
        assert parsed["invoice_number"] == "TEST-2024-001"
        assert parsed["buyer_reference"] == "PO-7"
        assert Decimal(str(parsed["sum_of_line_net_amounts"])) == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_malformed_xml_returns_error(self):
        result = await parse_ubl_invoice_be(xml_content="<broken")
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_string_returns_error(self):
        result = await parse_ubl_invoice_be(xml_content="")
        assert result["success"] is False


# ---------------------------------------------------------------------------
# BE-LC-2 — structured warning when BCE_API_KEY absent
# ---------------------------------------------------------------------------


class TestBceApiKeyWarning:
    @pytest.mark.asyncio
    async def test_warning_present_when_key_absent(self, monkeypatch):
        monkeypatch.delenv("BCE_API_KEY", raising=False)
        from mcp_einvoicing_be.tools.lookup import lookup_vat_be

        try:
            result = await lookup_vat_be(vat_number="BE0428759497")
        except Exception:
            pytest.skip("BCE API not reachable")
        if result.get("found") or not result.get("found"):
            assert "warning" in result
            assert result["warning"]["code"] == "BCE_API_KEY_MISSING"


# ---------------------------------------------------------------------------
# BE-LC-3 — structured error for Peppol lookup failures
# ---------------------------------------------------------------------------


class TestPeppolStructuredError:
    @pytest.mark.asyncio
    async def test_connection_error_returns_structured_dict(self, monkeypatch):
        from mcp_einvoicing_be.tools.lookup import check_peppol_participant_be

        async def _raise(*args, **kwargs):
            raise ConnectionError("DNS resolution failed")

        from mcp_einvoicing_core.peppol import PeppolSMPClient

        monkeypatch.setattr(PeppolSMPClient, "lookup_participant", _raise)

        result = await check_peppol_participant_be(identifier="0208:0428759497")
        assert result["registered"] is False
        assert "ConnectionError" in result["error"]
