# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Francais](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Inleiding

`mcp-einvoicing-be` is een [MCP-server (Model Context Protocol)](https://modelcontextprotocol.io) die tools aanbiedt voor Belgische elektronische facturatie. Het dekt het volledige Belgische e-facturatie-ecosysteem: **Peppol BIS Billing 3.0**, **UBL 2.1**, en het **Mercurius**-netwerk voor facturatie aan de overheidssector. De server maakt deel uit van de `mcp-einvoicing-*`-familie van landspecifieke servers, allemaal gebouwd bovenop [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), dat de gedeelde validatie-engine, UBL-abstracties en Peppol-netwerkutilities levert.

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

## Configuratie

### Omgevingsvariabelen

| Variabele | Beschrijving | Standaard |
|---|---|---|
| `BCE_API_KEY` | API-sleutel voor de Belgische BCE/KBO-ondernemingsdatabank | — |
| `PEPPOL_ENV` | Peppol-omgeving: `production` of `test` | `production` |
| `PEPPOL_SML_URL` | Overschrijf de SML-opzoek-URL | (auto) |
| `EINVOICING_PEPPOL_CODELIST_DIR` | Lokale map met uw eigen kopie van de OpenPeppol eDEC-codelijsten, vereist door de codelijsttools (niet meegeleverd met dit pakket; zie de README van `mcp-einvoicing-core`) | — |
| `EINVOICING_EN16931_CODELIST_DIR` | Lokale map met uw eigen kopie van de CEF "Digital Building Blocks" EN 16931-semantische codelijsten, vereist door de EN 16931-codelijsttools (niet meegeleverd; zie de README van `mcp-einvoicing-core`) | — |
| `LOG_LEVEL` | Logboekniveau: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

De EUSR/TSR-rapportagetools en MLS-tools vereisen daarnaast de `[xslt2]`-extra (`pip install "mcp-einvoicing-be[xslt2]"`) voor Schematron-validatie.

## Integratie met Claude Desktop

Voeg de volgende configuratie toe aan uw `claude_desktop_config.json`-bestand:

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "uw-bce-api-sleutel",
        "PEPPOL_ENV": "production"
      }
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

## Integratie met Cursor

Cursor ondersteunt MCP-servers via stdio. Voeg de configuratie toe aan:
- **Algemeen** (alle projecten): `~/.cursor/mcp.json`
- **Project** (alleen deze repository): `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "uw-bce-api-sleutel",
        "PEPPOL_ENV": "production"
      }
    }
  }
}
```

Herlaad het Cursor-venster (`Ctrl+Shift+P` dan *Reload Window*) om de wijzigingen toe te passen.

## Integratie met Kiro

Kiro ondersteunt MCP-servers via een speciaal configuratiebestand. Twee niveaus zijn beschikbaar:
- **Algemeen** (alle projecten): `~/.kiro/settings/mcp.json`
- **Workspace** (alleen deze repository): `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "uw-bce-api-sleutel",
        "PEPPOL_ENV": "production"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Het bestand wordt automatisch opnieuw geladen bij het opslaan. U kunt de configuratie ook openen via het opdrachtenpalet (`Cmd+Shift+P` / `Ctrl+Shift+P`) en dan *MCP*.

> **Kiro-beveiligingstip**: gebruik in plaats van geheimen in platte tekst de syntax `"BCE_API_KEY": "${BCE_API_KEY}"`, Kiro lost shell-omgevingsvariabelen op bij het opstarten.

## Beschikbare tools

### `validate_invoice_be`

Valideert een UBL 2.1 XML-factuur. De profielen `peppol-bis-3`/`pint-eu` voeren echte Schematron-validatie uit tegen de CEN EN 16931-basisregels (~50 structurele/rekenkundige `BR-*`-regels, via het gebundelde basis-Schematron van `mcp-einvoicing-core` — zie CHANGELOG.md v0.8.0). Dit controleert niet de Peppol-specifieke overlayregels (geen bevestigd herdistributierecht van OpenPeppol); resultaten bevatten een expliciete `en16931-base-only`-scopewaarschuwing en mogen niet worden gelezen als volledige Peppol BIS3-conformiteit. Het profiel `mercurius` voert de Mercurius-specifieke laag uit (eindpuntschema, bestelreferentie) maar controleert geen basis EN 16931/Peppol BIS 3.0-conformiteit.

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

### Peppol-netwerktools

Peppol-deelnemersopzoeking, service-endpointopzoeking, een alleen-DNS-diagnose, AS4-verzending, Peppol Directory-zoeken en de OpenPeppol eDEC-codelijsttools worden geleverd door de gedeelde Peppol-tool-plugin van de core (`mcp_einvoicing_core.peppol.tools.register_peppol_tools`), gemonteerd in `server.py` met een Belgiëspecifieke identifier-adapter: een gewoon Belgisch btw-nummer (bijv. `0428759497` of `BE0428759497`) wordt genormaliseerd naar het Peppol-schema `0208:<cijfers>` (KBO/BCE-ondernemingsnummer); een reeds schema-gekwalificeerde identifier (bijv. `0208:0428759497`) blijft ongewijzigd.

`peppol_send` ondertekent uitgaande berichten sinds `mcp-einvoicing-core` v1.20.0 met een echte `wsse:Security`-handtekening (voorheen berekend en genegeerd — zie CHANGELOG.md v0.10.0).

| Tool | Beschrijving |
|---|---|
| `peppol_lookup_participant` | Controleert of een bedrijf geregistreerd is op het Peppol-netwerk; retourneert registratiestatus en ondersteunde documenttypes |
| `peppol_get_service_endpoint` | Haalt het AS4-endpoint op voor het documenttype van een deelnemer |
| `resolve_peppol_dns` | Alleen-DNS-diagnose (SML), onafhankelijk van SMP-bereikbaarheid |
| `peppol_send` | Verzendt een UBL/CII-factuur via AS4 |
| `peppol_directory_search` | Doorzoekt de publieke Peppol Directory op deelnemer, naam, land of documenttype |
| `list_participant_id_schemes`, `list_document_type_ids`, `list_process_ids`, `list_spis_use_case_ids` | OpenPeppol eDEC-codelijstopzoekingen (vereisen `EINVOICING_PEPPOL_CODELIST_DIR`) |
| `check_document_type_id_in_codelist`, `check_process_id_in_codelist`, `check_participant_id_scheme_in_codelist`, `get_peppol_codelist_version` | OpenPeppol eDEC-codelijstcontroles en versierapportage |

Zie de [README van `mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core#readme) voor volledige parameterdocumentatie van deze tools.

---

### Peppol-rapportage- en statustools

Toegevoegd in v0.10.0 via drie optionele core-plugins, onvoorwaardelijk gemonteerd in `server.py`. Elke tool geeft een duidelijke fout bij aanroep (niet bij registratie) als de bijbehorende extra of datamap ontbreekt.

| Tool | Plugin | Beschrijving |
|---|---|---|
| `validate_eusr_report` | `register_peppol_reporting_tools` | Valideert een End User Statistics Report (XSD, dan Schematron). Vereist de `[xslt2]`-extra. |
| `validate_tsr_report` | `register_peppol_reporting_tools` | Valideert een Transaction Statistics Report (XSD, dan Schematron). Vereist de `[xslt2]`-extra. |
| `validate_mls_message` | `register_peppol_mls_tools` | Valideert een Message Level Status-document (UBL `ApplicationResponse-2`-subset). Vereist de `[xslt2]`-extra. |
| `build_mls_message` | `register_peppol_mls_tools` | Bouwt een MLS-respons op documentniveau. Vereist de `[xslt2]`-extra. |
| 13 `list_*`/`check_*`-paren, `get_en16931_codelist_version` | `register_en16931_codelist_tools` | Opzoekingen/controles van EN 16931-semantische codelijsten (eenheden, btw-categorieën, enz.). Vereisen `EINVOICING_EN16931_CODELIST_DIR`. |

Zie de [README van `mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core#readme) voor volledige parameterdocumentatie van deze tools.

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

## B2G via Mercurius

Mercurius is het Belgische federale e-facturatieplatform voor de overheidssector. Het werkt als een **Peppol-netwerkontvanger**, niet als een aparte API. B2G-facturen worden ingediend via het standaard Peppol-netwerk met het deelnemers-ID van de overheid in het `0208`-schema (KBO/BCE 10-cijferig ondernemingsnummer). Het Access Point stuurt de factuur automatisch door naar Mercurius. Geen Mercurius-specifiek indienpunt of API-sleutel is vereist.

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
│       │   └── lookup.py          # lookup_vat_be, get_invoice_types_be
│       ├── models/
│       │   ├── __init__.py
│       │   ├── invoice.py         # InvoiceInput, InvoiceLine, ValidationResult
│       │   └── party.py           # Supplier, Customer, Address
│       ├── standards/
│       │   ├── __init__.py
│       │   ├── peppol_bis_3.py    # Peppol BIS Billing 3.0 regels en aanpassings-ID's
│       │   ├── ubl.py             # UBL 2.1 namespaceconstanten en XML-hulpprogramma's
│       │   ├── pint_be.py         # PINT-BE placeholder (verwijderd in v0.4.0)
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
- Mercurius-netwerklaagregelvalidatie (XPath-gebaseerd) voor B2G-facturatie
- BCE/KBO-ondernemingsdatabank-integratie
- Belgische btw-nummernormalisatie (BTW/TVA-formaat) en OGM/VCS controlegetal-validatie
- UBL 2.1 factuuranalyse voor verplichte ontvangst (Art. 13quater)
- `customizationID`- en `profileID`-waarden specifiek voor de Belgische Peppol-hoek

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

## Andere MCP-servers voor e-facturatie

| Land | Server |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇧🇪 België | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brazilië | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 Frankrijk | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Duitsland | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italië | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇲🇽 Mexico | [mcp-cfdi-mx](https://github.com/cmendezs/mcp-cfdi-mx) |
| 🇵🇱 Polen | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇸🇬 Singapore | [mcp-invoicenow-sg](https://github.com/cmendezs/mcp-invoicenow-sg) |
| 🇪🇸 Spanje | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |
| 🇦🇪 Verenigde Arabische Emiraten | [mcp-einvoicing-ae](https://github.com/cmendezs/mcp-einvoicing-ae) |

## Licentie

Dit project valt onder de **Apache 2.0**-licentie. Zie [LICENSE](LICENSE) voor meer informatie. Zie [CHANGELOG.md](CHANGELOG.md) voor de volledige versiegeschiedenis.
