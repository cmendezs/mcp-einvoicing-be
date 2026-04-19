"""Belgian invoice models — extend mcp-einvoicing-core base types."""

from enum import Enum
from typing import Literal

from pydantic import Field, field_validator
from mcp_einvoicing_core import (
    DocumentValidationResult,
    InvoiceDocument,
    InvoiceLineItem,
    PaymentTerms,
)

from mcp_einvoicing_be.models.party import Customer, Supplier


class VatCategory(str, Enum):
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
    """

    vat_category: VatCategory = Field(default=VatCategory.STANDARD)
    unit_code: str = Field(default="C62", description="UN/ECE Unit of Measure code (BT-130)")
    buyer_item_id: str | None = Field(default=None, description="Buyer's item identifier (BT-157)")


class BEPaymentTerms(PaymentTerms):
    """Belgian payment terms.

    Adds the Belgian OGM/VCS structured payment reference (+++format+++)
    on top of the core ``PaymentTerms``.
    """

    ogm_reference: str | None = Field(
        default=None,
        description="Belgian structured payment reference (OGM/VCS), e.g. +++000/0000/00097+++",
    )
    iban: str | None = Field(default=None, description="Creditor IBAN (BT-84)")
    bic: str | None = Field(default=None, description="Creditor BIC/SWIFT (BT-86)")


class BEInvoice(InvoiceDocument):
    """Belgian e-invoice.

    Extends ``InvoiceDocument`` with Belgium-specific fields: PINT-BE profile
    selection, Belgian party types, and Belgian payment terms.
    """

    invoice_type_code: Literal["380", "381", "383"] = Field(
        default="380",
        description="UNTDID 1001 code: 380=Invoice, 381=Credit note, 383=Debit note",
    )
    profile: Literal["peppol-bis-3", "pint-be"] = Field(
        default="peppol-bis-3",
        description="Belgian Peppol profile to apply",
    )
    supplier: Supplier  # type: ignore[assignment]  # narrows InvoiceDocument.supplier
    customer: Customer  # type: ignore[assignment]  # narrows InvoiceDocument.customer
    lines: list[BEInvoiceLine] = Field(..., min_length=1)  # type: ignore[assignment]
    payment_terms: BEPaymentTerms | None = Field(default=None)
    order_reference: str | None = Field(default=None, description="Purchase order reference (BT-13)")
    contract_reference: str | None = Field(default=None, description="Contract reference (BT-12)")
    payment_means_code: str = Field(
        default="30",
        description="UNTDID 4461 payment means code (30=credit transfer)",
    )

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()


# Re-export the core validation result — no Belgium-specific fields needed.
ValidationResult = DocumentValidationResult
