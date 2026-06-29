# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Francais](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Introduction

`mcp-einvoicing-be` is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes tools for Belgian electronic invoicing. It covers the full Belgian e-invoicing ecosystem: **Peppol BIS Billing 3.0**, **UBL 2.1**, and the **Mercurius** network for public-sector invoicing. The server is part of the `mcp-einvoicing-*` family of country-specific servers, all built on top of [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), which provides the shared validation engine, UBL abstractions, and Peppol network utilities.

---

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

---

## Configuration

Add the server to your MCP client configuration. For Claude Desktop, edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"]
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

### Environment variables

| Variable | Description | Default |
|---|---|---|
| `BCE_API_KEY` | API key for the Belgian BCE/KBO enterprise database | — |
| `PEPPOL_ENV` | Peppol environment: `production` or `test` | `production` |
| `PEPPOL_SML_URL` | Override the SML lookup URL | (auto) |
| `LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## Available Tools

### `validate_invoice_be`

Validates a UBL 2.1 XML invoice against Belgian business rules (EN 16931 + Peppol BIS 3.0 + Mercurius overlay).

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

### `check_peppol_participant_be`

Checks whether a Belgian company is registered as a Peppol participant by querying the SMP/SML network.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `identifier` | `string` | yes | Peppol participant ID (e.g. `0088:BE0428759497`) or plain Belgian VAT number |

Returns registration status, supported document type identifiers, and the SMP access point endpoint URL.

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

---

## B2G via Mercurius

Mercurius is the Belgian federal public-sector e-invoicing platform. It operates as a **Peppol network receiver**, not a separate API. B2G invoices are submitted through the standard Peppol network using the authority's participant ID in the `0208` scheme (KBO/BCE 10-digit enterprise number). The Access Point routes the invoice to Mercurius automatically. No Mercurius-specific submission endpoint or API key is required.

---

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
│       │   └── lookup.py          # lookup_vat_be, check_peppol_participant_be, get_invoice_types_be
│       ├── models/
│       │   ├── __init__.py
│       │   ├── invoice.py         # InvoiceInput, InvoiceLine, ValidationResult
│       │   └── party.py           # Supplier, Customer, Address
│       ├── standards/
│       │   ├── __init__.py
│       │   ├── peppol_bis_3.py    # Peppol BIS Billing 3.0 rules & customization IDs
│       │   ├── ubl.py             # UBL 2.1 namespace constants & XML helpers
│       │   ├── pint_be.py         # PINT-BE placeholder (removed in v0.3.1)
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
- Peppol BIS 3.0 business rule validation (XPath-based)
- Mercurius network overlay rules for B2G invoicing
- BCE/KBO enterprise database integration
- Belgian VAT number normalization (BTW/TVA format) and OGM/VCS check-digit validation
- UBL 2.1 invoice parsing for mandatory reception (Art. 13quater)
- `customizationID` and `profileID` values specific to the Belgian Peppol corner

---

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

---

## Other e-invoicing MCP servers

| Country | Server |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇧🇪 Belgium | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brazil | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 France | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Germany | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italy | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇵🇱 Poland | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇪🇸 Spain | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |

---

## License

This project is licensed under the **Apache 2.0** — see [LICENSE](LICENSE) for details.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full list of changes by version.
