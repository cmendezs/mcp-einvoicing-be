---
title: Installation
description: Install mcp-einvoicing-be with uvx.
---

### Requirements

- Python ≥ 3.11
- [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core) (installed automatically as a dependency)

### Using `uv` (recommended)

```bash
uv add mcp-einvoicing-be
```

### Using `pip`

```bash
pip install mcp-einvoicing-be
```

### From source

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
```
