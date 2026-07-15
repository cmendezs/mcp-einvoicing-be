"""Tests for BEDocumentValidator tools."""

import pytest

from mcp_einvoicing_be.models.invoice import BEInvoice
from mcp_einvoicing_be.standards.ubl import BEUBLSerializer
from mcp_einvoicing_be.tools.validation import BEDocumentValidator

_val = BEDocumentValidator()


def _generated_invoice_xml(**extra_top_level: object) -> str:
    """Build and serialize a minimal, well-formed BE invoice for roundtrip tests."""
    data: dict = {
        "number": "TEST-2024-001",
        "date": "2024-01-15",
        "currency": "EUR",
        "seller": {
            "name": "Acme NV",
            "tax_id": "BE0428759497",
            "electronic_address": "0208:0428759497",
            "address": {
                "street": "Rue de la Loi 1",
                "city": "Brussels",
                "postal_code": "1000",
                "country_code": "BE",
            },
        },
        "buyer": {
            "name": "Client SPRL",
            "tax_id": "BE0403170701",
            "electronic_address": "0208:0403170701",
            "reference": "PO-REF-12345",
            "address": {
                "street": "Koningsstraat 2",
                "city": "Antwerp",
                "postal_code": "2000",
                "country_code": "BE",
            },
        },
        "purchase_order_reference": "PO-777",
        "lines": [
            {
                "description": "Consulting services",
                "quantity": 8.0,
                "unit_price": 125.00,
                "vat_rate": 21.0,
            }
        ],
        **extra_top_level,
    }
    invoice = BEInvoice.model_validate(data)
    return BEUBLSerializer().serialize_be_str(invoice)


@pytest.mark.asyncio
async def test_rejects_malformed_xml(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="peppol-bis-3")
    assert result["valid"] is False
    assert result["errors"]
    assert any("XML-PARSE" in str(m) for m in result["errors"])


@pytest.mark.asyncio
async def test_accepts_valid_peppol_xml(valid_peppol_xml: str) -> None:
    if not valid_peppol_xml:
        pytest.skip("Fixture invoice_valid_peppol.xml not yet available")
    result = await _val.validate_invoice_be(xml=valid_peppol_xml, profile="peppol-bis-3")
    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_mercurius_profile_is_recorded(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="mercurius")
    assert result["profile"] == "mercurius"


@pytest.mark.asyncio
async def test_default_profile_is_peppol(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml)
    assert result["profile"] == "peppol-bis-3"


@pytest.mark.asyncio
async def test_generate_validate_roundtrip_peppol_bis_3() -> None:
    """BE-SC-9/BE-SC-10 regression guard: the package's own generated output
    must pass its own validator on the default profile."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["valid"] is True, result["errors"]
    assert result["engine"] == "xpath-fallback"


@pytest.mark.asyncio
async def test_generate_validate_roundtrip_mercurius() -> None:
    """BE-SC-12 regression guard: standard BIS 3.0 output with 0208 endpoints
    is accepted under the mercurius profile (no fabricated CustomizationID
    requirement, real EndpointID checks)."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="mercurius")
    assert result["valid"] is True, result["errors"]


@pytest.mark.asyncio
async def test_metadata_engine_xpath_fallback_when_no_schematron() -> None:
    """BE-SC-11 regression guard: metadata.engine reports which validation
    engine actually ran. No compiled Schematron XSLT is bundled yet (see
    [GAP id=core.schematron.be_bundled_xslt]), so this is xpath-fallback."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["engine"] == "xpath-fallback"
