# mcp-einvoicing-be 🇧🇪

[English](README.md) | [Francais](README.fr.md) | [Nederlands](README.nl.md)

<!-- mcp-name: io.github.cmendezs/mcp-einvoicing-be -->

[![PyPI version](https://badge.fury.io/py/mcp-einvoicing-be.svg)](https://badge.fury.io/py/mcp-einvoicing-be)
[![Python](https://img.shields.io/pypi/pyversions/mcp-einvoicing-be.svg)](https://pypi.org/project/mcp-einvoicing-be/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![mcp-einvoicing-be MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-einvoicing-be)

---

## Introduction

`mcp-einvoicing-be` est un serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) qui expose des outils pour la facturation electronique en Belgique. Il couvre l'ensemble de l'ecosysteme belge de facturation electronique : **Peppol BIS Billing 3.0**, **UBL 2.1/2.3**, l'extension **PINT-BE** (Banque Nationale de Belgique), et le reseau **Mercurius** pour la facturation du secteur public. Ce serveur fait partie de la famille `mcp-einvoicing-*` de serveurs specifiques a chaque pays, tous construits sur [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), qui fournit le moteur de validation partage, les abstractions UBL et les utilitaires reseau Peppol.

---

## Installation

### Prerequis

- Python ≥ 3.11
- [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core) (installe automatiquement en tant que dependance)

### Avec `uv` (recommande)

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

Ajoutez le serveur a la configuration de votre client MCP. Pour Claude Desktop, modifiez `claude_desktop_config.json` :

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

Pour une installation de developpement locale :

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

| Variable | Description | Par defaut |
|---|---|---|
| `BCE_API_KEY` | Cle API pour la base de donnees d'entreprises belge BCE/KBO | — |
| `PEPPOL_ENV` | Environnement Peppol : `production` ou `test` | `production` |
| `PEPPOL_SML_URL` | Remplacer l'URL de recherche SML | (auto) |
| `LOG_LEVEL` | Niveau de journalisation : `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## Outils disponibles

### `validate_invoice_be`

Valide une facture XML UBL 2.1 selon les regles metier belges (EN 16931 + PINT-BE ou Peppol BIS 3.0 + couche Mercurius).

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `xml` | `string` | oui | Contenu XML UBL 2.1 brut |
| `profile` | `string` | non | `peppol-bis-3` (par defaut), `pint-be`, ou `mercurius` |

Retourne un `ValidationResult` avec `valid`, `errors` et `warnings` (chacun portant l'identifiant de la regle echouee et un message lisible).

---

### `validate_pint_be`

Valide une facture selon les regles metier specifiques PINT-BE publiees par la Banque Nationale de Belgique (BNB). Applique les regles Schematron PINT-BE au-dessus de la base EN 16931.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `xml` | `string` | oui | Contenu XML UBL 2.1 brut |

---

### `generate_invoice_be`

Genere un document XML de facture electronique belge UBL 2.1 valide a partir de donnees structurees.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `invoice_data` | `object` | oui | Champs de la facture (voir le schema `InvoiceInput` ci-dessous) |
| `profile` | `string` | non | `peppol-bis-3` (par defaut) ou `pint-be` |

L'objet `InvoiceInput` prend en charge :

```json
{
  "invoice_number": "INV-2024-001",
  "issue_date": "2024-01-15",
  "due_date": "2024-02-14",
  "currency_code": "EUR",
  "supplier": { "name": "...", "vat_number": "BE0123456789", "address": {...} },
  "customer": { "name": "...", "vat_number": "BE0987654321", "address": {...} },
  "lines": [{ "description": "...", "quantity": 1, "unit_price": 100.00, "vat_rate": 21.0 }]
}
```

Retourne une chaine XML UBL 2.1.

---

### `transform_to_ubl`

Convertit une charge utile JSON de facture structuree en XML UBL 2.1 sans validation complete. Utile comme premiere etape avant la validation.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `data` | `object` | oui | Donnees de facture source (meme format que `InvoiceInput`) |

---

### `lookup_vat_be`

Recherche un numero d'entreprise belge (numero de TVA) dans la base de donnees publique BCE/KBO.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `vat_number` | `string` | oui | Numero de TVA/entreprise belge, par ex. `BE0123456789` ou `0123456789` |

Retourne le nom de l'entreprise, l'adresse enregistree, le statut juridique et les codes d'activite NACE.

---

### `check_peppol_participant_be`

Verifie si une entreprise belge est enregistree en tant que participant Peppol en interrogeant le reseau SMP/SML.

| Parametre | Type | Requis | Description |
|---|---|---|---|
| `identifier` | `string` | oui | Identifiant de participant Peppol (par ex. `0088:BE0123456789`) ou numero de TVA belge simple |

Retourne le statut d'enregistrement, les identifiants de type de document pris en charge et l'URL du point d'acces SMP.

---

### `get_invoice_types_be`

Retourne la liste des types de documents de facture electronique belges pris en charge (facture, note de credit, note de debit) avec leurs valeurs `customizationID` et `profileID` UBL pour chaque profil.

Aucun parametre d'entree requis.

---

## Architecture

```
mcp-einvoicing-be/
├── src/
│   └── mcp_einvoicing_be/
│       ├── __init__.py
│       ├── server.py              # Point d'entree du serveur MCP et enregistrement des outils
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
│       │   ├── peppol_bis_3.py    # Regles et ID de personnalisation Peppol BIS Billing 3.0
│       │   ├── ubl.py             # Constantes de namespace UBL 2.1 et utilitaires XML
│       │   ├── pint_be.py         # Regles Schematron PINT-BE (BNB)
│       │   └── mercurius.py       # Configuration reseau Mercurius et regles de couche
│       └── utils/
│           ├── __init__.py
│           └── helpers.py         # Normalisation de numero de TVA, formatage de dates, etc.
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
- Utilitaires partages d'analyse et de serialisation XML UBL 2.1/2.3
- Regles de validation de base EN 16931 (syntaxe + semantique)
- Client reseau Peppol (recherche SMP, resolution SML)
- Modeles de base Pydantic communs (`BaseInvoice`, `BaseParty`, `BaseValidationResult`)

`mcp-einvoicing-be` ajoute la logique specifique a la Belgique :
- Regles Schematron PINT-BE (publication BNB)
- Configuration du point d'acces du reseau Mercurius et regles de couche
- Integration de la base de donnees d'entreprises BCE/KBO
- Normalisation des numeros de TVA belges (format BTW/TVA)
- Valeurs `customizationID` et `profileID` specifiques au coin belge de Peppol

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
- Passer la verification de types (`mypy`)
- Inclure ou mettre a jour les tests pour tout comportement modifie
- Faire reference aux identifiants de regle concernes lors de la correction d'un probleme de validation

Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour les directives completes.

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

## Licence

Ce projet est sous licence **Apache 2.0**. Consultez [LICENSE](LICENSE) pour plus de details.

---

## Journal des modifications

Consultez [CHANGELOG.md](CHANGELOG.md) pour la liste complete des modifications par version.
