import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightLlmsTxt from "starlight-llms-txt";

export default defineConfig({
  site: "https://cmendezs.github.io",
  base: "/mcp-einvoicing-be/",
  integrations: [
    starlight({
      title: "mcp-einvoicing-be",
      description: "MCP server for Belgian electronic invoicing (Peppol BIS 3.0, UBL 2.1, PINT-EU, Mercurius)",
      customCss: ["./src/styles/docs-theme.css"],
      social: [
        { icon: "github", label: "GitHub", href: "https://github.com/cmendezs/mcp-einvoicing-be" },
      ],
      locales: {
        root: { label: "English", lang: "en" },
        fr: { label: "Français", lang: "fr" },
        nl: { label: "Nederlands", lang: "nl" },
      },
      sidebar: [
        { label: "Overview", link: "/" },
        { label: "Installation", link: "/installation/" },
        { label: "Configuration", link: "/configuration/" },
        { label: "Tools", link: "/tools/" },
        { label: "Standards", link: "/standards/" },
        { label: "Changelog", link: "/changelog/" },
      ],
      plugins: [
        starlightLlmsTxt({
          projectName: "mcp-einvoicing-be",
          description: "MCP server for Belgian electronic invoicing (Peppol BIS 3.0, UBL 2.1, PINT-EU, Mercurius)",
          customSets: [
            {
              label: "Key links",
              description: "PyPI and MCP registry entries",
              links: ["https://pypi.org/project/mcp-einvoicing-be/", "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.cmendezs/mcp-einvoicing-be"],
            },
          ],
        }),
      ],
    }),
  ],
});
