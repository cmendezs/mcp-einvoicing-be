---
title: Configuration
description: Variables d'environnement pour mcp-einvoicing-be.
---

### Variables d'environnement

| Variable | Description | Par défaut |
|---|---|---|
| `BCE_API_KEY` | Clé API pour la base de données d'entreprises belge BCE/KBO | - |
| `PEPPOL_ENV` | Environnement Peppol : `production` ou `test` | `production` |
| `PEPPOL_SML_URL` | Remplacer l'URL de recherche SML | (auto) |
| `EINVOICING_PEPPOL_CODELIST_DIR` | Répertoire local contenant votre propre copie des listes de codes eDEC OpenPeppol, requis par les outils de listes de codes (non fourni avec ce paquet ; voir le README de `mcp-einvoicing-core`) | — |
| `EINVOICING_EN16931_CODELIST_DIR` | Répertoire local contenant votre propre copie des listes de codes sémantiques EN 16931 du CEF « Digital Building Blocks », requis par les outils de listes de codes EN 16931 (non fourni ; voir le README de `mcp-einvoicing-core`) | — |
| `LOG_LEVEL` | Niveau de journalisation : `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

Les outils de rapport EUSR/TSR et MLS nécessitent en plus l'extra `[xslt2]` (`pip install "mcp-einvoicing-be[xslt2]"`) pour la validation Schematron.
