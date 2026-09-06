---
title: Installatie
description: Installeer mcp-einvoicing-be met uvx.
---

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
