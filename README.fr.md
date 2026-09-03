# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Français](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Introduction

`mcp-einvoicing-be` est un serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) qui expose des outils pour la facturation electronique en Belgique. Il couvre l'ensemble de l'ecosysteme belge de facturation electronique : **Peppol BIS Billing 3.0**, **UBL 2.1**, et le reseau **Mercurius** pour la facturation du secteur public. Ce serveur fait partie de la famille `mcp-einvoicing-*` de serveurs specifiques a chaque pays, tous construits sur [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), qui fournit le moteur de validation partage, les abstractions UBL et les utilitaires reseau Peppol.

## Installation

### Prérequis

- Python ≥ 3.11
- [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core) (installé automatiquement en tant que dépendance)

### Avec `uv` (recommandé)

```bash
uv add mcp-einvoicing-be
```

### Avec `pip`

```bash
pip install mcp-einvoicing-be
```

### Depuis les sources

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
```

## Configuration

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

## Intégration Claude Desktop

Pour utiliser ce serveur avec Claude, ajoutez cette configuration dans votre fichier `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "votre-cle-api-bce",
        "PEPPOL_ENV": "production"
      }
    }
  }
}
```

Pour une installation de développement locale :

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

## Intégration Cursor

Cursor prend en charge les serveurs MCP en stdio. Ajoutez la configuration dans :
- **Global** (tous les projets) : `~/.cursor/mcp.json`
- **Projet** (ce dépôt uniquement) : `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "votre-cle-api-bce",
        "PEPPOL_ENV": "production"
      }
    }
  }
}
```

Rechargez la fenêtre Cursor (`Ctrl+Shift+P` puis *Reload Window*) pour prendre en compte les changements.

## Intégration Kiro

Kiro prend en charge les serveurs MCP via son fichier de configuration dédié. Deux niveaux sont disponibles :
- **Global** (tous les projets) : `~/.kiro/settings/mcp.json`
- **Workspace** (ce dépôt uniquement) : `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "einvoicing-be": {
      "command": "uvx",
      "args": ["mcp-einvoicing-be"],
      "env": {
        "BCE_API_KEY": "votre-cle-api-bce",
        "PEPPOL_ENV": "production"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Le fichier est rechargé automatiquement à la sauvegarde. Vous pouvez également ouvrir la configuration via la palette de commandes (`Cmd+Shift+P` / `Ctrl+Shift+P`) puis *MCP*.

> **Conseil sécurité Kiro** : plutôt que d'écrire les secrets en clair, utilisez la syntaxe `"BCE_API_KEY": "${BCE_API_KEY}"`, Kiro résout les variables d'environnement shell au démarrage.

## Outils disponibles

### `validate_invoice_be`

Valide une facture XML UBL 2.1. Les profils `peppol-bis-3`/`pint-eu` executent une validation Schematron reelle sur les regles de base CEN EN 16931 (~50 regles structurelles/arithmetiques `BR-*`, via le Schematron de base fourni par `mcp-einvoicing-core` — voir CHANGELOG.md v0.8.0). Cela ne verifie pas les regles de la couche specifique Peppol (aucun droit de redistribution confirme aupres d'OpenPeppol) ; les resultats portent un avertissement explicite de portee `en16931-base-only` et ne doivent pas etre lus comme une conformite Peppol BIS3 complete. Le profil `mercurius` applique la couche specifique Mercurius (schema de point de terminaison, reference de bon de commande) mais ne verifie pas la conformite EN 16931/Peppol BIS 3.0 de base.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `xml` | `string` | oui | Contenu XML UBL 2.1 brut |
| `profile` | `string` | non | `peppol-bis-3` (par defaut) ou `mercurius` |

Retourne un `ValidationResult` avec `valid`, `errors` et `warnings` (chacun portant l'identifiant de la règle échouée et un message lisible).

---

### `generate_invoice_be`

Génère un document XML de facture électronique belge UBL 2.1 valide à partir de données structurées.

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `invoice_data` | `object` | oui | Champs de la facture (voir le schéma `InvoiceInput` ci-dessous) |
| `profile` | `string` | non | `peppol-bis-3` (par defaut) |

L'objet `InvoiceInput` prend en charge :

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

Retourne une chaîne XML UBL 2.1.

---

### `transform_to_ubl`

Convertit une charge utile JSON de facture structurée en XML UBL 2.1 sans validation complète. Utile comme première étape avant la validation.

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `data` | `object` | oui | Données de facture source (même format que `InvoiceInput`) |

---

### `lookup_vat_be`

Recherche un numéro d'entreprise belge (numéro de TVA) dans la base de données publique BCE/KBO.

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `vat_number` | `string` | oui | Numéro de TVA/entreprise belge, par ex. `BE0428759497` ou `0123456789` |

Retourne le nom de l'entreprise, l'adresse enregistrée, le statut juridique et les codes d'activité NACE.

---

### Outils du réseau Peppol

La recherche de participant Peppol, la recherche de point de service, un diagnostic DNS seul, l'envoi AS4, la recherche dans l'annuaire Peppol et les outils de listes de codes eDEC OpenPeppol sont fournis par le plugin d'outils Peppol partagé du core (`mcp_einvoicing_core.peppol.tools.register_peppol_tools`), monté dans `server.py` avec un adaptateur d'identifiant spécifique à la Belgique : un numéro de TVA belge simple (par ex. `0428759497` ou `BE0428759497`) est normalisé vers le schéma Peppol `0208:<chiffres>` (numéro d'entreprise KBO/BCE) ; un identifiant déjà qualifié par schéma (par ex. `0208:0428759497`) passe inchangé.

`peppol_send` signe désormais les messages sortants avec une véritable signature `wsse:Security` depuis `mcp-einvoicing-core` v1.20.0 (auparavant calculée puis ignorée — voir CHANGELOG.md v0.10.0).

| Outil | Description |
|---|---|
| `peppol_lookup_participant` | Vérifie si une entreprise est enregistrée sur le réseau Peppol ; retourne le statut d'enregistrement et les types de documents pris en charge |
| `peppol_get_service_endpoint` | Récupère le point de terminaison AS4 pour le type de document d'un participant |
| `resolve_peppol_dns` | Diagnostic DNS seul (SML), indépendant de l'accessibilité SMP |
| `peppol_send` | Transmet une facture UBL/CII via AS4 |
| `peppol_directory_search` | Recherche dans l'annuaire public Peppol par participant, nom, pays ou type de document |
| `list_participant_id_schemes`, `list_document_type_ids`, `list_process_ids`, `list_spis_use_case_ids` | Recherches dans les listes de codes eDEC OpenPeppol (nécessitent `EINVOICING_PEPPOL_CODELIST_DIR`) |
| `check_document_type_id_in_codelist`, `check_process_id_in_codelist`, `check_participant_id_scheme_in_codelist`, `get_peppol_codelist_version` | Vérifications de listes de codes eDEC OpenPeppol et rapport de version |

Voir le [README de `mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core#readme) pour la documentation complète des paramètres de ces outils.

---

### Outils de rapport et de statut Peppol

Ajoutés en v0.10.0 via trois plugins core optionnels, montés inconditionnellement dans `server.py`. Chacun renvoie une erreur claire à l'appel (pas à l'enregistrement) si son extra ou son répertoire de données est manquant.

| Outil | Plugin | Description |
|---|---|---|
| `validate_eusr_report` | `register_peppol_reporting_tools` | Valide un End User Statistics Report (XSD, puis Schematron). Nécessite l'extra `[xslt2]`. |
| `validate_tsr_report` | `register_peppol_reporting_tools` | Valide un Transaction Statistics Report (XSD, puis Schematron). Nécessite l'extra `[xslt2]`. |
| `validate_mls_message` | `register_peppol_mls_tools` | Valide un document Message Level Status (sous-ensemble UBL `ApplicationResponse-2`). Nécessite l'extra `[xslt2]`. |
| `build_mls_message` | `register_peppol_mls_tools` | Construit une réponse MLS au niveau du document. Nécessite l'extra `[xslt2]`. |
| 13 paires `list_*`/`check_*`, `get_en16931_codelist_version` | `register_en16931_codelist_tools` | Recherches/vérifications des listes de codes sémantiques EN 16931 (unités, catégories de TVA, etc.). Nécessitent `EINVOICING_EN16931_CODELIST_DIR`. |

Voir le [README de `mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core#readme) pour la documentation complète des paramètres de ces outils.

---

### `parse_ubl_invoice_be`

Analyse une facture XML UBL 2.1 (Peppol BIS 3.0) en un dictionnaire structure. Repond a l'obligation de reception obligatoire de l'Art. 13quater de l'AR no. 1.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `xml_content` | `string` | oui | Contenu XML UBL 2.1 brut de la facture |

Retourne `{"success": true, "invoice": {...}, "warnings": []}` en cas de succes, ou `{"success": false, "error": "..."}` en cas d'echec.

---

### `get_invoice_types_be`

Retourne la liste des types de documents de facture electronique belges pris en charge (facture, note de credit, note de debit) avec leurs valeurs `customizationID` et `profileID` UBL pour chaque profil.

Aucun parametre d'entree requis.

## B2G via Mercurius

Mercurius est la plateforme belge de facturation electronique pour le secteur public federal. Elle fonctionne comme un **recepteur du reseau Peppol**, et non comme une API separee. Les factures B2G sont soumises via le reseau Peppol standard en utilisant l'identifiant de participant de l'autorite dans le schema `0208` (numero d'entreprise KBO/BCE a 10 chiffres). Le Point d'Acces achemine automatiquement la facture vers Mercurius. Aucun point de soumission specifique a Mercurius ni cle API n'est requis.

## Architecture

```
mcp-einvoicing-be/
├── src/
│   └── mcp_einvoicing_be/
│       ├── __init__.py
│       ├── server.py              # Point d'entrée du serveur MCP et enregistrement des outils
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
│       │   ├── peppol_bis_3.py    # Règles et ID de personnalisation Peppol BIS Billing 3.0
│       │   ├── ubl.py             # Constantes de namespace UBL 2.1 et utilitaires XML
│       │   ├── pint_be.py         # PINT-BE placeholder (supprime en v0.4.0)
│       │   └── mercurius.py       # Configuration réseau Mercurius et règles de couche
│       └── utils/
│           ├── __init__.py
│           └── helpers.py         # Normalisation de numéro de TVA, formatage de dates, etc.
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

### Relation avec `mcp-einvoicing-core`

`mcp-einvoicing-core` fournit :
- Utilitaires partagés d'analyse et de sérialisation XML UBL 2.1/2.3
- Règles de validation de base EN 16931 (syntaxe + sémantique)
- Client réseau Peppol (recherche SMP, résolution SML)
- Modèles de base Pydantic communs (`BaseInvoice`, `BaseParty`, `BaseValidationResult`)

`mcp-einvoicing-be` ajoute la logique specifique a la Belgique :
- Validation des regles de couche Mercurius (basee sur XPath) pour la facturation B2G
- Integration de la base de donnees d'entreprises BCE/KBO
- Normalisation des numeros de TVA belges (format BTW/TVA) et validation des digits de controle OGM/VCS
- Analyse de factures UBL 2.1 pour la reception obligatoire (Art. 13quater)
- Valeurs `customizationID` et `profileID` specifiques au coin belge de Peppol

## Contribuer

Les contributions sont les bienvenues. Veuillez ouvrir un ticket (issue) pour discuter des changements significatifs avant de soumettre une pull request.

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
uv run pytest
uv run ruff check src tests
uv run mypy src
```

Toutes les pull requests doivent :
- Passer l'ensemble de la suite de tests (`pytest`)
- Passer le linting (`ruff check`)
- Passer la vérification de types (`mypy`)
- Inclure ou mettre à jour les tests pour tout comportement modifié
- Faire référence aux identifiants de règle concernés lors de la correction d'un problème de validation

Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour les directives complètes.

## Autres serveurs MCP de facturation électronique

| Pays | Serveur |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇧🇪 Belgique | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brésil | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 France | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Allemagne | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italie | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇲🇽 Mexique | [mcp-cfdi-mx](https://github.com/cmendezs/mcp-cfdi-mx) |
| 🇵🇱 Pologne | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇸🇬 Singapour | [mcp-invoicenow-sg](https://github.com/cmendezs/mcp-invoicenow-sg) |
| 🇪🇸 Espagne | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |
| 🇦🇪 Émirats arabes unis | [mcp-einvoicing-ae](https://github.com/cmendezs/mcp-einvoicing-ae) |

## Licence

Ce projet est sous licence **Apache 2.0**. Consultez [LICENSE](LICENSE) pour plus de détails. Pour l'historique complet des versions, voir [CHANGELOG.md](CHANGELOG.md).
