"""Belgian-specific utility functions.

Generic utilities (IBAN validation, amount/quantity formatting, date validation,
XML element construction) are provided by mcp-einvoicing-core and should be
imported from there. Only Belgium-specific helpers live here.
"""

from __future__ import annotations

import re
from xml.etree.ElementTree import Element, ParseError, fromstring


def normalize_vat_be(vat_number: str) -> str:
    """Normalize a Belgian VAT/enterprise number to 'BE' + 10-digit format.

    Accepts:
    - ``BE0123456789``
    - ``0123456789``
    - ``BE 0123.456.789``
    - ``0123.456.789``

    Raises ``ValueError`` if the result is not exactly 10 digits.
    """
    cleaned = re.sub(r"[\s.\-]", "", vat_number.upper())
    digits = cleaned[2:] if cleaned.startswith("BE") else cleaned

    if not re.fullmatch(r"\d{10}", digits):
        raise ValueError(
            f"Invalid Belgian VAT/enterprise number: {vat_number!r}. "
            "Expected 10 digits (with optional 'BE' prefix)."
        )

    return f"BE{digits}"


def parse_ubl_xml(xml: str) -> tuple[Element | None, str | None]:
    """Parse a UBL XML string and return ``(root_element, None)`` or ``(None, error_str)``."""
    try:
        return fromstring(xml.strip()), None
    except ParseError as exc:
        return None, f"XML parse error: {exc}"


def format_belgian_ogm(base_digits: str) -> str:
    """Generate a Belgian OGM/VCS structured payment reference (+++xxx/xxxx/xxxxx+++).

    The modulo-97 check digit is appended to the last segment.
    ``base_digits`` should be a string of up to 10 digits used as the base reference.
    """
    base = re.sub(r"\D", "", base_digits)[:10].ljust(10, "0")
    checksum = int(base) % 97 or 97
    return f"+++{base[:3]}/{base[3:7]}/{base[7:10]}{checksum:02d}+++"


def vat_rate_to_category(rate: float) -> str:
    """Map a Belgian VAT rate percentage to its EN 16931 tax category code."""
    return "Z" if rate == 0.0 else "S"
