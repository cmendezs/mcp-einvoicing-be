# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.6.0] — 2026-08-17

### Fixed
- `PEPPOL_BIS3_RULES` (XPath fallback validator): rule IDs were paired with the wrong rule content — every entry from the old `BR-02` onward tested a different field than its real CEN/Peppol rule ID (e.g. the old `BR-02` checked ProfileID/BT-23, but the real `BR-02` checks the Invoice number/BT-1). Relabeled against the OpenPeppol 3.0.20 Schematron sources; the Profile identifier (BT-23) check is now correctly attributed to `PEPPOL-EN16931-R001` rather than a nonexistent CEN `BR-*` id.
- `BEDocumentValidator._validate_with_profile`: the Schematron-XSLT result branch read `svrl_result.messages`/`m.message`, fields that do not exist on core's `ValidationResult`/`ValidationMessage` (`.errors`/`.warnings` of `.text`) — dead code, never exercised because no XSLT was ever bundled, but would have raised `AttributeError` the first time it ran.
- `BEDocumentValidator.__init__` now uses core's `load_schematron_validator()` (auto-dispatch to XSLT 1.0 or Saxon/XSLT 2.0+) instead of hardcoding the XSLT-1-only `SchematronValidator`.

### Changed
- Pinned Peppol BIS Billing 3.0 spec version to 3.0.20 (OpenPeppol 2025 November release, was 3.0.17). Closes `regulatory-update` issue #4.
- Added optional `xslt2` extra (`mcp-einvoicing-core[xslt2]`) for future Saxon-HE-backed Schematron validation.

### Known gap (unchanged)
- `[GAP id=core.schematron.be_bundled_xslt]` remains open: no compiled, SVRL-producing Schematron XSLT is bundled. The 3.0.20 release bundle sourced for this refresh contains only the Schematron sources (`.sch`) plus a UBL-to-HTML viewer stylesheet (verified not to be a validator) — `validate_invoice_be` continues to run the XPath fallback above. See `context-library/countries/be.md` for detail.

---

## [0.4.0] — 2026-06-30

### Added
- `parse_ubl_invoice_be` tool: UBL 2.1 invoice parsing for the mandatory reception capability (Art. 13quater RD no. 1), including Belgian extensions (OGM/VCS reference, 0208 endpoint scheme)
- EU PINT v1.0.1 (`pint-eu`) profile: `urn:peppol:pint:billing-1@en16931-2017@eu-3`
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
