---
title: Configuratie
description: Omgevingsvariabelen voor mcp-einvoicing-be.
---

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
