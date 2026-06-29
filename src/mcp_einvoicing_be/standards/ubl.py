"""UBL 2.1 serialization and parsing for Belgian e-invoices.

Subclasses EN16931UBLSerializer / EN16931UBLParser from mcp-einvoicing-core.

BE-SC-2 (resolved): BEInvoice now extends EN16931Invoice, so the heavy
_be_party_to_en16931 and line-recomputation adapter have been removed.  The
only remaining transformation is resolving the short profile key ('peppol-bis-3'
/ 'pint-be') to its full CustomizationID URN (BT-24), which the core UBL
serializer emits verbatim.

BE-SH-1 (resolved): XML escaping is performed automatically by lxml inside the
EN16931UBLSerializer; no manual escaping is needed in this layer.
"""

from __future__ import annotations

from lxml import etree
from mcp_einvoicing_core.en16931 import EN16931Invoice
from mcp_einvoicing_core.wire_formats import UBL_NSMAP, EN16931UBLParser, EN16931UBLSerializer

from mcp_einvoicing_be.models.invoice import BEInvoice
from mcp_einvoicing_be.standards.peppol_bis_3 import CUSTOMIZATION_IDS

# Backward-compatibility alias — importers of UBL_NAMESPACES are not broken.
UBL_NAMESPACES: dict[str, str] = dict(UBL_NSMAP)

# BE-only fields that must be stripped before constructing a pure EN16931Invoice.
_BE_ONLY_FIELDS: frozenset[str] = frozenset({"lines", "payment", "payment_means_code"})


def _be_invoice_to_en16931(invoice: BEInvoice) -> EN16931Invoice:
    """Produce a pure EN16931Invoice with the full Peppol BIS 3.0 profile URN.

    BEInvoice is-a EN16931Invoice (BE-SC-2 resolved).  The EN 16931 mandatory
    totals and VAT breakdown are already computed and stored on the BEInvoice
    instance by its before-validator (_derive_en16931_fields).

    The two remaining transformations are:
    1.  Resolve the short profile key to the full CustomizationID URN (BT-24).
        The core UBL serializer emits profile verbatim as <cbc:CustomizationID>.
    2.  Strip Belgian-only fields (lines, payment, payment_means_code) that are
        not part of the EN16931Invoice schema.

    The seller and buyer are BEParty(EN16931Party) subclasses.  When serialised
    to dict and re-validated as EN16931Party, the BE-only fields (tax_id,
    peppol_scheme, reference) are silently ignored by Pydantic (extra='ignore'
    is the default).
    """
    data = invoice.model_dump(by_alias=False)
    data["profile"] = CUSTOMIZATION_IDS[invoice.profile]
    for key in _BE_ONLY_FIELDS:
        data.pop(key, None)
    return EN16931Invoice.model_validate(data)


# ---------------------------------------------------------------------------
# BE-specific serializer / parser subclasses
# ---------------------------------------------------------------------------


class BEUBLSerializer(EN16931UBLSerializer):
    """UBL 2.1 serializer for Belgian e-invoices (Peppol BIS 3.0).

    Converts a BEInvoice to a pure EN16931Invoice (profile URN resolved,
    BE-only fields stripped) then delegates to the core EN16931UBLSerializer
    for XML generation.  lxml handles all XML escaping automatically.
    """

    def serialize_be(self, invoice: BEInvoice) -> bytes:
        """Serialize a BEInvoice to UBL 2.1 XML bytes (with XML declaration)."""
        return self.serialize(_be_invoice_to_en16931(invoice))

    def serialize_be_str(self, invoice: BEInvoice) -> str:
        """Serialize a BEInvoice to a UBL 2.1 XML string (no XML declaration).

        Use this method when the result will be embedded in a JSON API response
        or parsed by xml.etree.ElementTree.fromstring(), which does not accept
        an encoding declaration in a Unicode string input (Python 3.11-3.13).
        """
        root = self._build_root(_be_invoice_to_en16931(invoice))
        return etree.tostring(root, encoding="unicode", pretty_print=True)


class BEUBLParser(EN16931UBLParser):
    """UBL 2.1 parser for Belgian e-invoices.

    Satisfies the mandatory reception capability required by Art. 13quater of
    Royal Decree no. 1 (inserted by the Royal Decree of 8 July 2025,
    MB/BS N. 157).  Parses the EN 16931 core field set from a Peppol BIS 3.0
    UBL 2.1 document.

    Belgian extensions extracted:
    - OGM/VCS structured payment reference from ``<cbc:PaymentID>``
    - Peppol endpoint IDs (scheme 0208 = KBO/BCE) from ``<cbc:EndpointID>``
    """

    def parse_be(self, xml_bytes: bytes) -> dict[str, object]:
        """Parse a UBL invoice and return core fields plus Belgian extensions.

        Returns a dict with ``invoice`` (EN16931Invoice.model_dump) merged with
        ``be_extensions`` containing OGM reference and endpoint scheme info.
        """
        invoice = self.parse(xml_bytes)
        extensions = self._extract_be_extensions(xml_bytes)
        result = invoice.model_dump(mode="json")
        result["be_extensions"] = extensions
        return result

    def _extract_be_extensions(self, xml_bytes: bytes) -> dict[str, object]:
        """Extract Belgian-specific fields from raw UBL XML."""
        from lxml import etree  # noqa: PLC0415

        root = etree.fromstring(xml_bytes)
        ns = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        }

        extensions: dict[str, object] = {}

        payment_id_el = root.find(".//cac:PaymentMeans/cbc:PaymentID", ns)
        if payment_id_el is not None and payment_id_el.text:
            raw = payment_id_el.text.strip()
            extensions["ogm_reference"] = raw
            try:
                from mcp_einvoicing_core.routing import RoutingIdentifier  # noqa: PLC0415

                result = RoutingIdentifier.validate_be_ogm(raw)
                extensions["ogm_valid"] = result.valid
                if result.valid:
                    extensions["ogm_reference"] = result.normalized_value
            except Exception:
                extensions["ogm_valid"] = False

        for role, xpath in [
            ("seller_endpoint", ".//cac:AccountingSupplierParty/cac:Party/cbc:EndpointID"),
            ("buyer_endpoint", ".//cac:AccountingCustomerParty/cac:Party/cbc:EndpointID"),
        ]:
            ep_el = root.find(xpath, ns)
            if ep_el is not None:
                extensions[role] = {
                    "scheme": ep_el.get("schemeID", ""),
                    "value": ep_el.text.strip() if ep_el.text else "",
                }

        return extensions


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

    Deprecated: use ``BEUBLSerializer().serialize_be_str(invoice)`` instead.
    The ``customization_id``, ``profile_id``, and ``namespaces`` arguments are
    accepted for backward compatibility but ignored; the profile is read from
    ``invoice.profile``.
    """
    return BEUBLSerializer().serialize_be_str(invoice)
