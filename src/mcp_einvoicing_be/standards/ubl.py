"""UBL 2.1 namespace constants and XML serialization for Belgian e-invoices."""

from __future__ import annotations

from itertools import groupby
from typing import Any
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

from mcp_einvoicing_core import format_amount, format_quantity

from mcp_einvoicing_be.models.invoice import BEInvoice

UBL_NAMESPACES: dict[str, str] = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

_UBL_INVOICE_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
_CBC = UBL_NAMESPACES["cbc"]
_CAC = UBL_NAMESPACES["cac"]

for _prefix, _uri in UBL_NAMESPACES.items():
    register_namespace(_prefix, _uri)
register_namespace("", _UBL_INVOICE_NS)


def _q(ns: str, local: str) -> str:
    return f"{{{ns}}}{local}"


def _el(parent: Element, tag: str, text: str) -> Element:
    child = SubElement(parent, tag)
    child.text = text
    return child


def _el_opt(parent: Element, tag: str, text: str | None) -> None:
    if text:
        child = SubElement(parent, tag)
        child.text = text


def render_ubl_invoice(
    invoice: BEInvoice,
    customization_id: str,
    profile_id: str,
    namespaces: dict[str, str],
) -> str:
    """Serialize a ``BEInvoice`` to a UBL 2.1 Invoice XML string."""
    root = Element(_q(_UBL_INVOICE_NS, "Invoice"))

    _el(root, _q(_CBC, "CustomizationID"), customization_id)
    _el(root, _q(_CBC, "ProfileID"), profile_id)
    _el(root, _q(_CBC, "ID"), invoice.number)
    _el(root, _q(_CBC, "IssueDate"), invoice.date)
    _el(root, _q(_CBC, "InvoiceTypeCode"), invoice.document_type)
    _el(root, _q(_CBC, "DocumentCurrencyCode"), invoice.currency)

    _el_opt(root, _q(_CBC, "Note"), getattr(invoice, "note", None))

    if invoice.order_reference:
        order_ref = SubElement(root, _q(_CAC, "OrderReference"))
        _el(order_ref, _q(_CBC, "ID"), invoice.order_reference)

    if invoice.contract_reference:
        contract_ref = SubElement(root, _q(_CAC, "ContractDocumentReference"))
        _el(contract_ref, _q(_CBC, "ID"), invoice.contract_reference)

    _render_party(root, "AccountingSupplierParty", invoice.seller)
    _render_party(root, "AccountingCustomerParty", invoice.buyer)

    _render_payment_means(root, invoice)

    if invoice.payment and invoice.payment.due_date:
        pt = SubElement(root, _q(_CAC, "PaymentTerms"))
        _el(pt, _q(_CBC, "Note"), f"Due: {invoice.payment.due_date}")

    _render_tax_total(root, invoice)
    _render_legal_monetary_total(root, invoice)

    for idx, line in enumerate(invoice.lines, start=1):
        line_el = SubElement(root, _q(_CAC, "InvoiceLine"))
        _el(line_el, _q(_CBC, "ID"), str(idx))
        qty_el = _el(line_el, _q(_CBC, "InvoicedQuantity"), format_quantity(line.quantity or 0))
        qty_el.set("unitCode", line.unit_code)
        ext_el = _el(
            line_el,
            _q(_CBC, "LineExtensionAmount"),
            format_amount((line.quantity or 0) * line.unit_price),
        )
        ext_el.set("currencyID", invoice.currency)
        item_el = SubElement(line_el, _q(_CAC, "Item"))
        _el(item_el, _q(_CBC, "Description"), line.description)
        _el_opt(  # noqa: E501
            item_el, _q(_CBC, "SellersItemIdentification"), getattr(line, "buyer_item_id", None)
        )
        cls_tax = SubElement(item_el, _q(_CAC, "ClassifiedTaxCategory"))
        _el(cls_tax, _q(_CBC, "ID"), line.vat_category.value)
        _el(cls_tax, _q(_CBC, "Percent"), str(line.vat_rate))
        ts = SubElement(cls_tax, _q(_CAC, "TaxScheme"))
        _el(ts, _q(_CBC, "ID"), "VAT")
        price_el = SubElement(line_el, _q(_CAC, "Price"))
        price_amt = _el(price_el, _q(_CBC, "PriceAmount"), format_amount(line.unit_price))
        price_amt.set("currencyID", invoice.currency)

    return tostring(root, encoding="unicode", xml_declaration=False)


def _render_party(root: Element, wrapper_tag: str, party: Any) -> None:
    wrapper = SubElement(root, _q(_CAC, wrapper_tag))
    party_el = SubElement(wrapper, _q(_CAC, "Party"))

    peppol_id = getattr(party, "peppol_id", None)
    if peppol_id:
        ep = _el(party_el, _q(_CBC, "EndpointID"), peppol_id)
        ep.set("schemeID", getattr(party, "peppol_scheme", "0208"))

    tax_id = getattr(party, "tax_id", None)
    vat = f"{tax_id.country_code}{tax_id.identifier}" if tax_id else None
    if vat:
        pts = SubElement(party_el, _q(_CAC, "PartyTaxScheme"))
        _el(pts, _q(_CBC, "CompanyID"), vat)
        ts = SubElement(pts, _q(_CAC, "TaxScheme"))
        _el(ts, _q(_CBC, "ID"), "VAT")

    legal = SubElement(party_el, _q(_CAC, "PartyLegalEntity"))
    _el(legal, _q(_CBC, "RegistrationName"), party.name)

    addr = party.address
    address_el = SubElement(party_el, _q(_CAC, "PostalAddress"))
    _el(address_el, _q(_CBC, "StreetName"), addr.street)
    _el_opt(address_el, _q(_CBC, "AdditionalStreetName"), getattr(addr, "additional_street", None))
    _el(address_el, _q(_CBC, "CityName"), addr.city)
    _el(address_el, _q(_CBC, "PostalZone"), addr.postal_code)
    country_el = SubElement(address_el, _q(_CAC, "Country"))
    _el(country_el, _q(_CBC, "IdentificationCode"), addr.country_code)


def _render_payment_means(root: Element, invoice: BEInvoice) -> None:
    pm = SubElement(root, _q(_CAC, "PaymentMeans"))
    _el(pm, _q(_CBC, "PaymentMeansCode"), invoice.payment_means_code)

    terms = invoice.payment
    if terms:
        _el_opt(pm, _q(_CBC, "PaymentID"), terms.ogm_reference)
        if terms.iban:
            payee = SubElement(pm, _q(_CAC, "PayeeFinancialAccount"))
            _el(payee, _q(_CBC, "ID"), terms.iban)
            if terms.bic:
                fi = SubElement(payee, _q(_CAC, "FinancialInstitutionBranch"))
                _el(fi, _q(_CBC, "ID"), terms.bic)


def _render_tax_total(root: Element, invoice: BEInvoice) -> None:
    tax_total_el = SubElement(root, _q(_CAC, "TaxTotal"))
    total_vat = sum(
        round((ln.quantity or 0) * ln.unit_price * ln.vat_rate / 100, 2) for ln in invoice.lines
    )
    vat_el = _el(tax_total_el, _q(_CBC, "TaxAmount"), format_amount(total_vat))
    vat_el.set("currencyID", invoice.currency)

    sorted_lines = sorted(invoice.lines, key=lambda ln: (ln.vat_rate, ln.vat_category.value))
    for (rate, category), group_iter in groupby(
        sorted_lines, key=lambda ln: (ln.vat_rate, ln.vat_category.value)
    ):
        group = list(group_iter)
        taxable = sum(round((ln.quantity or 0) * ln.unit_price, 2) for ln in group)
        tax_amt = sum(
            round((ln.quantity or 0) * ln.unit_price * ln.vat_rate / 100, 2) for ln in group
        )
        sub = SubElement(tax_total_el, _q(_CAC, "TaxSubtotal"))
        ta = _el(sub, _q(_CBC, "TaxableAmount"), format_amount(taxable))
        ta.set("currencyID", invoice.currency)
        tv = _el(sub, _q(_CBC, "TaxAmount"), format_amount(tax_amt))
        tv.set("currencyID", invoice.currency)
        cat = SubElement(sub, _q(_CAC, "TaxCategory"))
        _el(cat, _q(_CBC, "ID"), category)
        _el(cat, _q(_CBC, "Percent"), str(rate))
        ts = SubElement(cat, _q(_CAC, "TaxScheme"))
        _el(ts, _q(_CBC, "ID"), "VAT")


def _render_legal_monetary_total(root: Element, invoice: BEInvoice) -> None:
    total_el = SubElement(root, _q(_CAC, "LegalMonetaryTotal"))
    line_ext = sum(round((ln.quantity or 0) * ln.unit_price, 2) for ln in invoice.lines)
    vat_total = sum(
        round((ln.quantity or 0) * ln.unit_price * ln.vat_rate / 100, 2) for ln in invoice.lines
    )
    payable = line_ext + vat_total

    for tag, value in [
        ("LineExtensionAmount", line_ext),
        ("TaxExclusiveAmount", line_ext),
        ("TaxInclusiveAmount", payable),
        ("PayableAmount", payable),
    ]:
        el = _el(total_el, _q(_CBC, tag), format_amount(value))
        el.set("currencyID", invoice.currency)
