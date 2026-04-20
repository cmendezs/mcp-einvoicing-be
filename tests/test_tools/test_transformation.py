"""Tests for the transform_to_ubl tool."""

from xml.etree.ElementTree import fromstring

import pytest

from mcp_einvoicing_be.tools.transformation import transform_to_ubl


@pytest.mark.asyncio
async def test_returns_xml_string(minimal_invoice_data: dict) -> None:
    result = await transform_to_ubl(data=minimal_invoice_data)
    assert isinstance(result["xml"], str)
    assert len(result["xml"]) > 0


@pytest.mark.asyncio
async def test_produces_well_formed_xml(minimal_invoice_data: dict) -> None:
    result = await transform_to_ubl(data=minimal_invoice_data)
    assert fromstring(result["xml"]) is not None


@pytest.mark.asyncio
async def test_warns_when_customer_vat_absent(minimal_invoice_data: dict) -> None:
    data = {**minimal_invoice_data, "buyer": {**minimal_invoice_data["buyer"], "tax_id": None}}
    result = await transform_to_ubl(data=data)
    assert any("VAT" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_warns_when_iban_missing_for_credit_transfer(minimal_invoice_data: dict) -> None:
    data = {**minimal_invoice_data, "payment_means_code": "30"}
    result = await transform_to_ubl(data=data)
    assert any("IBAN" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_no_warnings_for_complete_data(minimal_invoice_data_with_payment: dict) -> None:
    result = await transform_to_ubl(data=minimal_invoice_data_with_payment)
    assert result["warnings"] == []
