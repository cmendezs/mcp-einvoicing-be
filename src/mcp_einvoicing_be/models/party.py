"""Belgian party models — extend mcp-einvoicing-core base types."""

from typing import Any

from mcp_einvoicing_core import InvoiceParty, PartyAddress, TaxIdentifier
from pydantic import Field, field_validator


class BEAddress(PartyAddress):  # type: ignore[misc]
    """Belgian postal address.

    Extends ``PartyAddress`` with no extra fields — the base already covers
    street, city, postal_code, and country_code. Kept as a named subclass so
    Belgian-specific validation (e.g. postal code format) can be added later.
    """


class BEParty(InvoiceParty):  # type: ignore[misc]
    """Base Belgian party (supplier or customer).

    Adds the Peppol participant ID and the Belgian KBO/BCE scheme identifier
    on top of the core ``InvoiceParty``.
    """

    tax_id: TaxIdentifier | None = Field(default=None)
    peppol_id: str | None = Field(
        default=None,
        description="Peppol participant ID, e.g. '0208:0123456789'",
    )
    peppol_scheme: str = Field(
        default="0208",
        description="Peppol ICD scheme for Belgium (KBO/BCE = 0208)",
    )

    @field_validator("tax_id", mode="before")
    @classmethod
    def coerce_tax_id(cls, v: Any) -> Any:
        """Accept 'BE0123456789' string shorthand in addition to TaxIdentifier dict/object."""
        if isinstance(v, str) and len(v) >= 2 and v[:2].isalpha():
            return {"country_code": v[:2].upper(), "identifier": v[2:]}
        return v


class Supplier(BEParty):
    """Belgian invoice supplier (seller)."""

    contact_name: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    contact_phone: str | None = Field(default=None)


class Customer(BEParty):
    """Belgian invoice customer (buyer)."""

    contact_name: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    reference: str | None = Field(
        default=None,
        description="Buyer's internal reference (BT-10)",
    )
