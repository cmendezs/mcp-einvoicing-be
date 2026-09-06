---
title: Installation
description: Installer mcp-einvoicing-be avec uvx.
---

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
