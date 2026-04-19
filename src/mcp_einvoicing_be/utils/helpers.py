"""Shared utility functions for Belgian e-invoicing."""

from __future__ import annotations

import re
from xml.etree.ElementTree import Element, ParseError, fromstring


def normalize_vat_be(vat_number: str) -> str:
    """Normalize a Belgian VAT/enterprise number to the 'BE' + 10-digit format.

    Accepts:
    - ``BE0123456789``
    - ``0123456789``
    - ``BE 0123.456.789``
    - ``0123.456.789``

    Raises ValueError if the number is not a valid Belgian enterprise number.
    """
    cleaned = re.sub(r"[\s.\-]", "", vat_number.upper())
    if cleaned.startswith("BE"):
        digits = cleaned[2:]
    else:
        digits = cleaned

    if not re.fullmatch(r"\d{10}", digits):
        raise ValueError(
            f"Invalid Belgian VAT/enterprise number: {vat_number!r}. "
            "Expected 10 digits (with optional 'BE' prefix)."
        )

    return f"BE{digits}"


def parse_ubl_xml(xml: str) -> tuple[Element | None, str | None]:
    """Parse a UBL XML string and return (root_element, error_message).

    Returns ``(element, None)`` on success and ``(None, error_str)`` on failure.
    """
    try:
        root = fromstring(xml.strip())
        return root, None
    except ParseError as exc:
        return None, f"XML parse error: {exc}"


def format_belgian_ogm(amount: float, supplier_digits: str) -> str:
    """Generate a Belgian OGM/VCS structured payment reference (+++ format).

    The OGM (Overschrijvingsformulier met Gestructureerde Mededeling) reference
    is the standard structured creditor reference used in Belgian banking.
    Format: +++xxx/xxxx/xxxxx+++ with a modulo-97 check digit.

    ``supplier_digits`` should be a string of digits used as the base reference.
    """
    base = re.sub(r"\D", "", supplier_digits)[:10].ljust(10, "0")
    part1 = base[:3]
    part2 = base[3:7]
    part3_base = base[7:10]
    checksum = int(base) % 97 or 97
    part3 = f"{part3_base}{checksum:02d}"
    return f"+++{part1}/{part2}/{part3}+++"


def is_valid_iban(iban: str) -> bool:
    """Basic IBAN format validation (structure check, not modulo-97)."""
    cleaned = re.sub(r"\s", "", iban.upper())
    return bool(re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{1,30}", cleaned))


def vat_rate_to_category(rate: float) -> str:
    """Map a Belgian VAT rate percentage to its EN 16931 tax category code."""
    if rate == 0.0:
        return "Z"
    return "S"
