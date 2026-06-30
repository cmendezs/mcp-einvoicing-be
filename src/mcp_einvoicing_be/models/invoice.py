"""Belgian invoice models — extend mcp-einvoicing-core EN16931 base types.

BE-SC-2 (resolved): BEInvoice now extends EN16931Invoice (Peppol BIS 3.0 is a
CIUS of EN 16931-1:2017).  Backward-compatible Belgian field-name aliases
(number, date, currency, document_type) are provided via AliasChoices.

BE-TL-2 (resolved): VatCategory now includes REDUCED_12 = "AA" (12% rate)
and REDUCED_6 = "AB" (6% rate) per UNCL5305.

Rounding: ROUND_HALF_EVEN on document-total VAT per EN 16931-1:2017 §7.4
and Art. 4 of the Royal Decree of 8 July 2025 amending RD no. 8.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from typing import Any, Literal

from mcp_einvoicing_core import (
    DocumentValidationResult,
    InvoiceLineItem,
)
from mcp_einvoicing_core.en16931 import (
    EN16931Invoice,
    EN16931PaymentMeans,
)
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from mcp_einvoicing_be.models.party import Customer, Supplier
from mcp_einvoicing_be.utils.helpers import validate_belgian_ogm


class VatCategory(StrEnum):
    """UNCL5305 VAT category codes used in Belgian Peppol BIS 3.0 invoices.

    BE-TL-2: REDUCED_12 ("AA") and REDUCED_6 ("AB") added per the Belgian
    intermediate (12%) and reduced (6%) VAT rate tiers.
    """

    STANDARD = "S"
    REDUCED_12 = "AA"  # 12% intermediate rate — margarine, restaurant, construction
    REDUCED_6 = "AB"  # 6% reduced rate — food, medicines, books, social housing
    ZERO_RATED = "Z"
    EXEMPT = "E"
    INTRA_COMMUNITY = "K"
    NOT_SUBJECT = "O"
    REVERSE_CHARGE = "AE"


class BEInvoiceLine(InvoiceLineItem):
    """Belgian invoice line.

    Extends ``InvoiceLineItem`` with the EN 16931 VAT category code (UNCL5305)
    and the UN/ECE unit of measure (BT-130), both mandatory for Belgian Peppol
    profiles.  Auto-computes ``total_price`` from ``quantity * unit_price``
    when omitted.
    """

    line_number: int = Field(default=1, ge=1, le=9999)
    total_price: Decimal = Field(default=Decimal("0"))
    vat_category: VatCategory = Field(default=VatCategory.STANDARD)
    unit_code: str = Field(default="C62", description="UN/ECE Unit of Measure code (BT-130)")
    buyer_article_id: str | None = Field(
        default=None,
        description="Buyer's item identifier (BT-156)",
        validation_alias=AliasChoices("buyer_article_id", "buyer_item_id"),
    )

    @model_validator(mode="after")
    def compute_total_price(self) -> BEInvoiceLine:
        if self.total_price == Decimal("0") and self.quantity and self.unit_price:
            self.total_price = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        return self


class BEPaymentTerms(BaseModel):
    """Belgian payment terms.

    Covers the OGM/VCS structured payment reference and IBAN/BIC for credit
    transfers.  Does not extend the core ``PaymentTerms`` model due to the
    Belgian-specific OGM modulo-97 structure.
    """

    ogm_reference: str | None = Field(
        default=None,
        description="Belgian structured payment reference (OGM/VCS), e.g. +++000/0000/00097+++",
    )
    iban: str | None = Field(default=None, description="Creditor IBAN (BT-84)")
    bic: str | None = Field(default=None, description="Creditor BIC/SWIFT (BT-86)")
    due_date: str | None = Field(default=None, description="Payment due date (YYYY-MM-DD)")

    @field_validator("ogm_reference", mode="before")
    @classmethod
    def _validate_ogm(cls, v: object) -> object:
        if v is None or v == "":
            return v
        if isinstance(v, str):
            return validate_belgian_ogm(v)
        return v


class BEInvoice(EN16931Invoice):
    """Belgian e-invoice.

    Extends ``EN16931Invoice`` (Peppol BIS 3.0 is a CIUS of EN 16931-1:2017).
    Provides a Belgian-friendly input API (short field-name aliases, BEInvoiceLine,
    BEPaymentTerms) and auto-derives all EN 16931 mandatory totals and VAT
    breakdown from the Belgian lines via a before-validator, so that parent-class
    validators (_require_tax_lines, etc.) are transparently satisfied.

    Legal basis:
    - Art. 13ter, RD no. 1 (inserted by RD of 8 July 2025): Peppol BIS 3.0 UBL
      is the mandatory base format.
    - Art. 4, RD no. 8 (amended by RD of 8 July 2025): per-line VAT rounding is
      prohibited; ROUND_HALF_EVEN applies to the document-total VAT amount only.
    """

    model_config = ConfigDict(populate_by_name=True)

    # ── Header — narrow types and provide backward-compatible aliases ─────────

    profile: Literal["peppol-bis-3", "pint-eu"] = Field(
        "peppol-bis-3",
        description=(
            "Belgian Peppol profile: 'peppol-bis-3' (mandatory base, Art. 13ter al. 1) "
            "or 'pint-eu' (EU PINT v1.0.1, optional under Art. 13ter subsidiary rule)."
        ),
    )
    invoice_number: str = Field(
        ...,
        description="Invoice number (BT-1)",
        validation_alias=AliasChoices("invoice_number", "number"),
    )
    invoice_date: date = Field(
        ...,
        description="Invoice issue date (BT-2)",
        validation_alias=AliasChoices("invoice_date", "date"),
    )
    invoice_type_code: Literal["380", "381", "383"] = Field(
        "380",
        description="UNTDID 1001 code: 380=Invoice, 381=Credit note, 383=Debit note",
        validation_alias=AliasChoices("invoice_type_code", "document_type"),
    )
    currency_code: str = Field(
        "EUR",
        description="Invoice currency code (BT-5) — Belgium mandates EUR",
        validation_alias=AliasChoices("currency_code", "currency"),
    )

    # ── Parties — narrow to Belgian party types ───────────────────────────────

    seller: Supplier = Field(..., description="Seller / supplier (BG-4)")
    buyer: Customer = Field(..., description="Buyer / customer (BG-7)")

    # ── Belgian invoice lines (user-facing) ──────────────────────────────────

    lines: list[BEInvoiceLine] = Field(
        ...,
        min_length=1,
        description=(
            "Invoice lines in Belgian format.  EN 16931 ``line_items`` and ``tax_lines`` "
            "are automatically derived from these by the before-validator."
        ),
    )

    # ── EN 16931 computed totals — overridden with defaults so the before-
    # validator can inject them before parent validators (_require_tax_lines)
    # fire.  The defaults are replaced by the before-validator in all normal
    # construction paths.  ─────────────────────────────────────────────────────

    sum_of_line_net_amounts: Decimal = Field(
        default=Decimal("0"),
        description="Sum of line net amounts (BT-106) — auto-computed from lines",
    )
    tax_exclusive_amount: Decimal = Field(
        default=Decimal("0"),
        description="Invoice total without VAT (BT-109) — auto-computed",
    )
    tax_total: Decimal = Field(
        default=Decimal("0"),
        description="Total VAT amount (BT-110) — auto-computed",
    )
    tax_inclusive_amount: Decimal = Field(
        default=Decimal("0"),
        description="Invoice total with VAT (BT-112) — auto-computed",
    )
    amount_due: Decimal = Field(
        default=Decimal("0"),
        description="Amount due for payment (BT-115) — auto-computed",
    )

    # ── Optional header references — accept Belgian short-name alias ──────────

    purchase_order_reference: str | None = Field(
        default=None,
        description="Purchase order reference (BT-13)",
        validation_alias=AliasChoices("purchase_order_reference", "order_reference"),
    )

    # ── Belgian payment fields ────────────────────────────────────────────────

    payment: BEPaymentTerms | None = Field(default=None)
    payment_means_code: str = Field(
        default="30",
        description="UNTDID 4461 payment means code (30 = credit transfer)",
    )

    # ── Validators ───────────────────────────────────────────────────────────

    @field_validator("currency_code", mode="before")
    @classmethod
    def uppercase_currency(cls, v: object) -> object:
        return v.upper() if isinstance(v, str) else v

    @model_validator(mode="before")
    @classmethod
    def _derive_en16931_fields(cls, data: Any) -> Any:
        """Compute EN 16931 totals and VAT breakdown from Belgian invoice lines.

        Runs before Pydantic field validation so that parent-class validators
        (EN16931Invoice._require_tax_lines, etc.) see fully populated fields.

        Rounding rule: ROUND_HALF_EVEN on the document-total VAT amount per
        EN 16931-1:2017 §7.4 and Art. 4 of the Royal Decree of 8 July 2025
        amending RD no. 8 (published MB/BS N. 157, 14 July 2025).
        Per-line rounding is explicitly prohibited for Peppol BIS 3.0 UBL invoices.
        """
        if not isinstance(data, dict):
            return data

        raw_lines: list[Any] = data.get("lines") or data.get("line_items", [])
        if not raw_lines:
            return data  # let min_length=1 on lines report the error

        # Normalise each entry to a plain dict
        normalized: list[dict[str, Any]] = []
        for ln in raw_lines:
            if hasattr(ln, "model_dump"):
                normalized.append(ln.model_dump())
            elif isinstance(ln, dict):
                normalized.append(ln)
            else:
                normalized.append(dict(vars(ln)))

        # Build EN16931LineItem dicts and accumulate per-(category, rate) taxable amounts
        line_items: list[dict[str, Any]] = []
        tax_groups: dict[tuple[str, str], Decimal] = defaultdict(Decimal)

        for idx, ln in enumerate(normalized, 1):
            qty = Decimal(str(ln.get("quantity") or 1))
            price = Decimal(str(ln.get("unit_price", 0)))
            raw_total = ln.get("total_price")
            line_net = (
                Decimal(str(raw_total)).quantize(Decimal("0.01"))
                if raw_total and Decimal(str(raw_total)) != Decimal("0")
                else (qty * price).quantize(Decimal("0.01"))
            )
            # vat_category may be a VatCategory enum (StrEnum) or a plain string
            vat_cat = str(ln.get("vat_category") or "S")
            vat_rate = Decimal(str(ln.get("vat_rate", 21)))

            line_item: dict[str, Any] = {
                "line_id": str(ln.get("line_number", idx)),
                "name": ln.get("description", ""),
                "description": None,
                "quantity": qty,
                "unit_code": ln.get("unit_code", "C62"),
                "unit_price": price,
                "line_net_amount": line_net,
                "tax_category": vat_cat,
                "tax_rate": vat_rate,
            }
            if ln.get("buyer_article_id") or ln.get("buyer_item_id"):
                line_item["buyer_article_id"] = ln.get("buyer_article_id") or ln.get(
                    "buyer_item_id"
                )
            line_items.append(line_item)
            tax_groups[(vat_cat, str(vat_rate))] += line_net

        # VAT breakdown — ROUND_HALF_EVEN on the document total per EN 16931 §7.4
        tax_lines: list[dict[str, Any]] = []
        for (cat, rate_str), taxable in tax_groups.items():
            rate = Decimal(rate_str)
            taxable_q = taxable.quantize(Decimal("0.01"))
            tax_amt = (taxable_q * rate / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )
            tax_lines.append(
                {
                    "category": cat,
                    "rate": rate,
                    "taxable_amount": taxable_q,
                    "tax_amount": tax_amt,
                }
            )

        # Document totals
        sum_lines = sum(li["line_net_amount"] for li in line_items).quantize(Decimal("0.01"))
        tax_total_val = sum(tl["tax_amount"] for tl in tax_lines).quantize(Decimal("0.01"))
        tax_incl = (sum_lines + tax_total_val).quantize(Decimal("0.01"))

        data = dict(data)
        data.setdefault("line_items", line_items)
        data.setdefault("tax_lines", tax_lines)
        data.setdefault("sum_of_line_net_amounts", sum_lines)
        data.setdefault("tax_exclusive_amount", sum_lines)
        data.setdefault("tax_total", tax_total_val)
        data.setdefault("tax_inclusive_amount", tax_incl)
        data.setdefault("amount_due", tax_incl)
        return data

    @model_validator(mode="after")
    def _populate_payment_means(self) -> BEInvoice:
        """Build ``EN16931PaymentMeans`` from Belgian payment fields when not already set."""
        if self.payment_means is not None:
            return self
        terms = self.payment
        self.payment_means = EN16931PaymentMeans(
            type_code=self.payment_means_code,
            iban=terms.iban if terms else None,
            bic=terms.bic if terms else None,
            payment_id=terms.ogm_reference if terms else None,
        )
        if terms and terms.due_date and self.due_date is None:
            try:
                self.due_date = date.fromisoformat(terms.due_date)
            except ValueError:
                pass
        return self


# Re-export the core validation result — no Belgium-specific fields needed.
ValidationResult = DocumentValidationResult
