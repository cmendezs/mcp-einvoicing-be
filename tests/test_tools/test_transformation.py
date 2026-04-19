"""Tests for the transform_to_ubl tool."""

import pytest
from xml.etree.ElementTree import fromstring

from mcp_einvoicing_be.tools.transformation import transform_to_ubl


@pytest.mark.asyncio
async def test_transform_to_ubl_returns_xml(minimal_invoice_data: dict) -> None:
    result = await transform_to_ubl(data=minimal_invoice_data)
    assert "xml" in result
    assert isinstance(result["xml"], str)
    assert len(result["xml"]) > 0


@pytest.mark.asyncio
async def test_transform_to_ubl_is_well_formed(minimal_invoice_data: dict) -> None:
    result = await transform_to_ubl(data=minimal_invoice_data)
    root = fromstring(result["xml"])
    assert root is not None


@pytest.mark.asyncio
async def test_transform_to_ubl_warns_missing_customer_vat(minimal_invoice_data: dict) -> None:
    data = dict(minimal_invoice_data)
    customer = dict(data["customer"])
    customer["vat_number"] = None
    data["customer"] = customer
    result = await transform_to_ubl(data=data)
    assert any("VAT" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_transform_to_ubl_warns_missing_iban_for_credit_transfer(
    minimal_invoice_data: dict,
) -> None:
    data = dict(minimal_invoice_data)
    data["payment_means_code"] = "30"
    data["iban"] = None
    result = await transform_to_ubl(data=data)
    assert any("IBAN" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_transform_to_ubl_no_warnings_for_complete_data(
    minimal_invoice_data: dict,
) -> None:
    data = dict(minimal_invoice_data)
    data["iban"] = "BE68539007547034"
    result = await transform_to_ubl(data=data)
    assert result["warnings"] == []
