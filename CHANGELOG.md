# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.4.0] — 2026-06-30

### Added
- `parse_ubl_invoice_be` tool: UBL 2.1 invoice parsing for the mandatory reception capability (Art. 13quater RD no. 1), including Belgian extensions (OGM/VCS reference, 0208 endpoint scheme)
- EU PINT v1.0.0 (`pint-eu`) profile: `urn:peppol:pint:billing-1@en16931-2017@eu-3`
- OGM/VCS structured payment reference check-digit validator on `BEPaymentTerms.ogm_reference`
- Schematron-based validation via core's `SchematronValidator` when the Peppol BIS 3.0 XSLT is present in `specs/`
- Structured `BCE_API_KEY_MISSING` warning and structured Peppol lookup error responses

### Removed
- `validate_pint_be` tool and the `pint-be` profile (PINT-BE was never a published OpenPeppol specification)

### Fixed
- `buyer_item_id` renamed to `buyer_article_id` (BT-156, was mislabelled as BT-157); now wired to `<cac:BuyersItemIdentification>` in UBL output

### Changed
- Core dependency floor raised to `mcp-einvoicing-core>=1.13.0,<2.0.0`

---

## [0.3.0] — 2026-06-27

### Added
- **[ARCH-VALID-1c]** `BEParty.tax_id` now enforces the BCE/KBO modulo-97 check digit at model-construction time via a new `@field_validator` calling `mcp_einvoicing_core.TaxIdentifier.validate_be_vat` (3-layer party-validation pattern, Layer 1). Invalid VAT/enterprise numbers raise `ValidationError` instead of being silently accepted.

### Changed
- Test fixtures in `tests/conftest.py` switched from placeholder VAT numbers to mod-97-valid examples (`BE0428759497` and `BE0403170701`).

---

## [0.1.0] — TBD

_Initial release._

[Unreleased]: https://github.com/cmendezs/mcp-einvoicing-be/compare/HEAD
