# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Francais](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Introduction

`mcp-einvoicing-be` is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes tools for Belgian electronic invoicing. It covers the full Belgian e-invoicing ecosystem: **Peppol BIS Billing 3.0**, **UBL 2.1**, and the **Mercurius** network for public-sector invoicing. The server is part of the `mcp-einvoicing-*` family of country-specific servers, all built on top of [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), which provides the shared validation engine, UBL abstractions, and Peppol network utilities.

## Installation

### Requirements

- Python ≥ 3.11
- [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core) (installed automatically as a dependency)

### Using `uv` (recommended)

```bash
uv add mcp-einvoicing-be
```

### Using `pip`

```bash
pip install mcp-einvoicing-be
```

### From source

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
```

## Configuration

### Environment variables

| Variable | Description | Default |
|---|---|---|
| `BCE_API_KEY` | API key for the Belgian BCE/KBO enterprise database | — |
| `PEPPOL_ENV` | Peppol environment: `production` or `test` | `production` |
| `PEPPOL_SML_URL` | Override the SML lookup URL | (auto) |
| `EINVOICING_PEPPOL_CODELIST_DIR` | Local directory containing your own copy of the OpenPeppol eDEC Code Lists, required by the codelist tools (not bundled with this package; see `mcp-einvoicing-core` README) | — |
| `EINVOICING_EN16931_CODELIST_DIR` | Local directory containing your own copy of the CEF "Digital Building Blocks" EN 16931 semantic code lists, required by the EN 16931 codelist tools (not bundled; see `mcp-einvoicing-core` README) | — |
| `LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

The EUSR/TSR reporting and MLS tools additionally require the `[xslt2]` extra (`pip install "mcp-einvoicing-be[xslt2]"`) for Schematron validation.

## Claude Desktop integration

To use this server with Claude, add this configuration to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "your-bce-api-key",
        "PEPPOL_ENV": "production"
      }
    }
  }
}
```

For a local development install:

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uv",
      "args": ["run", "mcp-einvoicing-be"],
      "cwd": "/path/to/mcp-einvoicing-be"
    }
  }
}
```

## Cursor integration

Cursor supports MCP servers via stdio. Add the configuration in:
- **Global** (all projects): `~/.cursor/mcp.json`
- **Project** (this repository only): `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "your-bce-api-key",
        "PEPPOL_ENV": "production"
      }
    }
  }
}
```

Reload the Cursor window (`Ctrl+Shift+P` then *Reload Window*) to apply the changes.

## Kiro integration

Kiro supports MCP servers via its dedicated configuration file. Two levels are available:
- **Global** (all projects): `~/.kiro/settings/mcp.json`
- **Workspace** (this repository only): `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "your-bce-api-key",
        "PEPPOL_ENV": "production"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

The file is automatically reloaded on save. You can also open the config via the command palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) then *MCP*.

> **Kiro security tip**: rather than writing secrets in plain text, use the syntax `"BCE_API_KEY": "${BCE_API_KEY}"`, Kiro resolves shell environment variables at startup.

## Available tools

### `validate_invoice_be`

Validates a UBL 2.1 XML invoice. The `peppol-bis-3`/`pint-eu` profiles run real Schematron validation against the CEN EN 16931 base rules (~50 `BR-*` structural/arithmetic rules, via `mcp-einvoicing-core`'s bundled base Schematron — see CHANGELOG.md v0.8.0). This does not check the Peppol-specific overlay rules (no confirmed OpenPeppol redistribution rights); results carry an explicit `en16931-base-only` scope warning and should not be read as full Peppol BIS3 conformance. The `mercurius` profile runs the Mercurius-specific overlay (endpoint scheme, PO reference) but does not check base EN 16931/Peppol BIS 3.0 compliance.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `xml` | `string` | yes | Raw UBL 2.1 XML content |
| `profile` | `string` | no | `peppol-bis-3` (default) or `mercurius` |

Returns a `ValidationResult` with `valid`, `errors`, and `warnings` (each carrying the failed rule ID and a human-readable message).

---

### `generate_invoice_be`

Generates a valid UBL 2.1 Belgian e-invoice XML document from structured data.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `invoice_data` | `object` | yes | Invoice fields (see `InvoiceInput` schema below) |
| `profile` | `string` | no | `peppol-bis-3` (default) |

The `InvoiceInput` object supports:

```json
{
  "invoice_number": "INV-2024-001",
  "issue_date": "2024-01-15",
  "due_date": "2024-02-14",
  "currency_code": "EUR",
  "supplier": { "name": "...", "vat_number": "BE0428759497", "address": {...} },
  "customer": { "name": "...", "vat_number": "BE0403170701", "address": {...} },
  "lines": [{ "description": "...", "quantity": 1, "unit_price": 100.00, "vat_rate": 21.0 }]
}
```

Returns a UBL 2.1 XML string.

---

### `transform_to_ubl`

Converts a structured JSON invoice payload to UBL 2.1 XML without full validation. Useful as a first step before validation.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `data` | `object` | yes | Source invoice data (same shape as `InvoiceInput`) |

---

### `lookup_vat_be`

Looks up a Belgian enterprise number (VAT number) against the BCE/KBO public database.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `vat_number` | `string` | yes | Belgian VAT/enterprise number, e.g. `BE0428759497` or `0123456789` |

Returns enterprise name, registered address, legal status, and NACE activity codes.

---

### Peppol network tools

Peppol participant lookup, service-endpoint lookup, a DNS-only diagnostic, AS4 send, Peppol Directory search, and the OpenPeppol eDEC codelist tools are provided by the shared core Peppol tool plugin (`mcp_einvoicing_core.peppol.tools.register_peppol_tools`), mounted in `server.py` with a BE-specific identifier adapter: a bare Belgian VAT number (e.g. `0428759497` or `BE0428759497`) is normalized to the `0208:<digits>` Peppol scheme (KBO/BCE enterprise number); an already scheme-qualified identifier (e.g. `0208:0428759497`) passes through unchanged.

`peppol_send` signs outbound messages with a real `wsse:Security` signature as of `mcp-einvoicing-core` v1.20.0 (previously computed and discarded — see CHANGELOG.md v0.10.0).

| Tool | Description |
|---|---|
| `peppol_lookup_participant` | Check whether a business is registered on the Peppol network; returns registration status and supported document types |
| `peppol_get_service_endpoint` | Fetch the AS4 endpoint for a participant's document type |
| `resolve_peppol_dns` | DNS-only (SML) diagnostic, independent of SMP reachability |
| `peppol_send` | Transmit a UBL/CII invoice via AS4 |
| `peppol_directory_search` | Search the public Peppol Directory by participant, name, country, or document type |
| `list_participant_id_schemes`, `list_document_type_ids`, `list_process_ids`, `list_spis_use_case_ids` | OpenPeppol eDEC codelist lookups (require `EINVOICING_PEPPOL_CODELIST_DIR`) |
| `check_document_type_id_in_codelist`, `check_process_id_in_codelist`, `check_participant_id_scheme_in_codelist`, `get_peppol_codelist_version` | OpenPeppol eDEC codelist checks and version reporting |

See the [`mcp-einvoicing-core` README](https://github.com/cmendezs/mcp-einvoicing-core#readme) for full parameter documentation on these tools.

---

### Peppol reporting and status tools

Added in v0.10.0 via three opt-in core plugins, mounted unconditionally in `server.py`. Each raises a clear error at call time (not at registration) if its extra or data directory is missing.

| Tool | Plugin | Description |
|---|---|---|
| `validate_eusr_report` | `register_peppol_reporting_tools` | Validate an End User Statistics Report (XSD, then Schematron). Requires the `[xslt2]` extra. |
| `validate_tsr_report` | `register_peppol_reporting_tools` | Validate a Transaction Statistics Report (XSD, then Schematron). Requires the `[xslt2]` extra. |
| `validate_mls_message` | `register_peppol_mls_tools` | Validate a Message Level Status document (UBL `ApplicationResponse-2` subset). Requires the `[xslt2]` extra. |
| `build_mls_message` | `register_peppol_mls_tools` | Build a document-level MLS response. Requires the `[xslt2]` extra. |
| 13 `list_*`/`check_*` pairs, `get_en16931_codelist_version` | `register_en16931_codelist_tools` | EN 16931 semantic code list lookups/checks (units, VAT categories, etc.). Require `EINVOICING_EN16931_CODELIST_DIR`. |

See the [`mcp-einvoicing-core` README](https://github.com/cmendezs/mcp-einvoicing-core#readme) for full parameter documentation on these tools.

---

### `parse_ubl_invoice_be`

Parses a UBL 2.1 XML invoice (Peppol BIS 3.0) into a structured dict. Satisfies the mandatory reception capability required by Art. 13quater of Royal Decree no. 1.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `xml_content` | `string` | yes | Raw UBL 2.1 XML invoice content |

Returns `{"success": true, "invoice": {...}, "warnings": []}` on success, or `{"success": false, "error": "..."}` on parse failure.

---

### `get_invoice_types_be`

Returns the list of supported Belgian e-invoice document types (invoice, credit note, debit note) with their UBL `customizationID` and `profileID` values for each profile.

No input parameters required.

## B2G via Mercurius

Mercurius is the Belgian federal public-sector e-invoicing platform. It operates as a **Peppol network receiver**, not a separate API. B2G invoices are submitted through the standard Peppol network using the authority's participant ID in the `0208` scheme (KBO/BCE 10-digit enterprise number). The Access Point routes the invoice to Mercurius automatically. No Mercurius-specific submission endpoint or API key is required.

## Architecture

```
mcp-einvoicing-be/
├── src/
│   └── mcp_einvoicing_be/
│       ├── __init__.py
│       ├── server.py              # MCP server entry point & tool registration
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── validation.py      # validate_invoice_be
│       │   ├── generation.py      # generate_invoice_be
│       │   ├── transformation.py  # transform_to_ubl
│       │   ├── parsing.py         # parse_ubl_invoice_be
│       │   └── lookup.py          # lookup_vat_be, get_invoice_types_be
│       ├── models/
│       │   ├── __init__.py
│       │   ├── invoice.py         # InvoiceInput, InvoiceLine, ValidationResult
│       │   └── party.py           # Supplier, Customer, Address
│       ├── standards/
│       │   ├── __init__.py
│       │   ├── peppol_bis_3.py    # Peppol BIS Billing 3.0 rules & customization IDs
│       │   ├── ubl.py             # UBL 2.1 namespace constants & XML helpers
│       │   ├── pint_be.py         # PINT-BE placeholder (removed in v0.4.0)
│       │   └── mercurius.py       # Mercurius network config & overlay rules
│       └── utils/
│           ├── __init__.py
│           └── helpers.py         # VAT number normalization, date formatting, etc.
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tools/
│   │   ├── __init__.py
│   │   ├── test_validation.py
│   │   ├── test_generation.py
│   │   └── test_transformation.py
│   └── fixtures/
│       ├── invoice_valid_peppol.xml
│       ├── invoice_valid_pint_be.xml
│       └── invoice_invalid.xml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── publish.yml
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

### Relationship to `mcp-einvoicing-core`

`mcp-einvoicing-core` provides:
- Shared UBL 2.1/2.3 XML parsing and serialization utilities
- EN 16931 base validation rules (syntax + semantic)
- Peppol network client (SMP lookup, SML resolution)
- Common Pydantic base models (`BaseInvoice`, `BaseParty`, `BaseValidationResult`)

`mcp-einvoicing-be` adds Belgium-specific logic on top:
- Mercurius network overlay rule validation (XPath-based) for B2G invoicing
- BCE/KBO enterprise database integration
- Belgian VAT number normalization (BTW/TVA format) and OGM/VCS check-digit validation
- UBL 2.1 invoice parsing for mandatory reception (Art. 13quater)
- `customizationID` and `profileID` values specific to the Belgian Peppol corner

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a pull request.

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
uv run pytest
uv run ruff check src tests
uv run mypy src
```

All pull requests must:
- Pass the full test suite (`pytest`)
- Pass linting (`ruff check`)
- Pass type checking (`mypy`)
- Include or update tests for any changed behaviour
- Reference the relevant rule ID(s) when fixing a validation issue

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## Other e-invoicing MCP servers

| Country | Server |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇧🇪 Belgium | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brazil | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 France | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Germany | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italy | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇲🇽 Mexico | [mcp-cfdi-mx](https://github.com/cmendezs/mcp-cfdi-mx) |
| 🇵🇱 Poland | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇸🇬 Singapore | [mcp-invoicenow-sg](https://github.com/cmendezs/mcp-invoicenow-sg) |
| 🇪🇸 Spain | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |
| 🇦🇪 United Arab Emirates | [mcp-einvoicing-ae](https://github.com/cmendezs/mcp-einvoicing-ae) |

## License

This project is licensed under the **Apache 2.0** — see [LICENSE](LICENSE) for details. For the full version history, see [CHANGELOG.md](CHANGELOG.md).
