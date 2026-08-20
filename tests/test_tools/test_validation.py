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
async def test_peppol_bis_3_malformed_xml_reports_xml_parse_error(invalid_xml: str) -> None:
    """v0.8.0 [CORE-EN16931-BASE-SCHEMATRON-1]: peppol-bis-3/pint-eu now run
    real Schematron validation (core's bundled EN16931-base validator), so
    malformed XML reaches the parse step and gets a real XML-PARSE finding
    from the Schematron engine, not the old unconditional
    PEPPOL-VALIDATION-UNAVAILABLE."""
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="peppol-bis-3")
    assert result["valid"] is False
    assert result["engine"] == "schematron-xslt"
    assert result["scope"] == "en16931-base-only"
    assert any("XML-PARSE" in str(m) for m in result["errors"])


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
async def test_generate_validate_roundtrip_peppol_bis_3_finds_real_gaps() -> None:
    """v0.8.0 [CORE-EN16931-BASE-SCHEMATRON-1]: with real CEN EN16931 base
    validation now running (instead of the old unconditional "unavailable"),
    the minimal fixture invoice's real gaps surface: no payment account
    identifier for the default SEPA credit-transfer payment means (BR-61),
    and no PayableAmount due-date signal reaching the wire format (BR-CO-25 —
    a known separate BE serializer bug where PaymentDueDate is emitted in
    the wrong place; see the payment-bearing test below and the tracked
    follow-up). This is a real improvement over both the old hand-rolled
    approximation (which never checked either rule) and the old unconditional
    "unavailable" (which caught neither)."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["valid"] is False
    assert result["engine"] == "schematron-xslt"
    assert result["scope"] == "en16931-base-only"
    rule_ids = {str(e).split(":")[0] for e in result["errors"]}
    assert "BR-CO-25" in rule_ids


@pytest.mark.asyncio
async def test_generate_validate_roundtrip_peppol_bis_3_fully_compliant() -> None:
    """A payment-bearing fixture (IBAN + due_date set) is now fully compliant:
    BR-61 (payment account identifier for SEPA credit transfer) and BR-CO-25
    (due date or payment terms note required) both pass. BR-CO-25 previously
    fired here due to a core wire_formats.py bug — EN16931UBLSerializer only
    emitted <cbc:PaymentDueDate> inside PaymentMeans, never the top-level
    <cbc:DueDate> that BR-CO-25 actually checks for — fixed in core
    (mcp-einvoicing-core>=1.18.1). This proves the arithmetic/business-rule
    checks this validator adds are real and discriminating, not just a
    blanket failure."""
    xml = _generated_invoice_xml(payment={"iban": "BE68539007547034", "due_date": "2024-02-15"})
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["valid"] is True, result["errors"]
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_generate_validate_roundtrip_mercurius() -> None:
    """BE-SC-12 regression guard: standard BIS 3.0 output with 0208 endpoints
    is accepted under the mercurius profile (no fabricated CustomizationID
    requirement, real EndpointID checks)."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="mercurius")
    assert result["valid"] is True, result["errors"]


@pytest.mark.asyncio
async def test_metadata_engine_schematron_xslt_en16931_base_only_scope() -> None:
    """BE-SC-11 / v0.8.0 [CORE-EN16931-BASE-SCHEMATRON-1]: metadata.engine and
    metadata.scope report which validation actually ran. Core's bundled
    EN16931-base Schematron is always available now, so peppol-bis-3 reports
    'schematron-xslt' / 'en16931-base-only' — real base validation, but
    explicitly not full Peppol BIS3 conformance (no overlay rules checked)."""
    xml = _generated_invoice_xml()
    result = await _val.validate_invoice_be(xml=xml, profile="peppol-bis-3")
    assert result["engine"] == "schematron-xslt"
    assert result["scope"] == "en16931-base-only"
    assert any("EN16931-BASE-ONLY-SCOPE" in str(w) for w in result["warnings"])
