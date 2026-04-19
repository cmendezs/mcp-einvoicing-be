"""Belgian party models — extend mcp-einvoicing-core base types."""

from pydantic import Field
from mcp_einvoicing_core import InvoiceParty, PartyAddress


class BEAddress(PartyAddress):
    """Belgian postal address.

    Extends ``PartyAddress`` with no extra fields — the base already covers
    street, city, postal_code, and country_code. Kept as a named subclass so
    Belgian-specific validation (e.g. postal code format) can be added later.
    """


class BEParty(InvoiceParty):
    """Base Belgian party (supplier or customer).

    Adds the Peppol participant ID and the Belgian KBO/BCE scheme identifier
    on top of the core ``InvoiceParty``.
    """

    peppol_id: str | None = Field(
        default=None,
        description="Peppol participant ID, e.g. '0208:0123456789'",
    )
    peppol_scheme: str = Field(
        default="0208",
        description="Peppol ICD scheme for Belgium (KBO/BCE = 0208)",
    )


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
