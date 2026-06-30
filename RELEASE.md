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

### [0.4.0] - 2026-06-30
#### Added
- **[BE-LC-5]** `parse_ubl_invoice_be` MCP tool for the mandatory UBL reception capability (Art. 13quater RD no. 1, RD of 8 July 2025). Extracts the EN 16931 core field set plus Belgian extensions (OGM/VCS reference, 0208 endpoint scheme) into a `be_extensions` dict.
- **[BE-SC-15]** EU PINT v1.0.0 (`pint-eu`) profile support: `urn:peppol:pint:billing-1@en16931-2017@eu-3`, the OpenPeppol-published spec, selectable alongside `peppol-bis-3`.
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
