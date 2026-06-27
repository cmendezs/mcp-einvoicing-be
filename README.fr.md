# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Français](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Introduction

`mcp-einvoicing-be` est un serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) qui expose des outils pour la facturation électronique en Belgique. Il couvre l'ensemble de l'écosystème belge de facturation électronique : **Peppol BIS Billing 3.0**, **UBL 2.1/2.3**, l'extension **PINT-BE** (Banque Nationale de Belgique), et le réseau **Mercurius** pour la facturation du secteur public. Ce serveur fait partie de la famille `mcp-einvoicing-*` de serveurs spécifiques à chaque pays, tous construits sur [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), qui fournit le moteur de validation partagé, les abstractions UBL et les utilitaires réseau Peppol.

---

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

---

## Configuration

Ajoutez le serveur à la configuration de votre client MCP. Pour Claude Desktop, modifiez `claude_desktop_config.json` :

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

### Variables d'environnement

| Variable | Description | Par défaut |
|---|---|---|
| `BCE_API_KEY` | Clé API pour la base de données d'entreprises belge BCE/KBO | - |
| `PEPPOL_ENV` | Environnement Peppol : `production` ou `test` | `production` |
| `PEPPOL_SML_URL` | Remplacer l'URL de recherche SML | (auto) |
| `LOG_LEVEL` | Niveau de journalisation : `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## Outils disponibles

### `validate_invoice_be`

Valide une facture XML UBL 2.1 selon les règles métier belges (EN 16931 + PINT-BE ou Peppol BIS 3.0 + couche Mercurius).

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `xml` | `string` | oui | Contenu XML UBL 2.1 brut |
| `profile` | `string` | non | `peppol-bis-3` (par défaut), `pint-be`, ou `mercurius` |

Retourne un `ValidationResult` avec `valid`, `errors` et `warnings` (chacun portant l'identifiant de la règle échouée et un message lisible).

---

### `validate_pint_be`

Valide une facture selon les règles métier spécifiques PINT-BE publiées par la Banque Nationale de Belgique (BNB). Applique les règles Schematron PINT-BE au-dessus de la base EN 16931.

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `xml` | `string` | oui | Contenu XML UBL 2.1 brut |

---

### `generate_invoice_be`

Génère un document XML de facture électronique belge UBL 2.1 valide à partir de données structurées.

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `invoice_data` | `object` | oui | Champs de la facture (voir le schéma `InvoiceInput` ci-dessous) |
| `profile` | `string` | non | `peppol-bis-3` (par défaut) ou `pint-be` |

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

### `check_peppol_participant_be`

Vérifie si une entreprise belge est enregistrée en tant que participant Peppol en interrogeant le réseau SMP/SML.

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `identifier` | `string` | oui | Identifiant de participant Peppol (par ex. `0088:BE0428759497`) ou numéro de TVA belge simple |

Retourne le statut d'enregistrement, les identifiants de type de document pris en charge et l'URL du point d'accès SMP.

---

### `get_invoice_types_be`

Retourne la liste des types de documents de facture électronique belges pris en charge (facture, note de crédit, note de débit) avec leurs valeurs `customizationID` et `profileID` UBL pour chaque profil.

Aucun paramètre d'entrée requis.

---

## Architecture

```
mcp-einvoicing-be/
├── src/
│   └── mcp_einvoicing_be/
│       ├── __init__.py
│       ├── server.py              # Point d'entrée du serveur MCP et enregistrement des outils
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── validation.py      # validate_invoice_be, validate_pint_be
│       │   ├── generation.py      # generate_invoice_be
│       │   ├── transformation.py  # transform_to_ubl
│       │   └── lookup.py          # lookup_vat_be, check_peppol_participant_be, get_invoice_types_be
│       ├── models/
│       │   ├── __init__.py
│       │   ├── invoice.py         # InvoiceInput, InvoiceLine, ValidationResult
│       │   └── party.py           # Supplier, Customer, Address
│       ├── standards/
│       │   ├── __init__.py
│       │   ├── peppol_bis_3.py    # Règles et ID de personnalisation Peppol BIS Billing 3.0
│       │   ├── ubl.py             # Constantes de namespace UBL 2.1 et utilitaires XML
│       │   ├── pint_be.py         # Règles Schematron PINT-BE (BNB)
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

`mcp-einvoicing-be` ajoute la logique spécifique à la Belgique :
- Règles Schematron PINT-BE (publication BNB)
- Configuration du point d'accès du réseau Mercurius et règles de couche
- Intégration de la base de données d'entreprises BCE/KBO
- Normalisation des numéros de TVA belges (format BTW/TVA)
- Valeurs `customizationID` et `profileID` spécifiques au coin belge de Peppol

---

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

---

## Autres serveurs MCP de facturation électronique

| Pays | Serveur |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇧🇪 Belgique | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brésil | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 France | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Allemagne | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italie | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇵🇱 Pologne | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇪🇸 Espagne | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |

---

## Licence

Ce projet est sous licence **Apache 2.0**. Consultez [LICENSE](LICENSE) pour plus de détails.

---

## Journal des modifications

Consultez [CHANGELOG.md](CHANGELOG.md) pour la liste complète des modifications par version.
