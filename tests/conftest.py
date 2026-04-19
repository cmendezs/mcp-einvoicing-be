"""Shared pytest fixtures for mcp-einvoicing-be tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def minimal_invoice_data() -> dict:
    return {
        "invoice_number": "TEST-2024-001",
        "issue_date": date(2024, 1, 15).isoformat(),
        "currency_code": "EUR",
        "supplier": {
            "name": "Acme NV",
            "vat_number": "BE0123456789",
            "address": {
                "street": "Rue de la Loi 1",
                "city": "Brussels",
                "postal_code": "1000",
                "country_code": "BE",
            },
        },
        "customer": {
            "name": "Client SPRL",
            "vat_number": "BE0987654321",
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
