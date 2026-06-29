# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Francais](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Inleiding

`mcp-einvoicing-be` is een [MCP-server (Model Context Protocol)](https://modelcontextprotocol.io) die tools aanbiedt voor Belgische elektronische facturatie. Het dekt het volledige Belgische e-facturatie-ecosysteem: **Peppol BIS Billing 3.0**, **UBL 2.1**, en het **Mercurius**-netwerk voor facturatie aan de overheidssector. De server maakt deel uit van de `mcp-einvoicing-*`-familie van landspecifieke servers, allemaal gebouwd bovenop [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), dat de gedeelde validatie-engine, UBL-abstracties en Peppol-netwerkutilities levert.

---

## Installatie

### Vereisten

- Python ≥ 3.11
- [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core) (wordt automatisch geïnstalleerd als afhankelijkheid)

### Met `uv` (aanbevolen)

```bash
uv add mcp-einvoicing-be
```

### Met `pip`

```bash
pip install mcp-einvoicing-be
```

### Vanuit broncode

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
```

---

## Configuratie

Voeg de server toe aan de configuratie van uw MCP-client. Voor Claude Desktop, bewerk `claude_desktop_config.json`:

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

Voor een lokale ontwikkelingsinstallatie:

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

### Omgevingsvariabelen

| Variabele | Beschrijving | Standaard |
|---|---|---|
| `BCE_API_KEY` | API-sleutel voor de Belgische BCE/KBO-ondernemingsdatabank | — |
| `PEPPOL_ENV` | Peppol-omgeving: `production` of `test` | `production` |
| `PEPPOL_SML_URL` | Overschrijf de SML-opzoek-URL | (auto) |
| `LOG_LEVEL` | Logboekniveau: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## Beschikbare tools

### `validate_invoice_be`

Valideert een UBL 2.1 XML-factuur volgens de Belgische bedrijfsregels (EN 16931 + Peppol BIS 3.0 + Mercurius-laag).

| Parameter | Type | Vereist | Beschrijving |
|---|---|---|---|
| `xml` | `string` | ja | Ruwe UBL 2.1 XML-inhoud |
| `profile` | `string` | nee | `peppol-bis-3` (standaard) of `mercurius` |

Retourneert een `ValidationResult` met `valid`, `errors` en `warnings` (elk met het gefaalde regel-ID en een leesbaar bericht).

---

### `generate_invoice_be`

Genereert een geldig UBL 2.1 Belgisch e-factuur XML-document vanuit gestructureerde gegevens.

| Parameter | Type | Vereist | Beschrijving |
|---|---|---|---|
| `invoice_data` | `object` | ja | Factuurvelden (zie het `InvoiceInput`-schema hieronder) |
| `profile` | `string` | nee | `peppol-bis-3` (standaard) |

Het `InvoiceInput`-object ondersteunt:

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

Retourneert een UBL 2.1 XML-tekenreeks.

---

### `transform_to_ubl`

Converteert een gestructureerde JSON-factuurpayload naar UBL 2.1 XML zonder volledige validatie. Handig als eerste stap voor validatie.

| Parameter | Type | Vereist | Beschrijving |
|---|---|---|---|
| `data` | `object` | ja | Bronfactuurgegevens (zelfde formaat als `InvoiceInput`) |

---

### `lookup_vat_be`

Zoekt een Belgisch ondernemingsnummer (btw-nummer) op in de openbare BCE/KBO-databank.

| Parameter | Type | Vereist | Beschrijving |
|---|---|---|---|
| `vat_number` | `string` | ja | Belgisch btw-/ondernemingsnummer, bijv. `BE0428759497` of `0123456789` |

Retourneert de ondernemingsnaam, het geregistreerde adres, de juridische status en de NACE-activiteitscodes.

---

### `check_peppol_participant_be`

Controleert of een Belgisch bedrijf geregistreerd is als Peppol-deelnemer door het SMP/SML-netwerk te bevragen.

| Parameter | Type | Vereist | Beschrijving |
|---|---|---|---|
| `identifier` | `string` | ja | Peppol-deelnemer-ID (bijv. `0088:BE0428759497`) of gewoon Belgisch btw-nummer |

Retourneert de registratiestatus, ondersteunde documenttype-identificatoren en de URL van het SMP-toegangspunt.

---

### `parse_ubl_invoice_be`

Analyseert een UBL 2.1 XML-factuur (Peppol BIS 3.0) naar een gestructureerd woordenboek. Voldoet aan de verplichte ontvangstcapaciteit vereist door Art. 13quater van KB nr. 1.

| Parameter | Type | Vereist | Beschrijving |
|---|---|---|---|
| `xml_content` | `string` | ja | Ruwe UBL 2.1 XML-factuurinhoud |

Retourneert `{"success": true, "invoice": {...}, "warnings": []}` bij succes, of `{"success": false, "error": "..."}` bij een parseerfout.

---

### `get_invoice_types_be`

Retourneert de lijst van ondersteunde Belgische e-factuurdocumenttypen (factuur, creditnota, debetnota) met hun UBL `customizationID`- en `profileID`-waarden voor elk profiel.

Geen invoerparameters vereist.

---

## B2G via Mercurius

Mercurius is het Belgische federale e-facturatieplatform voor de overheidssector. Het werkt als een **Peppol-netwerkontvanger**, niet als een aparte API. B2G-facturen worden ingediend via het standaard Peppol-netwerk met het deelnemers-ID van de overheid in het `0208`-schema (KBO/BCE 10-cijferig ondernemingsnummer). Het Access Point stuurt de factuur automatisch door naar Mercurius. Geen Mercurius-specifiek indienpunt of API-sleutel is vereist.

---

## Architectuur

```
mcp-einvoicing-be/
├── src/
│   └── mcp_einvoicing_be/
│       ├── __init__.py
│       ├── server.py              # MCP-server-ingangspunt en toolregistratie
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
│       │   ├── peppol_bis_3.py    # Peppol BIS Billing 3.0 regels en aanpassings-ID's
│       │   ├── ubl.py             # UBL 2.1 namespaceconstanten en XML-hulpprogramma's
│       │   ├── pint_be.py         # PINT-BE placeholder (verwijderd in v0.3.1)
│       │   └── mercurius.py       # Mercurius-netwerkconfiguratie en laagregels
│       └── utils/
│           ├── __init__.py
│           └── helpers.py         # Btw-nummernormalisatie, datumopmaak, enz.
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

### Relatie met `mcp-einvoicing-core`

`mcp-einvoicing-core` biedt:
- Gedeelde UBL 2.1/2.3 XML-parsing- en serialisatieutilities
- EN 16931 basisvalidatieregels (syntaxis + semantiek)
- Peppol-netwerkclient (SMP-opzoeken, SML-resolutie)
- Gemeenschappelijke Pydantic-basismodellen (`BaseInvoice`, `BaseParty`, `BaseValidationResult`)

`mcp-einvoicing-be` voegt Belgie-specifieke logica toe:
- Peppol BIS 3.0 bedrijfsregelvalidatie (XPath-gebaseerd)
- Mercurius-netwerklaagregels voor B2G-facturatie
- BCE/KBO-ondernemingsdatabank-integratie
- Belgische btw-nummernormalisatie (BTW/TVA-formaat) en OGM/VCS controlegetal-validatie
- UBL 2.1 factuuranalyse voor verplichte ontvangst (Art. 13quater)
- `customizationID`- en `profileID`-waarden specifiek voor de Belgische Peppol-hoek

---

## Bijdragen

Bijdragen zijn welkom. Open een ticket (issue) om significante wijzigingen te bespreken voordat u een pull request indient.

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
uv run pytest
uv run ruff check src tests
uv run mypy src
```

Alle pull requests moeten:
- De volledige testsuite doorstaan (`pytest`)
- Linting doorstaan (`ruff check`)
- Typecontrole doorstaan (`mypy`)
- Tests bevatten of bijwerken voor elk gewijzigd gedrag
- Verwijzen naar de relevante regel-ID's bij het oplossen van een validatieprobleem

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor volledige richtlijnen.

---

## Andere MCP-servers voor e-facturatie

| Land | Server |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇧🇪 België | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brazilië | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 Frankrijk | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Duitsland | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italië | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇵🇱 Polen | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇪🇸 Spanje | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |

---

## Licentie

Dit project valt onder de **Apache 2.0**-licentie. Zie [LICENSE](LICENSE) voor meer informatie.

---

## Wijzigingslogboek

Zie [CHANGELOG.md](CHANGELOG.md) voor een volledige lijst van wijzigingen per versie.
