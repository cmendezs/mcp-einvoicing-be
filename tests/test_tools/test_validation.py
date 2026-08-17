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
async def test_rejects_malformed_xml_mercurius(invalid_xml: str) -> None:
    """mercurius still parses+evaluates, so malformed XML still gets XML-PARSE."""
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="mercurius")
    assert result["valid"] is False
    assert result["errors"]
    assert any("XML-PARSE" in str(m) for m in result["errors"])


@pytest.mark.asyncio
async def test_peppol_bis_3_unavailable_without_schematron(invalid_xml: str) -> None:
    """v0.7.0: peppol-bis-3/pint-eu report an explicit unavailable result
    (not a parse attempt, not a partial pass/fail) when no compiled Schematron
    is loaded — even malformed XML gets PEPPOL-VALIDATION-UNAVAILABLE, not
    XML-PARSE, since validation never reaches the parse step."""
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="peppol-bis-3")
    assert result["valid"] is False
    assert result["engine"] == "unavailable"
    assert any("PEPPOL-VALIDATION-UNAVAILABLE" in str(m) for m in result["errors"])


@pytest.mark.asyncio
async def test_accepts_valid_peppol_xml_under_mercurius(valid_peppol_xml: str) -> None:
    """No real Schematron is loaded, so peppol-bis-3 itself cannot assert
    validity here — exercise the same fixture under mercurius instead, which
    still runs real rule evaluation (endpoint scheme, PO reference)."""
    if not valid_peppol_xml:
        pytest.skip("Fixture invoice_valid_peppol.xml not yet available")
    result = await _val.validate_invoice_be(xml=valid_peppol_xml, profile="mercurius")
    assert result["valid"] is True, result["errors"]


@pytest.mark.asyncio
async def test_mercurius_profile_is_recorded(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="mercurius")
    assert result["profile"] == "mercurius"


@pytest.mark.asyncio
async def test_mercurius_result_carries_scope_warning() -> None:
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="mercurius")
    assert any("MERCURIUS-SCOPE" in str(w) for w in result["warnings"])


@pytest.mark.asyncio
async def test_default_profile_is_peppol(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml)
    assert result["profile"] == "peppol-bis-3"


@pytest.mark.asyncio
async def test_generate_validate_roundtrip_peppol_bis_3_unavailable() -> None:
    """v0.7.0: with no real Schematron loaded, the peppol-bis-3 profile can no
    longer claim its own generated output is valid — it reports unavailable
    instead of a hand-rolled approximation's pass/fail."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["valid"] is False
    assert result["engine"] == "unavailable"


@pytest.mark.asyncio
async def test_generate_validate_roundtrip_mercurius() -> None:
    """BE-SC-12 regression guard: standard BIS 3.0 output with 0208 endpoints
    is accepted under the mercurius profile (no fabricated CustomizationID
    requirement, real EndpointID checks)."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="mercurius")
    assert result["valid"] is True, result["errors"]


@pytest.mark.asyncio
async def test_metadata_engine_unavailable_when_no_schematron() -> None:
    """BE-SC-11 / v0.7.0: metadata.engine reports which validation engine
    actually ran. No compiled Schematron XSLT is bundled yet (see
    [GAP id=core.schematron.be_bundled_xslt]), so peppol-bis-3 is
    'unavailable' rather than a hand-rolled 'xpath-fallback'."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["engine"] == "unavailable"
