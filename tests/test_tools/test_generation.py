"""Tests for the generate_invoice_be tool."""

import pytest
from xml.etree.ElementTree import fromstring

from mcp_einvoicing_be.tools.generation import generate_invoice_be
from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS, PROFILE_IDS


@pytest.mark.asyncio
async def test_generate_invoice_be_returns_xml(minimal_invoice_data: dict) -> None:
    result = await generate_invoice_be(invoice_data=minimal_invoice_data)
    assert "xml" in result
    xml_str = result["xml"]
    assert isinstance(xml_str, str)
    assert len(xml_str) > 0


@pytest.mark.asyncio
async def test_generate_invoice_be_is_well_formed_xml(minimal_invoice_data: dict) -> None:
    result = await generate_invoice_be(invoice_data=minimal_invoice_data)
    root = fromstring(result["xml"])
    assert root is not None


@pytest.mark.asyncio
async def test_generate_invoice_be_peppol_customization_id(minimal_invoice_data: dict) -> None:
    result = await generate_invoice_be(invoice_data=minimal_invoice_data, profile="peppol-bis-3")
    assert result["customization_id"] == CUSTOMIZATION_IDS["peppol-bis-3"]
    assert result["profile_id"] == PROFILE_IDS["peppol-bis-3"]


@pytest.mark.asyncio
async def test_generate_invoice_be_pint_be_customization_id(minimal_invoice_data: dict) -> None:
    result = await generate_invoice_be(invoice_data=minimal_invoice_data, profile="pint-be")
    assert result["customization_id"] == CUSTOMIZATION_IDS["pint-be"]


@pytest.mark.asyncio
async def test_generate_invoice_be_contains_invoice_number(minimal_invoice_data: dict) -> None:
    result = await generate_invoice_be(invoice_data=minimal_invoice_data)
    assert "TEST-2024-001" in result["xml"]


@pytest.mark.asyncio
async def test_generate_invoice_be_rejects_missing_lines(minimal_invoice_data: dict) -> None:
    data = dict(minimal_invoice_data)
    data["lines"] = []
    with pytest.raises(Exception):
        await generate_invoice_be(invoice_data=data)
