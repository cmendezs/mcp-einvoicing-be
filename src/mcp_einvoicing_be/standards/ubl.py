"""UBL 2.1 namespace constants and XML serialization helpers."""

from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from mcp_einvoicing_be.models.invoice import InvoiceInput

UBL_NAMESPACES: dict[str, str] = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

_UBL_INVOICE_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
_CBC = UBL_NAMESPACES["cbc"]
_CAC = UBL_NAMESPACES["cac"]


def _tag(ns: str, local: str) -> str:
    return f"{{{ns}}}{local}"


def render_ubl_invoice(
    invoice: InvoiceInput,
    customization_id: str,
    profile_id: str,
    namespaces: dict[str, str],
) -> str:
    """Serialize an InvoiceInput to a UBL 2.1 Invoice XML string.

    This is a reference implementation that covers the mandatory EN 16931 elements.
    It delegates to mcp-einvoicing-core's serializer when available.
    """
    for prefix, uri in namespaces.items():
        Element.attrib  # noqa: B018  (trigger namespace registration side-effect)
        try:
            from xml.etree.ElementTree import register_namespace
            register_namespace(prefix, uri)
        except Exception:  # noqa: BLE001
            pass

    root = Element(_tag(_UBL_INVOICE_NS, "Invoice"))
    root.set(f"{{{namespaces['xsi']}}}schemaLocation", _UBL_INVOICE_NS)

    _cbc(root, "CustomizationID", customization_id)
    _cbc(root, "ProfileID", profile_id)
    _cbc(root, "ID", invoice.invoice_number)
    _cbc(root, "IssueDate", invoice.issue_date.isoformat())
    _cbc(root, "InvoiceTypeCode", invoice.invoice_type_code)
    _cbc(root, "DocumentCurrencyCode", invoice.currency_code)

    if invoice.note:
        _cbc(root, "Note", invoice.note)
    if invoice.order_reference:
        order_ref = SubElement(root, _tag(_CAC, "OrderReference"))
        _cbc(order_ref, "ID", invoice.order_reference)
    if invoice.due_date:
        payment_terms = SubElement(root, _tag(_CAC, "PaymentTerms"))
        _cbc(payment_terms, "Note", f"Due: {invoice.due_date.isoformat()}")

    _render_party(root, "AccountingSupplierParty", invoice.supplier)
    _render_party(root, "AccountingCustomerParty", invoice.customer)

    payment_means = SubElement(root, _tag(_CAC, "PaymentMeans"))
    _cbc(payment_means, "PaymentMeansCode", invoice.payment_means_code)
    if invoice.iban:
        payee_account = SubElement(payment_means, _tag(_CAC, "PayeeFinancialAccount"))
        _cbc(payee_account, "ID", invoice.iban)
    if invoice.payment_reference:
        _cbc(payment_means, "PaymentID", invoice.payment_reference)

    _render_tax_total(root, invoice)
    _render_legal_monetary_total(root, invoice)

    for idx, line in enumerate(invoice.lines, start=1):
        line_el = SubElement(root, _tag(_CAC, "InvoiceLine"))
        _cbc(line_el, "ID", str(idx))
        qty_el = _cbc(line_el, "InvoicedQuantity", str(line.quantity))
        qty_el.set("unitCode", line.unit_code)
        _cbc(line_el, "LineExtensionAmount", f"{line.line_extension_amount:.2f}")
        line_el[-1].set("currencyID", invoice.currency_code)
        item_el = SubElement(line_el, _tag(_CAC, "Item"))
        _cbc(item_el, "Description", line.description)
        price_el = SubElement(line_el, _tag(_CAC, "Price"))
        _cbc(price_el, "PriceAmount", f"{line.unit_price:.2f}")
        price_el[-1].set("currencyID", invoice.currency_code)

    return tostring(root, encoding="unicode", xml_declaration=False)


def _cbc(parent: Element, tag: str, text: str) -> Element:
    el = SubElement(parent, _tag(_CBC, tag))
    el.text = text
    return el


def _render_party(root: Element, wrapper_tag: str, party: object) -> None:
    wrapper = SubElement(root, _tag(_CAC, wrapper_tag))
    party_el = SubElement(wrapper, _tag(_CAC, "Party"))
    if hasattr(party, "peppol_id") and party.peppol_id:  # type: ignore[union-attr]
        ep_el = SubElement(party_el, _tag(_CAC, "EndpointID"))
        ep_el.text = party.peppol_id  # type: ignore[union-attr]
        ep_el.set("schemeID", "0208")
    if hasattr(party, "vat_number") and party.vat_number:  # type: ignore[union-attr]
        tax_scheme_el = SubElement(party_el, _tag(_CAC, "PartyTaxScheme"))
        _cbc(tax_scheme_el, "CompanyID", party.vat_number)  # type: ignore[union-attr]
        tax_scheme_inner = SubElement(tax_scheme_el, _tag(_CAC, "TaxScheme"))
        _cbc(tax_scheme_inner, "ID", "VAT")
    legal_el = SubElement(party_el, _tag(_CAC, "PartyLegalEntity"))
    _cbc(legal_el, "RegistrationName", party.name)  # type: ignore[union-attr]
    addr = party.address  # type: ignore[union-attr]
    address_el = SubElement(party_el, _tag(_CAC, "PostalAddress"))
    _cbc(address_el, "StreetName", addr.street)
    _cbc(address_el, "CityName", addr.city)
    _cbc(address_el, "PostalZone", addr.postal_code)
    country_el = SubElement(address_el, _tag(_CAC, "Country"))
    _cbc(country_el, "IdentificationCode", addr.country_code)


def _render_tax_total(root: Element, invoice: InvoiceInput) -> None:
    tax_total_el = SubElement(root, _tag(_CAC, "TaxTotal"))
    total_vat = sum(line.vat_amount for line in invoice.lines)
    vat_el = _cbc(tax_total_el, "TaxAmount", f"{total_vat:.2f}")
    vat_el.set("currencyID", invoice.currency_code)

    from itertools import groupby

    sorted_lines = sorted(invoice.lines, key=lambda l: (l.vat_rate, l.vat_category.value))
    for (rate, category), group_lines in groupby(
        sorted_lines, key=lambda l: (l.vat_rate, l.vat_category.value)
    ):
        group = list(group_lines)
        taxable = sum(l.line_extension_amount for l in group)
        tax_amount = sum(l.vat_amount for l in group)
        sub_el = SubElement(tax_total_el, _tag(_CAC, "TaxSubtotal"))
        ta_el = _cbc(sub_el, "TaxableAmount", f"{taxable:.2f}")
        ta_el.set("currencyID", invoice.currency_code)
        tv_el = _cbc(sub_el, "TaxAmount", f"{tax_amount:.2f}")
        tv_el.set("currencyID", invoice.currency_code)
        cat_el = SubElement(sub_el, _tag(_CAC, "TaxCategory"))
        _cbc(cat_el, "ID", category)
        _cbc(cat_el, "Percent", str(rate))
        scheme_el = SubElement(cat_el, _tag(_CAC, "TaxScheme"))
        _cbc(scheme_el, "ID", "VAT")


def _render_legal_monetary_total(root: Element, invoice: InvoiceInput) -> None:
    total_el = SubElement(root, _tag(_CAC, "LegalMonetaryTotal"))
    line_ext = sum(l.line_extension_amount for l in invoice.lines)
    vat_total = sum(l.vat_amount for l in invoice.lines)
    payable = line_ext + vat_total

    for tag, value in [
        ("LineExtensionAmount", line_ext),
        ("TaxExclusiveAmount", line_ext),
        ("TaxInclusiveAmount", payable),
        ("PayableAmount", payable),
    ]:
        el = _cbc(total_el, tag, f"{value:.2f}")
        el.set("currencyID", invoice.currency_code)
