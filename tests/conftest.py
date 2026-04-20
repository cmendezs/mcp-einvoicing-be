"""Shared pytest fixtures for mcp-einvoicing-be tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def minimal_invoice_data() -> dict:
    return {
        "number": "TEST-2024-001",
        "date": "2024-01-15",
        "currency": "EUR",
        "seller": {
            "name": "Acme NV",
            "tax_id": "BE0123456789",
            "address": {
                "street": "Rue de la Loi 1",
                "city": "Brussels",
                "postal_code": "1000",
                "country_code": "BE",
            },
        },
        "buyer": {
            "name": "Client SPRL",
            "tax_id": "BE0987654321",
            "address": {
                "street": "Koningsstraat 2",
                "city": "Antwerp",
                "postal_code": "2000",
                "country_code": "BE",
            },
        },
        "lines": [
            {
                "description": "Consulting services",
                "quantity": 8.0,
                "unit_price": 125.00,
                "vat_rate": 21.0,
            }
        ],
    }


@pytest.fixture
def minimal_invoice_data_with_payment(minimal_invoice_data: dict) -> dict:
    return {
        **minimal_invoice_data,
        "payment_means_code": "30",
        "payment": {
            "iban": "BE68539007547034",
            "bic": "NICABEBB",
            "ogm_reference": "+++000/0000/00097+++",
        },
    }


@pytest.fixture
def valid_peppol_xml() -> str:
    path = FIXTURES_DIR / "invoice_valid_peppol.xml"
    if path.exists():
        return path.read_text()
    return ""


@pytest.fixture
def valid_pint_be_xml() -> str:
    path = FIXTURES_DIR / "invoice_valid_pint_be.xml"
    if path.exists():
        return path.read_text()
    return ""


@pytest.fixture
def invalid_xml() -> str:
    return "<Invoice><broken"
