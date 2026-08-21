# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.9.0] - 2026-08-21

### Changed
- `check_peppol_participant_be` removed. Peppol participant lookup (and the rest of the Peppol network surface: service-endpoint lookup, DNS-only diagnostic, AS4 send, and the eDEC codelist tools) now comes from the shared core Peppol tool plugin (`mcp_einvoicing_core.peppol.tools.register_peppol_tools`), mounted in `server.py` with a BE-specific identifier adapter (`_be_id_adapter`) that normalizes a bare Belgian VAT number to the `0208:<digits>` Peppol scheme (KBO/BCE). Use `peppol_lookup_participant` instead of the removed tool; behavior and response shape are unchanged for that use case, but the tool now also exposes `peppol_get_service_endpoint`, `resolve_peppol_dns`, `peppol_send`, and 8 eDEC codelist tools that were not previously available in this package. See `context-library/roadmap-2026.md` **[ARCH-CONVERGE-BE]**.
- Lower-bound pin on `mcp-einvoicing-core` raised to `>=1.19.0` (was `>=1.18.0`), required for `register_peppol_tools`.

---

## [0.8.0] — 2026-08-20

### Changed
- `validate_invoice_be(profile="peppol-bis-3"|"pint-eu")` now returns real validation results (`metadata.engine="schematron-xslt"`, `metadata.scope="en16931-base-only"`) instead of the `"unavailable"` result introduced in v0.7.0, using the CEN EN16931 base Schematron newly bundled in `mcp-einvoicing-core>=1.18.0` (**[CORE-EN16931-BASE-SCHEMATRON-1]**). This checks the ~50 CEN `BR-*` structural/arithmetic rules — a real improvement over the presence-only XPath fallback this package carried before v0.7.0 — but explicitly does **not** check the Peppol-specific overlay rules (profile/process ID registration, `EndpointID` scheme, narrowed code lists). Every result now carries an explicit warning that this is not a full Peppol BIS3 conformance check. See `context-library/decisions/peppol-schematron-artifact.md` for why the overlay itself still cannot ship (no confirmed OpenPeppol redistribution rights).
- Lower-bound pin on `mcp-einvoicing-core` raised to `>=1.18.0` (was `>=1.15.0`) for the new `schematron_artifacts` module.

### Unchanged
- The local full-Peppol-overlay Schematron path (`specs/peppol_bis_3/`, `_find_schematron_xslt`) stays wired exactly as before — if a properly-licensed compiled overlay stylesheet is ever added there, it still takes priority over the new base-only path. No such file exists today.

---

## [0.7.0] — 2026-08-17

### Removed
- `PEPPOL_BIS3_RULES` (the package's hand-rolled Peppol BIS 3.0 base-rule approximation) removed entirely, rather than kept as the "fixed" version shipped in v0.6.0. It covered only ~10 of the ~50+ real CEN/Peppol rules (no arithmetic/totals checks) and had just been found to carry a rule-ID mislabeling bug — a package-local partial duplication of rules that are identical across every Peppol-BIS3-consuming country is a recurring source of exactly this class of bug. See `context-library/roadmap-2026.md` **[CORE-PEPPOL-SCHEMATRON-1]**.

### Changed
- `validate_invoice_be(profile="peppol-bis-3"|"pint-eu")` now returns an explicit unavailable result (`valid=False`, an error explaining why, `metadata.engine="unavailable"`) when no real compiled Schematron is loaded, instead of a silently-partial pass/fail. A false "valid" from an incomplete rule set is worse than a clear "cannot validate" signal for a compliance tool.
- `standards/mercurius.py`'s `MERCURIUS_RULES` no longer splices in `PEPPOL_BIS3_RULES` — it now contains only the Mercurius-specific overlay (`MER-002`/`MER-003`/`MER-004`), which is genuinely BE-local and was not part of the cross-country duplication problem. Every `mercurius`-profile result now carries an explicit `MERCURIUS-SCOPE` warning stating that base EN16931/Peppol BIS 3.0 compliance is not checked by this profile, since it no longer runs those checks at all.

### Fixed
- `mercurius` profile validation was silently affected by the same rule-ID mislabeling bug fixed in v0.6.0, since `MERCURIUS_RULES` previously spliced in `PEPPOL_BIS3_RULES` directly. Moot now that the splice is removed.

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
