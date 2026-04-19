"""Tests for validation tools."""

import pytest

from mcp_einvoicing_be.tools.validation import validate_invoice_be, validate_pint_be


@pytest.mark.asyncio
async def test_validate_invoice_be_rejects_malformed_xml(invalid_xml: str) -> None:
    result = await validate_invoice_be(xml=invalid_xml, profile="peppol-bis-3")
    assert result["valid"] is False
    assert result["error_count"] >= 1
    messages = result["messages"]
    assert any(m["rule_id"] == "XML-PARSE" for m in messages)


@pytest.mark.asyncio
async def test_validate_invoice_be_accepts_valid_xml(valid_peppol_xml: str) -> None:
    if not valid_peppol_xml:
        pytest.skip("Fixture invoice_valid_peppol.xml not yet available")
    result = await validate_invoice_be(xml=valid_peppol_xml, profile="peppol-bis-3")
    assert result["valid"] is True
    assert result["error_count"] == 0


@pytest.mark.asyncio
async def test_validate_pint_be_accepts_valid_xml(valid_pint_be_xml: str) -> None:
    if not valid_pint_be_xml:
        pytest.skip("Fixture invoice_valid_pint_be.xml not yet available")
    result = await validate_pint_be(xml=valid_pint_be_xml)
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_invoice_be_profile_mercurius(invalid_xml: str) -> None:
    result = await validate_invoice_be(xml=invalid_xml, profile="mercurius")
    assert result["profile"] == "mercurius"
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_validate_invoice_be_default_profile_is_peppol(invalid_xml: str) -> None:
    result = await validate_invoice_be(xml=invalid_xml)
    assert result["profile"] == "peppol-bis-3"
