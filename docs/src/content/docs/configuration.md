---
title: Configuration
description: Environment variables for mcp-einvoicing-be.
---

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
