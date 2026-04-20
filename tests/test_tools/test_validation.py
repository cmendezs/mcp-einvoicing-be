"""Tests for BEDocumentValidator tools."""

import pytest

from mcp_einvoicing_be.tools.validation import BEDocumentValidator

_val = BEDocumentValidator()


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
async def test_validate_pint_be_accepts_valid_xml(valid_pint_be_xml: str) -> None:
    if not valid_pint_be_xml:
        pytest.skip("Fixture invoice_valid_pint_be.xml not yet available")
    result = await _val.validate_pint_be(xml=valid_pint_be_xml)
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_mercurius_profile_is_recorded(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml, profile="mercurius")
    assert result["profile"] == "mercurius"


@pytest.mark.asyncio
async def test_default_profile_is_peppol(invalid_xml: str) -> None:
    result = await _val.validate_invoice_be(xml=invalid_xml)
    assert result["profile"] == "peppol-bis-3"
