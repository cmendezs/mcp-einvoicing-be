"""Tests for BEDocumentGenerator.generate_invoice_be."""

from xml.etree.ElementTree import fromstring

import pytest

from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS, PROFILE_IDS
from mcp_einvoicing_be.tools.generation import BEDocumentGenerator

_gen = BEDocumentGenerator()


@pytest.mark.asyncio
async def test_generate_returns_xml_string(minimal_invoice_data: dict) -> None:
    result = await _gen.generate_invoice_be(invoice_data=minimal_invoice_data)
    assert isinstance(result["xml"], str)
    assert len(result["xml"]) > 0


@pytest.mark.asyncio
async def test_generate_is_well_formed_xml(minimal_invoice_data: dict) -> None:
    result = await _gen.generate_invoice_be(invoice_data=minimal_invoice_data)
    root = fromstring(result["xml"])
    assert root is not None


@pytest.mark.asyncio
async def test_generate_peppol_customization_id(minimal_invoice_data: dict) -> None:
    result = await _gen.generate_invoice_be(
        invoice_data=minimal_invoice_data, profile="peppol-bis-3"
    )  # noqa: E501
    assert result["customization_id"] == CUSTOMIZATION_IDS["peppol-bis-3"]
    assert result["profile_id"] == PROFILE_IDS["peppol-bis-3"]


@pytest.mark.asyncio
async def test_generate_pint_be_customization_id(minimal_invoice_data: dict) -> None:
    result = await _gen.generate_invoice_be(invoice_data=minimal_invoice_data, profile="pint-be")
    assert result["customization_id"] == CUSTOMIZATION_IDS["pint-be"]


@pytest.mark.asyncio
async def test_generate_contains_invoice_number(minimal_invoice_data: dict) -> None:
    result = await _gen.generate_invoice_be(invoice_data=minimal_invoice_data)
    assert "TEST-2024-001" in result["xml"]


@pytest.mark.asyncio
async def test_generate_rejects_empty_lines(minimal_invoice_data: dict) -> None:
    data = {**minimal_invoice_data, "lines": []}
    with pytest.raises(Exception):
        await _gen.generate_invoice_be(invoice_data=data)
