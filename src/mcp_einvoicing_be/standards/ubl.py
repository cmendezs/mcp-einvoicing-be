"""UBL 2.1 serialization and parsing for Belgian e-invoices.

Subclasses EN16931UBLSerializer / EN16931UBLParser from mcp-einvoicing-core
(BE-CORE-1: resolves local UBL reimplementation).  A thin adapter converts
BEInvoice → EN16931Invoice before delegating to the core serializer.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from itertools import groupby
from typing import Any

from mcp_einvoicing_core.en16931 import (
    EN16931Address,
    EN16931Invoice,
    EN16931LineItem,
    EN16931Party,
    EN16931PaymentMeans,
    EN16931Tax,
)
from mcp_einvoicing_core.wire_formats import UBL_NSMAP, EN16931UBLParser, EN16931UBLSerializer

from mcp_einvoicing_be.models.invoice import BEInvoice
from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS

# Keep the legacy alias so existing importers of UBL_NAMESPACES do not break
# during the migration to BEUBLSerializer.
UBL_NAMESPACES: dict[str, str] = dict(UBL_NSMAP)


# ---------------------------------------------------------------------------
# BEInvoice → EN16931Invoice adapter
# ---------------------------------------------------------------------------


def _be_party_to_en16931(party: Any) -> EN16931Party:
    addr = party.address
    if addr is not None:
        en_addr = EN16931Address(
            line_one=addr.street,
            city=addr.city,
            postcode=addr.postal_code,
            country_code=addr.country_code,
            region=getattr(addr, "province", None),
        )
    else:
        en_addr = EN16931Address(line_one="", city="", postcode="", country_code="BE")

    tax_id = getattr(party, "tax_id", None)
    vat_id = f"{tax_id.country_code}{tax_id.identifier}" if tax_id else None

    peppol_id = getattr(party, "peppol_id", None)
    peppol_scheme = getattr(party, "peppol_scheme", None) if peppol_id else None

    return EN16931Party(
        name=party.name
        or f"{getattr(party, 'first_name', '')} {getattr(party, 'last_name', '')}".strip(),
        address=en_addr,
        vat_id=vat_id,
        electronic_address=peppol_id,
        electronic_address_scheme=peppol_scheme,
        contact_name=getattr(party, "contact_name", None),
        contact_phone=getattr(party, "contact_phone", None),
        contact_email=getattr(party, "contact_email", None),
    )


def _be_invoice_to_en16931(invoice: BEInvoice) -> EN16931Invoice:
    """Convert a BEInvoice to the EN16931Invoice expected by core serializers."""
    profile_urn = CUSTOMIZATION_IDS[invoice.profile]

    seller = _be_party_to_en16931(invoice.seller)
    buyer = _be_party_to_en16931(invoice.buyer)

    # Line items
    line_items: list[EN16931LineItem] = []
    for line in invoice.lines:
        qty = line.quantity if line.quantity is not None else Decimal("1")
        line_net = (
            line.total_price
            if line.total_price != Decimal("0")
            else (qty * line.unit_price).quantize(Decimal("0.01"))
        )
        line_items.append(
            EN16931LineItem(
                line_id=str(line.line_number),
                name=line.description,
                description=None,
                quantity=qty,
                unit_code=line.unit_code,
                unit_price=line.unit_price,
                line_net_amount=line_net,
                tax_category=line.vat_category.value,
                tax_rate=line.vat_rate,
            )
        )

    # VAT breakdown (group by category + rate, ROUND_HALF_EVEN per EN 16931 §7.4)
    sorted_lines = sorted(invoice.lines, key=lambda ln: (ln.vat_category.value, float(ln.vat_rate)))
    tax_lines: list[EN16931Tax] = []
    for (cat, rate), group_iter in groupby(
        sorted_lines, key=lambda ln: (ln.vat_category.value, ln.vat_rate)
    ):
        group = list(group_iter)
        taxable = sum(
            (
                ln.total_price
                if ln.total_price != Decimal("0")
                else (ln.quantity or Decimal("1")) * ln.unit_price
            )
            for ln in group
        ).quantize(Decimal("0.01"))
        tax_amt = (taxable * Decimal(str(rate)) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        tax_lines.append(
            EN16931Tax(
                category=cat,
                rate=Decimal(str(rate)),
                taxable_amount=taxable,
                tax_amount=tax_amt,
            )
        )

    # Document totals
    sum_lines = sum(li.line_net_amount for li in line_items).quantize(Decimal("0.01"))
    tax_total = sum(tl.tax_amount for tl in tax_lines).quantize(Decimal("0.01"))
    tax_incl = (sum_lines + tax_total).quantize(Decimal("0.01"))

    # Payment
    payment_means: EN16931PaymentMeans | None = None
    due_date: date | None = None
    terms = invoice.payment
    if terms is not None:
        due_date = date.fromisoformat(terms.due_date) if terms.due_date else None
        payment_means = EN16931PaymentMeans(
            type_code=invoice.payment_means_code,
            iban=terms.iban,
            bic=terms.bic,
            payment_id=terms.ogm_reference,
        )
    elif invoice.payment_means_code:
        payment_means = EN16931PaymentMeans(type_code=invoice.payment_means_code)

    invoice_date = (
        date.fromisoformat(invoice.date) if isinstance(invoice.date, str) else invoice.date
    )

    return EN16931Invoice(
        profile=profile_urn,
        invoice_number=invoice.number,
        invoice_date=invoice_date,
        invoice_type_code=invoice.document_type,
        currency_code=invoice.currency,
        note=getattr(invoice, "note", None),
        purchase_order_reference=invoice.order_reference,
        contract_reference=invoice.contract_reference,
        seller=seller,
        buyer=buyer,
        line_items=line_items,
        tax_lines=tax_lines,
        sum_of_line_net_amounts=sum_lines,
        tax_exclusive_amount=sum_lines,
        tax_total=tax_total,
        tax_inclusive_amount=tax_incl,
        allowances_total=Decimal("0"),
        charges_total=Decimal("0"),
        prepaid_amount=Decimal("0"),
        rounding_amount=Decimal("0"),
        amount_due=tax_incl,
        payment_means=payment_means,
        due_date=due_date,
    )


# ---------------------------------------------------------------------------
# BE-specific subclasses
# ---------------------------------------------------------------------------


class BEUBLSerializer(EN16931UBLSerializer):
    """UBL 2.1 serializer for Belgian e-invoices (Peppol BIS 3.0 / PINT-BE).

    Converts BEInvoice to EN16931Invoice via the adapter then delegates to
    the core EN16931UBLSerializer for XML generation.
    """

    def serialize_be(self, invoice: BEInvoice) -> bytes:
        """Serialize a BEInvoice to UBL 2.1 XML bytes."""
        en_invoice = _be_invoice_to_en16931(invoice)
        return self.serialize(en_invoice)


class BEUBLParser(EN16931UBLParser):
    """UBL 2.1 parser for Belgian e-invoices.

    Parses the EN 16931 core field set from a Peppol BIS 3.0 / PINT-BE XML
    document.  Belgian national extensions (OGM reference, 0208 endpoint) are
    silently ignored at this layer; subclass and override ``_extract`` to add
    extraction of national fields.
    """


# ---------------------------------------------------------------------------
# Backward-compatibility shim (deprecated — use BEUBLSerializer instead)
# ---------------------------------------------------------------------------


def render_ubl_invoice(
    invoice: BEInvoice,
    customization_id: str,
    profile_id: str,
    namespaces: dict[str, str],
) -> str:
    """Serialize a BEInvoice to a UBL 2.1 XML string.

    Deprecated: use BEUBLSerializer().serialize_be(invoice).decode() instead.
    The customization_id and profile_id arguments are accepted for backward
    compatibility but are ignored — the profile is read from invoice.profile.
    """
    return BEUBLSerializer().serialize_be(invoice).decode("utf-8")
