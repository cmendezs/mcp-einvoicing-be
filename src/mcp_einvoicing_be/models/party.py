"""Belgian party models — extend mcp-einvoicing-core EN16931 base types.

BE-SC-2 (resolved): BEParty now extends EN16931Party; BEAddress now extends
EN16931Address.  The Belgian input API (street / postal_code field names) is
preserved via AliasChoices so that existing callers do not break.
"""

from typing import Any

from mcp_einvoicing_core import TaxIdentifier
from mcp_einvoicing_core.en16931 import EN16931Address, EN16931Party
from pydantic import AliasChoices, ConfigDict, Field, field_validator, model_validator


class BEAddress(EN16931Address):
    """Belgian postal address.

    Extends ``EN16931Address`` with backward-compatible aliases for the legacy
    Belgian field names ``street`` (maps to ``line_one``, BT-35 / BT-50) and
    ``postal_code`` (maps to ``postcode``, BT-38 / BT-53).
    """

    model_config = ConfigDict(populate_by_name=True)

    line_one: str = Field(
        ...,
        description="Street and house number (BT-35 / BT-50)",
        validation_alias=AliasChoices("line_one", "street"),
    )
    postcode: str = Field(
        ...,
        description="Postal / ZIP code (BT-38 / BT-53)",
        validation_alias=AliasChoices("postcode", "postal_code"),
    )


class BEParty(EN16931Party):
    """Base Belgian trading party (supplier or customer).

    Extends ``EN16931Party`` with:
    - a structured ``TaxIdentifier`` for KBO/BCE modulo-97-validated numbers,
    - the Belgian Peppol ICD scheme (0208),
    - automatic sync of ``tax_id`` → ``vat_id`` (BT-31 / BT-48).

    Override ``address`` to ``BEAddress`` so the Belgian input aliases
    (street / postal_code) are accepted at the party level.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Override address type to BEAddress so street / postal_code aliases work
    address: BEAddress

    # Structured Belgian VAT/enterprise number — additional field not in EN16931Party
    tax_id: TaxIdentifier | None = Field(
        default=None,
        description="Belgian VAT/enterprise number as structured TaxIdentifier",
    )
    # Peppol ICD scheme; 0208 = KBO/BCE Belgian enterprise number
    peppol_scheme: str = Field(
        default="0208",
        description="Peppol ICD scheme for Belgium (KBO/BCE = 0208)",
    )

    @field_validator("tax_id", mode="before")
    @classmethod
    def coerce_tax_id(cls, v: Any) -> Any:
        """Accept 'BE0428759497' string shorthand in addition to TaxIdentifier dict/object."""
        if isinstance(v, str) and len(v) >= 2 and v[:2].isalpha():
            return {"country_code": v[:2].upper(), "identifier": v[2:]}
        return v

    @field_validator("tax_id", mode="after")
    @classmethod
    def _validate_tax_id_checksum(cls, v: TaxIdentifier | None) -> TaxIdentifier | None:
        """Enforce the BCE/KBO modulo-97 check digit on the structured tax_id (BT-31 / BT-48).

        Delegates to the core 3-layer pattern: TaxIdentifier.validate_be_vat (Layer 1).
        """
        if v is None:
            return v
        full = f"{v.country_code}{v.identifier}"
        ok, error = TaxIdentifier.validate_be_vat(full)
        if not ok:
            raise ValueError(f"Invalid Belgian VAT/enterprise number: {error}")
        return v

    @model_validator(mode="after")
    def sync_vat_and_endpoint(self) -> "BEParty":
        """Populate ``vat_id`` (BT-31/BT-48) from ``tax_id`` when the caller uses the
        structured form only, and propagate ``peppol_scheme`` to
        ``electronic_address_scheme`` when an electronic address is given without
        an explicit scheme.
        """
        if self.tax_id and not self.vat_id:
            self.vat_id = f"{self.tax_id.country_code}{self.tax_id.identifier}"
        if self.electronic_address and not self.electronic_address_scheme:
            self.electronic_address_scheme = self.peppol_scheme
        return self


class Supplier(BEParty):
    """Belgian invoice supplier (seller)."""


class Customer(BEParty):
    """Belgian invoice customer (buyer)."""

    reference: str | None = Field(
        default=None,
        description="Buyer's internal reference (BT-10)",
    )
