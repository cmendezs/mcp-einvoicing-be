"""Belgian-specific utility functions.

Generic utilities (IBAN validation, amount/quantity formatting, date validation,
XML element construction) are provided by mcp-einvoicing-core and should be
imported from there.  Only Belgium-specific helpers live here.

BE-TL-1 (resolved): normalize_vat_be now validates the modulo-97 check digit
(identical to the IBAN modulo-97 algorithm) as mandated by SPF Finances.

BE-TL-3 (resolved): vat_rate_to_category no longer maps every non-zero rate to
"S".  Callers must pass an explicit VatCategory; this helper is retained only
for the legacy zero-rate detection use case.
"""

from __future__ import annotations

import re
from typing import Any


def normalize_vat_be(vat_number: str) -> str:
    """Normalize a Belgian VAT/enterprise number to 'BE' + 10-digit format.

    Accepts:
    - ``BE0123456789``
    - ``0123456789``
    - ``BE 0123.456.789``
    - ``0123.456.789``

    Validates the modulo-97 check digit: the last two digits of the 10-digit
    number must equal ``97 - (first_8_digits mod 97)`` (or 97 when the remainder
    is 0).  This algorithm is identical to the IBAN check digit (ISO 7064 MOD 97-10).

    Raises:
        ValueError: if the string cannot be normalised to 10 digits, or if the
            check digit is invalid.
    """
    cleaned = re.sub(r"[\s.\-]", "", vat_number.upper())
    digits = cleaned[2:] if cleaned.startswith("BE") else cleaned

    if not re.fullmatch(r"\d{10}", digits):
        raise ValueError(
            f"Invalid Belgian VAT/enterprise number: {vat_number!r}. "
            "Expected 10 digits (with optional 'BE' prefix)."
        )

    # BE-TL-1: Modulo-97 check digit validation (SPF Finances / FOD Financiën).
    # The first digit is always 0 or 1.  The last 2 digits are the check digits.
    # Algorithm: 97 - (int(first_8_digits) % 97) == int(last_2_digits)
    # Edge case: when the remainder is 0 the check digits are 97.
    first_eight = int(digits[:8])
    check_digits = int(digits[8:])
    expected = 97 - (first_eight % 97)
    if expected == 0:
        expected = 97
    if check_digits != expected:
        raise ValueError(
            f"Invalid Belgian VAT/enterprise number: {vat_number!r}. "
            f"Check digit mismatch: expected {expected:02d}, got {check_digits:02d}."
        )

    return f"BE{digits}"


def parse_ubl_xml(xml: str | bytes) -> tuple[Any, str | None]:
    """Parse a UBL XML string/bytes with lxml and return ``(root, None)`` or ``(None, error)``.

    Uses lxml for XPath namespace support required by ``_evaluate_rule``.
    The return type is ``lxml.etree._Element | None`` (typed as ``Any`` to avoid
    exposing the lxml internal type in the public signature).
    """
    from lxml import etree  # noqa: PLC0415

    try:
        raw = xml.encode("utf-8") if isinstance(xml, str) else xml
        root = etree.fromstring(raw.strip())
        return root, None
    except etree.XMLSyntaxError as exc:
        return None, f"XML parse error: {exc}"


def validate_belgian_ogm(value: str) -> str:
    """Validate a Belgian OGM/VCS structured payment reference.

    Accepts both the formatted form (+++xxx/xxxx/xxxcc+++) and bare 12-digit form.
    The last two digits are the modulo-97 check digits: remainder of the first 10
    digits divided by 97 (or 97 when the remainder is 0).

    Returns the normalised +++xxx/xxxx/xxxcc+++ form on success.

    Raises:
        ValueError: if the check digit does not match or the format is invalid.
    """
    digits = re.sub(r"[+/\s.\-]", "", value)
    if not re.fullmatch(r"\d{12}", digits):
        raise ValueError(
            f"Invalid OGM/VCS reference: {value!r}. Expected 12 digits "
            "(with optional +++xxx/xxxx/xxxcc+++ formatting)."
        )
    base = int(digits[:10])
    check = int(digits[10:])
    expected = base % 97 or 97
    if check != expected:
        raise ValueError(
            f"Invalid OGM/VCS check digit in {value!r}: expected {expected:02d}, got {check:02d}."
        )
    return f"+++{digits[:3]}/{digits[3:7]}/{digits[7:12]}+++"


def format_belgian_ogm(base_digits: str) -> str:
    """Generate a Belgian OGM/VCS structured payment reference (+++xxx/xxxx/xxxxx+++).

    The modulo-97 check digit is appended to the last segment.
    ``base_digits`` should be a string of up to 10 digits used as the base reference.
    """
    base = re.sub(r"\D", "", base_digits)[:10].ljust(10, "0")
    checksum = int(base) % 97 or 97
    return f"+++{base[:3]}/{base[3:7]}/{base[7:10]}{checksum:02d}+++"


def vat_rate_to_category(rate: float) -> str:
    """Map a Belgian VAT rate percentage to its UNCL5305 tax category code.

    BE-TL-3 (resolved): only the unambiguous zero-rate mapping is retained.
    For all other rates the caller must select an explicit VatCategory value,
    because the rate alone is not sufficient to determine the category:
    - 21 % may be STANDARD ("S") or, for intra-community supplies, "K"
    - 12 % uses REDUCED_12 ("AA"), not STANDARD
    - 6 %  uses REDUCED_6 ("AB"), not STANDARD
    - 0 %  may be ZERO_RATED ("Z"), EXEMPT ("E"), REVERSE_CHARGE ("AE"), etc.

    This function is retained for backward compatibility and for automated
    zero-rate detection only.  Callers with non-zero rates should set
    ``vat_category`` explicitly on ``BEInvoiceLine``.
    """
    return "Z" if rate == 0.0 else "S"
