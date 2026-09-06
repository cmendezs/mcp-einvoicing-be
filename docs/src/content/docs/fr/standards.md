---
title: Normes prises en charge
description: Normes et profils implementes par mcp-einvoicing-be.
---

`mcp-einvoicing-be` est un serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) qui expose des outils pour la facturation electronique en Belgique. Il couvre l'ensemble de l'ecosysteme belge de facturation electronique : **Peppol BIS Billing 3.0**, **UBL 2.1**, et le reseau **Mercurius** pour la facturation du secteur public. Ce serveur fait partie de la famille `mcp-einvoicing-*` de serveurs specifiques a chaque pays, tous construits sur [`mcp-einvoicing-core`](https://github.com/cmendezs/mcp-einvoicing-core), qui fournit le moteur de validation partage, les abstractions UBL et les utilitaires reseau Peppol.
