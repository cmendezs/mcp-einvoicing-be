# Release Process for mcp-einvoicing-be

This document describes how to release a new version of `mcp-einvoicing-be` to PyPI and the official MCP registry.

## One-Time Setup Requirements

**PyPI Trusted Publishing:**
PyPI publishing is fully automated via OIDC (no token stored). The Trusted Publisher is configured on PyPI under `cmendezs/mcp-einvoicing-be`, workflow `publish.yml`, environment `pypi`. No `.env` or secret needed.

**MCP Publisher CLI:**
Binary installed at `~/.local/bin/mcp-publisher` (already in `PATH`). To update:
```bash
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_darwin_arm64.tar.gz" \
  | tar xzf - -C ~/.local/bin/
```

**MCP Registry Authentication:**
Authenticate once with GitHub (device flow):
```bash
mcp-publisher login github
```

## Release Steps

**Step 1 — Version bump:** update `version` in `pyproject.toml` and `server.json` (top-level and `packages[].version`).

**Step 2 — Commit, tag and push:**
```bash
git add pyproject.toml server.json
git commit -m "release: v{VERSION} — {summary}"
git push origin main
git tag v{VERSION}
git push origin v{VERSION}
```
GitHub Actions publishes to PyPI automatically on tag push.

**Step 3 — MCP registry:**
```bash
mcp-publisher publish
```

## Changelog

### [0.10.0] - 2026-08-24
#### Changed
- **[core v1.20.0]** `peppol_send` now emits a real `wsse:Security` message signature. Core's AS4 transport client's `_apply_message_signature` previously computed a signature and discarded it, sending unsigned outbound messages. Wire-level behavior change, not independently validated against a live sandbox Peppol AP at time of publish — the signing code is shared core logic, not BE-specific, so no per-package sandbox gate was required (2026-08-24 user decision).
- Lower-bound pin on `mcp-einvoicing-core` raised to `>=1.20.0` (was `>=1.19.0`).
- `xslt2` extra now chains `mcp-einvoicing-core[xslt2]>=1.20.0` (was `>=1.19.0`).

#### Added
- Mounted three new opt-in core plugins in `server.py`, alongside the existing Peppol tool plugin: `register_peppol_reporting_tools` (`validate_eusr_report`, `validate_tsr_report`; requires `[xslt2]`), `register_peppol_mls_tools` (`validate_mls_message`, `build_mls_message`; requires `[xslt2]`), and `register_en16931_codelist_tools` (13 `list_*`/`check_*` pairs; requires `EINVOICING_EN16931_CODELIST_DIR`). `peppol_directory_search` arrives automatically via the existing `register_peppol_tools` mount.
- Server-registration smoke test asserting the new tools register.

### [0.9.0] - 2026-08-21
#### Changed
- **[ARCH-CONVERGE-BE]** `check_peppol_participant_be` removed. Peppol participant lookup, plus service-endpoint lookup, DNS-only diagnostic, AS4 send, and 8 eDEC codelist tools now come from the shared core Peppol tool plugin (`mcp_einvoicing_core.peppol.tools.register_peppol_tools`), mounted in `server.py` with a BE-specific identifier adapter that normalizes a bare Belgian VAT number to the `0208:<digits>` Peppol scheme. Use `peppol_lookup_participant` instead of the removed tool.
- Lower-bound pin on `mcp-einvoicing-core` raised to `>=1.19.0` (was `>=1.18.0`), required for `register_peppol_tools`.

### [0.8.0] - 2026-08-20
#### Changed
- **[CORE-EN16931-BASE-SCHEMATRON-1]** `validate_invoice_be(profile="peppol-bis-3"|"pint-eu")` now returns real validation results (`metadata.engine="schematron-xslt"`, `metadata.scope="en16931-base-only"`) instead of the `"unavailable"` result introduced in v0.7.0, using the CEN EN16931 base Schematron newly bundled in `mcp-einvoicing-core>=1.18.0`. Checks the ~50 CEN `BR-*` structural/arithmetic rules — a real improvement over the presence-only fallback this package carried before v0.7.0 — but explicitly does not check the Peppol-specific overlay (profile/process ID registration, `EndpointID` scheme, narrowed code lists). Every result carries an explicit warning that this is not a full Peppol BIS3 conformance check. See `context-library/decisions/peppol-schematron-artifact.md`.
- Lower-bound pin on `mcp-einvoicing-core` raised to `>=1.18.0` (was `>=1.15.0`) for the new `schematron_artifacts` module. Picks up the core v1.18.1 fix for the missing top-level `DueDate` in the UBL serializer/parser.

#### Unchanged
- The local full-Peppol-overlay Schematron path (`specs/peppol_bis_3/`, `_find_schematron_xslt`) stays wired exactly as before — if a properly-licensed compiled overlay stylesheet is ever added there, it still takes priority over the new base-only path. No such file exists today.

### [0.7.0] - 2026-08-17
#### Removed
- **[BE-SC-11 follow-up]** `PEPPOL_BIS3_RULES` (hand-rolled Peppol BIS 3.0 base-rule approximation, ~10 of ~50+ real rules, no arithmetic checks) removed entirely rather than kept as the "fixed" version from v0.6.0 — a package-local partial duplication of rules identical across every Peppol-BIS3 country is a recurring bug source. See `context-library/roadmap-2026.md` **[CORE-PEPPOL-SCHEMATRON-1]**.

#### Changed
- `validate_invoice_be(profile="peppol-bis-3"|"pint-eu")` now returns an explicit unavailable result (`valid=False`, `metadata.engine="unavailable"`) instead of a partial pass/fail when no compiled Schematron is loaded.
- `standards/mercurius.py`'s `MERCURIUS_RULES` no longer splices in the removed base rules — only the Mercurius-specific overlay (`MER-002`/`MER-003`/`MER-004`) remains. Every `mercurius` result now carries a `MERCURIUS-SCOPE` warning noting base EN16931/Peppol compliance is not checked.

### [0.6.0] - 2026-08-17
#### Fixed
- **[BE-SC-11]** `standards/peppol_bis_3.py`: `PEPPOL_BIS3_RULES` had every rule from the old `BR-02` onward paired with the wrong CEN/Peppol rule content (a pre-existing mislabeling, not introduced by this release) — relabeled against the real Peppol BIS 3.0 3.0.20 Schematron; added `PEPPOL-EN16931-R001` for the Profile identifier (BT-23) check, which is a Peppol-specific rule, not a CEN `BR-*` id.
- `tools/validation.py`: `_validate_with_profile`'s Schematron-result branch referenced `svrl_result.messages`/`m.message`, fields that do not exist on core's `ValidationResult`/`ValidationMessage` (`.errors`/`.warnings` of `.text`) — dead code, never exercised because no XSLT was ever bundled, would have raised `AttributeError` on first real use.

#### Changed
- `tools/validation.py`: `BEDocumentValidator.__init__` now uses core's `load_schematron_validator()` auto-dispatch (XSLT 1.0 vs. Saxon/XSLT 2.0+) instead of hardcoding the XSLT-1-only `SchematronValidator`. Added optional `xslt2` extra (`mcp-einvoicing-core[xslt2]`).
- Peppol BIS Billing 3.0 pin bumped 3.0.17 → 3.0.20 (2025 November release). Closes `regulatory-update` issue #4.

#### Known gap (unchanged)
- **[BE-SC-11]** remains open: no compiled, SVRL-producing Schematron XSLT is bundled. The 3.0.20 release bundle sourced for this refresh contained only the Schematron *sources* (`.sch`) plus a UBL-invoice-to-HTML viewer stylesheet (verified not to be a validator) — `validate_invoice_be` continues to run the (now-corrected) XPath fallback. Only `CEN-EN16931-UBL.sch` (EUPL 1.2 licensed) is bundled; `PEPPOL-EN16931-UBL.sch` and the viewer stylesheet were excluded pending redistribution-license confirmation. See `context-library/roadmap-2026.md` → `[CORE-PEPPOL-SCHEMATRON-1]`.

### [0.5.0] - 2026-07-15
#### Added
- **[BE-SC-9]** `standards/ubl.py` now populates `business_process` (BT-23) from the profile's `PROFILE_IDS` mapping, consuming `mcp-einvoicing-core>=1.15.0`; emitted as `<cbc:ProfileID>`.
- **[BE-SC-10]** `models/invoice.py` model validator auto-populates `buyer_reference` (BT-10) from `buyer.reference` when unset.
- `DocumentValidationResult` metadata now includes `engine` (`schematron-xslt` vs `xpath-fallback`) so callers can tell which validation path ran.

#### Fixed
- **[BE-SC-12]** Removed the fabricated Mercurius `MER-001` CustomizationID rule and `MERCURIUS_CUSTOMIZATION_ID` constant — Mercurius accepts standard Peppol BIS 3.0 UBL and does not define its own profile.
- Mercurius `MER-002`/`MER-003` endpoint-scheme rules used `cac:EndpointID` instead of the correct UBL basic-component `cbc:EndpointID`, so they never matched even on correctly-tagged invoices. Fixed as part of BE-SC-12 verification.
- **[BE-SC-13]** Removed the `BR-CO-15` XPath-presence-only fallback rule from `peppol_bis_3.py`; a weak presence check is no longer represented as arithmetic enforcement.
- **[BE-LC-6]** `tools/lookup.py` now calls the public `client.request()` (added in core v1.15.0) instead of the private `client._request()`.

#### Changed
- **[BE-SC-11]** (partial — not fully resolved) `tools/validation.py` no longer silently degrades to XPath validation when no Schematron XSLT is bundled; raises loudly with a documented gap reference instead. Bundling an actual compiled Peppol BIS 3.0 Schematron XSLT remains open — OpenPeppol does not distribute one as a release asset.
- Core dependency floor raised to `mcp-einvoicing-core>=1.15.0,<2.0.0`.

### [0.4.0] - 2026-06-30
#### Added
- **[BE-LC-5]** `parse_ubl_invoice_be` MCP tool for the mandatory UBL reception capability (Art. 13quater RD no. 1, RD of 8 July 2025). Extracts the EN 16931 core field set plus Belgian extensions (OGM/VCS reference, 0208 endpoint scheme) into a `be_extensions` dict.
- **[BE-SC-15]** EU PINT v1.0.1 (`pint-eu`) profile support: `urn:peppol:pint:billing-1@en16931-2017@eu-3`, the OpenPeppol-published spec, selectable alongside `peppol-bis-3`.
- **[BE-TL-4]** OGM/VCS structured payment reference check-digit validator (`@field_validator` on `BEPaymentTerms.ogm_reference`), delegating to the new `RoutingIdentifier.validate_be_ogm` in `mcp-einvoicing-core>=1.13.0`.
- Schematron wiring: `BEDocumentValidator` loads the pre-compiled Peppol BIS 3.0 Schematron XSLT from `specs/` when present, delegating to core's `SchematronValidator`; falls back to hand-coded XPath rules otherwise.
- **[BE-LC-2]** Structured `BCE_API_KEY_MISSING` warning in `lookup_vat_be` response when the env var is absent.
- **[BE-LC-3]** Structured error dict for non-404 Peppol SMP lookup failures in `check_peppol_participant_be`.

#### Fixed
- **[BE-SC-4]** Removed the fabricated `pint-be` profile and its unanchored URN (`urn:fdc:www.nbb.be:2020:pintbe`) — PINT-BE was never published by OpenPeppol. Belgian law mandates Peppol BIS 3.0 only.
- **[BE-SC-8]** Renamed `buyer_item_id` to `buyer_article_id` (BT-156, was mislabelled as BT-157); wired to `<cac:BuyersItemIdentification>` in the UBL serializer. Backward-compat alias retained.
- **[BE-SC-6]** `buyer_reference` (BT-10) confirmed end-to-end via `EN16931Invoice` inheritance; round-trip test added.

#### Changed
- **[BE-AUD-1]** Closed all remaining audit overrides for core v1.12.0+ symbols (Generic, TypeVar, CAdESSigner, CAdESSignerConfig). Audit verdict: PASS, 0 blocking, 0 warnings.
- **[BE-LC-4]** Removed dead `MERCURIUS_ACCESS_POINT` constant; documented Mercurius B2G routing (Peppol receiver, no separate API, `0208` scheme) in README (EN/FR/NL) and server instructions.
- Core dependency floor raised to `mcp-einvoicing-core>=1.13.0,<2.0.0`.

### [0.3.0] - 2026-06-27
#### Added
- **[ARCH-VALID-1c] HIGH:** `BEParty.tax_id` now enforces the BCE/KBO modulo-97 check digit at model construction via a new `@field_validator(mode="after")` delegating to `mcp_einvoicing_core.TaxIdentifier.validate_be_vat` (3-layer party-validation pattern, Layer 1). Invalid VAT/enterprise numbers raise `ValidationError` instead of being silently accepted.

#### Changed
- Test fixtures in `tests/conftest.py` switched from placeholder VATs to mod-97-valid examples (`BE0428759497`, `BE0403170701`); added `TestBEPartyTaxIdValidation` covering invalid checksum and `None` cases.

### [0.2.0] - 2026-06-01
#### Fixed / Added
- **[BE-SC-2] BLOCKING:** `BEInvoice` now extends `EN16931Invoice`; `BEParty` extends
  `EN16931Party`; `BEAddress` extends `EN16931Address`. Belgian field-name aliases via
  Pydantic `AliasChoices`. A `model_validator(mode="before")` auto-derives EN 16931
  mandatory totals, `line_items`, and `tax_lines` from Belgian `lines` input.
- **[BE-SC-3] BLOCKING:** `src/mcp_einvoicing_be/specs/` created with `download.py`
  (fetches Peppol BIS 3.0 Schematron from OpenPeppol; documents UBL 2.1 XSD sources).
- **[BE-SC-1] BLOCKING:** `_evaluate_rule` now uses lxml XPath evaluation;
  `/Invoice/...` absolute XPaths converted to relative paths on the Invoice root element
  with the full UBL 2.1 namespace map. The unconditional `return None` stub removed.
  `parse_ubl_xml` in `helpers.py` updated to lxml for namespace-aware parsing.
- **[BE-TL-1] HIGH:** `normalize_vat_be` validates the modulo-97 check digit
  (SPF Finances / FOD Financiën algorithm, identical to ISO 7064 MOD 97-10 / IBAN).
- **[BE-TL-2] HIGH:** `VatCategory` enum gains `REDUCED_12 = "AA"` (12%) and
  `REDUCED_6 = "AB"` (6%) per UNCL5305.
- **[BE-TL-3] HIGH:** `vat_rate_to_category` documented as a legacy zero-rate detection
  helper; docstring explains why callers must set `vat_category` explicitly for 12%/6%
  and reverse-charge lines.
- **[BE-SH-1] HIGH:** XML escaping now handled structurally via `EN16931UBLSerializer`
  (lxml escapes all text content automatically). Old hand-rolled serialiser replaced by
  a lightweight adapter.
- **[BE-SH-2] MEDIUM:** `_INTENTIONAL_OVERRIDES` fully populated with `OVERRIDE-REASON:`
  comments; 0 BLOCKING / 0 WARNINGS in audit gate.
- **[BE-LC-1] HIGH:** `check_peppol_participant_be` migrated to `PeppolSMPClient` from
  `mcp-einvoicing-core`; DNS-over-HTTPS U-NAPTR resolution + SMP service-group lookup
  per Peppol BDMSL specification.
- 44 tests passing (28 new); audit gate PASS (0 blocking, 0 warnings).

### [0.1.4] - 2026-05-31
#### Added
- **[BE-CORE-1]** Replaced the 200-line local `render_ubl_invoice()` with
  `BEUBLSerializer(EN16931UBLSerializer)` and `BEUBLParser(EN16931UBLParser)` subclasses
  from `mcp-einvoicing-core` v1.3.0.
- `_be_invoice_to_en16931()` adapter maps `BEInvoice` fields to `EN16931Invoice`,
  including VAT totals grouped per EN 16931 §7.4 (ROUND_HALF_EVEN) and Peppol BIS 3.0 /
  PINT-BE profile URNs.
- `BEUBLSerializer.serialize_be_str()` for API/tool use (no XML declaration).
- `render_ubl_invoice()` retained as a deprecated backward-compatibility shim.
- **[BE-SC-5]** closed: `BEUBLSerializer` inherits `_build_root()` from
  `EN16931UBLSerializer` which already dispatches `<CreditNote>` root for type code 381.
- **[BE-SC-7]** closed: local `round(x, 2)` arithmetic replaced by `format_amount()`
  with `ROUND_HALF_EVEN` throughout.
- Audit gate: PASS (0 blocking, 0 warnings, 133 OK).

---

## Notes

- The MCP registry does **not** sync automatically with PyPI or GitHub — step 3 is required for every release.
- The `server.json` description field must be **≤ 100 characters**.
- PyPI rejects re-uploads of the same version — always bump before tagging.
