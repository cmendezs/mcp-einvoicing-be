"""UBL 2.1 namespace constants and XML serialization for Belgian e-invoices.

Uses ``xml_element()``, ``xml_optional()``, ``format_amount()``, and
``format_quantity()`` from mcp-einvoicing-core to avoid duplicating generic
XML and formatting utilities.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

from mcp_einvoicing_core import format_amount, format_quantity, xml_element, xml_optional

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


def render_ubl_invoice(
    invoice: BEInvoice,
    customization_id: str,
    profile_id: str,
    namespaces: dict[str, str],
) -> str:
    """Serialize a ``BEInvoice`` to a UBL 2.1 Invoice XML string.

    Uses the core ``xml_element()`` / ``xml_optional()`` helpers for element
    construction and ``format_amount()`` / ``format_quantity()`` for numeric
    formatting, so the serializer stays aligned with core conventions.
    """
    root = Element(_q(_UBL_INVOICE_NS, "Invoice"))

    xml_element(root, _q(_CBC, "CustomizationID"), customization_id)
    xml_element(root, _q(_CBC, "ProfileID"), profile_id)
    xml_element(root, _q(_CBC, "ID"), invoice.invoice_number)
    xml_element(root, _q(_CBC, "IssueDate"), invoice.issue_date.isoformat())
    xml_element(root, _q(_CBC, "InvoiceTypeCode"), invoice.invoice_type_code)
    xml_element(root, _q(_CBC, "DocumentCurrencyCode"), invoice.currency_code)

    xml_optional(root, _q(_CBC, "Note"), getattr(invoice, "note", None))

    if invoice.order_reference:
        order_ref = SubElement(root, _q(_CAC, "OrderReference"))
        xml_element(order_ref, _q(_CBC, "ID"), invoice.order_reference)

    if invoice.contract_reference:
        contract_ref = SubElement(root, _q(_CAC, "ContractDocumentReference"))
        xml_element(contract_ref, _q(_CBC, "ID"), invoice.contract_reference)

    _render_party(root, "AccountingSupplierParty", invoice.supplier)
    _render_party(root, "AccountingCustomerParty", invoice.customer)

    _render_payment_means(root, invoice)

    if invoice.payment_terms and invoice.payment_terms.due_date:
        pt = SubElement(root, _q(_CAC, "PaymentTerms"))
        xml_element(pt, _q(_CBC, "Note"), f"Due: {invoice.payment_terms.due_date.isoformat()}")

    _render_tax_total(root, invoice)
    _render_legal_monetary_total(root, invoice)

    for idx, line in enumerate(invoice.lines, start=1):
        line_el = SubElement(root, _q(_CAC, "InvoiceLine"))
        xml_element(line_el, _q(_CBC, "ID"), str(idx))
        qty_el = xml_element(line_el, _q(_CBC, "InvoicedQuantity"), format_quantity(line.quantity))
        qty_el.set("unitCode", line.unit_code)
        ext_el = xml_element(
            line_el,
            _q(_CBC, "LineExtensionAmount"),
            format_amount(line.quantity * line.unit_price),
        )
        ext_el.set("currencyID", invoice.currency_code)
        item_el = SubElement(line_el, _q(_CAC, "Item"))
        xml_element(item_el, _q(_CBC, "Description"), line.description)
        xml_optional(item_el, _q(_CBC, "SellersItemIdentification"), getattr(line, "item_id", None))
        cls_tax = SubElement(item_el, _q(_CAC, "ClassifiedTaxCategory"))
        xml_element(cls_tax, _q(_CBC, "ID"), line.vat_category.value)
        xml_element(cls_tax, _q(_CBC, "Percent"), str(line.vat_rate))
        ts = SubElement(cls_tax, _q(_CAC, "TaxScheme"))
        xml_element(ts, _q(_CBC, "ID"), "VAT")
        price_el = SubElement(line_el, _q(_CAC, "Price"))
        price_amt = xml_element(price_el, _q(_CBC, "PriceAmount"), format_amount(line.unit_price))
        price_amt.set("currencyID", invoice.currency_code)

    return tostring(root, encoding="unicode", xml_declaration=False)


def _render_party(root: Element, wrapper_tag: str, party: object) -> None:
    wrapper = SubElement(root, _q(_CAC, wrapper_tag))
    party_el = SubElement(wrapper, _q(_CAC, "Party"))

    peppol_id = getattr(party, "peppol_id", None)
    if peppol_id:
        ep = xml_element(party_el, _q(_CBC, "EndpointID"), peppol_id)
        ep.set("schemeID", getattr(party, "peppol_scheme", "0208"))

    vat = getattr(party, "tax_id", None) or getattr(party, "vat_number", None)
    if vat:
        pts = SubElement(party_el, _q(_CAC, "PartyTaxScheme"))
        xml_element(pts, _q(_CBC, "CompanyID"), vat)
        ts = SubElement(pts, _q(_CAC, "TaxScheme"))
        xml_element(ts, _q(_CBC, "ID"), "VAT")

    legal = SubElement(party_el, _q(_CAC, "PartyLegalEntity"))
    xml_element(legal, _q(_CBC, "RegistrationName"), party.name)  # type: ignore[union-attr]

    addr = party.address  # type: ignore[union-attr]
    address_el = SubElement(party_el, _q(_CAC, "PostalAddress"))
    xml_element(address_el, _q(_CBC, "StreetName"), addr.street)
    xml_optional(address_el, _q(_CBC, "AdditionalStreetName"), getattr(addr, "additional_street", None))
    xml_element(address_el, _q(_CBC, "CityName"), addr.city)
    xml_element(address_el, _q(_CBC, "PostalZone"), addr.postal_code)
    country_el = SubElement(address_el, _q(_CAC, "Country"))
    xml_element(country_el, _q(_CBC, "IdentificationCode"), addr.country_code)


def _render_payment_means(root: Element, invoice: BEInvoice) -> None:
    pm = SubElement(root, _q(_CAC, "PaymentMeans"))
    xml_element(pm, _q(_CBC, "PaymentMeansCode"), invoice.payment_means_code)

    terms = invoice.payment_terms
    if terms:
        xml_optional(pm, _q(_CBC, "PaymentID"), getattr(terms, "ogm_reference", None))
        if getattr(terms, "iban", None):
            payee = SubElement(pm, _q(_CAC, "PayeeFinancialAccount"))
            xml_element(payee, _q(_CBC, "ID"), terms.iban)  # type: ignore[arg-type]
            if getattr(terms, "bic", None):
                fi = SubElement(payee, _q(_CAC, "FinancialInstitutionBranch"))
                xml_element(fi, _q(_CBC, "ID"), terms.bic)  # type: ignore[arg-type]


def _render_tax_total(root: Element, invoice: BEInvoice) -> None:
    from itertools import groupby

    tax_total_el = SubElement(root, _q(_CAC, "TaxTotal"))
    total_vat = sum(
        round(l.quantity * l.unit_price * l.vat_rate / 100, 2) for l in invoice.lines
    )
    vat_el = xml_element(tax_total_el, _q(_CBC, "TaxAmount"), format_amount(total_vat))
    vat_el.set("currencyID", invoice.currency_code)

    sorted_lines = sorted(invoice.lines, key=lambda l: (l.vat_rate, l.vat_category.value))
    for (rate, category), group_iter in groupby(
        sorted_lines, key=lambda l: (l.vat_rate, l.vat_category.value)
    ):
        group = list(group_iter)
        taxable = sum(round(l.quantity * l.unit_price, 2) for l in group)
        tax_amt = sum(round(l.quantity * l.unit_price * l.vat_rate / 100, 2) for l in group)
        sub = SubElement(tax_total_el, _q(_CAC, "TaxSubtotal"))
        ta = xml_element(sub, _q(_CBC, "TaxableAmount"), format_amount(taxable))
        ta.set("currencyID", invoice.currency_code)
        tv = xml_element(sub, _q(_CBC, "TaxAmount"), format_amount(tax_amt))
        tv.set("currencyID", invoice.currency_code)
        cat = SubElement(sub, _q(_CAC, "TaxCategory"))
        xml_element(cat, _q(_CBC, "ID"), category)
        xml_element(cat, _q(_CBC, "Percent"), str(rate))
        ts = SubElement(cat, _q(_CAC, "TaxScheme"))
        xml_element(ts, _q(_CBC, "ID"), "VAT")


def _render_legal_monetary_total(root: Element, invoice: BEInvoice) -> None:
    total_el = SubElement(root, _q(_CAC, "LegalMonetaryTotal"))
    line_ext = sum(round(l.quantity * l.unit_price, 2) for l in invoice.lines)
    vat_total = sum(round(l.quantity * l.unit_price * l.vat_rate / 100, 2) for l in invoice.lines)
    payable = line_ext + vat_total

    for tag, value in [
        ("LineExtensionAmount", line_ext),
        ("TaxExclusiveAmount", line_ext),
        ("TaxInclusiveAmount", payable),
        ("PayableAmount", payable),
    ]:
        el = xml_element(total_el, _q(_CBC, tag), format_amount(value))
        el.set("currencyID", invoice.currency_code)
