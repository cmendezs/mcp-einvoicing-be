"""Belgian invoice models — extend mcp-einvoicing-core base types."""

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from mcp_einvoicing_core import (
    DocumentValidationResult,
    InvoiceDocument,
    InvoiceLineItem,
)
from pydantic import BaseModel, Field, field_validator, model_validator

from mcp_einvoicing_be.models.party import Customer, Supplier


class VatCategory(StrEnum):
    STANDARD = "S"
    ZERO_RATED = "Z"
    EXEMPT = "E"
    INTRA_COMMUNITY = "K"
    NOT_SUBJECT = "O"
    REVERSE_CHARGE = "AE"


class BEInvoiceLine(InvoiceLineItem):
    """Belgian invoice line.

    Extends ``InvoiceLineItem`` with the EN 16931 VAT category code and the
    UN/ECE unit of measure, both mandatory for Belgian Peppol profiles.
    Auto-computes ``total_price`` from ``quantity * unit_price`` when omitted.
    """

    line_number: int = Field(default=1, ge=1, le=9999)
    total_price: Decimal = Field(default=Decimal("0"))
    vat_category: VatCategory = Field(default=VatCategory.STANDARD)
    unit_code: str = Field(default="C62", description="UN/ECE Unit of Measure code (BT-130)")
    buyer_item_id: str | None = Field(default=None, description="Buyer's item identifier (BT-157)")

    @model_validator(mode="after")
    def compute_total_price(self) -> "BEInvoiceLine":
        if self.total_price == Decimal("0") and self.quantity and self.unit_price:
            self.total_price = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        return self


class BEPaymentTerms(BaseModel):
    """Belgian payment terms.

    Standalone model (does not extend core PaymentTerms due to API divergence).
    Covers the OGM/VCS structured reference and IBAN/BIC for credit transfers.
    """

    ogm_reference: str | None = Field(
        default=None,
        description="Belgian structured payment reference (OGM/VCS), e.g. +++000/0000/00097+++",
    )
    iban: str | None = Field(default=None, description="Creditor IBAN (BT-84)")
    bic: str | None = Field(default=None, description="Creditor BIC/SWIFT (BT-86)")
    due_date: str | None = Field(default=None, description="Payment due date (YYYY-MM-DD)")


class BEInvoice(InvoiceDocument):
    """Belgian e-invoice.

    Extends ``InvoiceDocument`` with Belgium-specific fields: PINT-BE profile
    selection, Belgian party types, and Belgian payment terms.
    """

    document_type: Literal["380", "381", "383"] = Field(
        default="380",
        description="UNTDID 1001 code: 380=Invoice, 381=Credit note, 383=Debit note",
    )
    profile: Literal["peppol-bis-3", "pint-be"] = Field(
        default="peppol-bis-3",
        description="Belgian Peppol profile to apply",
    )
    seller: Supplier  # type: ignore[assignment]
    buyer: Customer  # type: ignore[assignment]
    lines: list[BEInvoiceLine] = Field(..., min_length=1)  # type: ignore[assignment]
    payment: BEPaymentTerms | None = Field(default=None)  # type: ignore[assignment]
    order_reference: str | None = Field(default=None, description="Purchase order reference (BT-13)")  # noqa: E501
    contract_reference: str | None = Field(default=None, description="Contract reference (BT-12)")
    payment_means_code: str = Field(
        default="30",
        description="UNTDID 4461 payment means code (30=credit transfer)",
    )

    @field_validator("currency", check_fields=False)
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()


# Re-export the core validation result — no Belgium-specific fields needed.
ValidationResult = DocumentValidationResult
