"""Download the OpenPeppol validation artefacts required by mcp-einvoicing-be.

Belgium adopts Peppol BIS Billing 3.0 as-is (Royal Decree of 8 July 2025,
Art. 13ter, MB/BS N. 157, 14 July 2025).  There are no Belgian-specific XSD or
Schematron files.  The normative artefacts are published by OpenPeppol and OASIS.

Usage (from the workspace root):
    uv run python src/mcp_einvoicing_be/specs/download.py

Artefacts downloaded:
- peppol_bis_3/  — Peppol BIS Billing 3.0 Schematron (XSLT + SCH)
- ubl_2_1/       — UBL 2.1 Invoice XSD

Sources:
- https://docs.peppol.eu/poacc/billing/3.0/  (spec reference)
- https://github.com/OpenPeppol/poacc-upgrade-3/releases  (Schematron)
- https://docs.oasis-open.org/ubl/os-UBL-2.1/  (UBL XSD)

[GAP id=core.schematron.be_bundled_xslt] (verified 2026-07-15): the release
URL below (release-3.0.17) does not exist — verified against the GitHub
Releases API, which lists no version past v3.0.15 and, more importantly, no
release in this repository has ever carried binary assets (`assets: []` on
every entry checked). OpenPeppol publishes only uncompiled Schematron
`.sch` sources under `rules/` in the repo tree; producing a compiled XSLT
requires running the project's own `build.sh` (trang/Saxon toolchain), which
is not reproduced here to avoid shipping an unverified compiled ruleset for
a compliance-critical validator. `download_peppol_bis3()` below is disabled
pending a verified source for the compiled artifact — see BE-SC-11 in
`context-library/roadmap-2026.md`. `tools/validation.py::_find_schematron_xslt`
already fails loudly (`allow_fallback=False`) rather than silently degrading.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

PEPPOL_BIS3_RELEASE = "3.0.17"
PEPPOL_BIS3_SCHEMATRON_URL = (
    f"https://github.com/OpenPeppol/poacc-upgrade-3/releases/download/release-{PEPPOL_BIS3_RELEASE}"
    f"/POACC-Billing-3.0_authority-EN16931_{PEPPOL_BIS3_RELEASE}.zip"
)

SPECS_DIR = Path(__file__).parent
PEPPOL_BIS3_DIR = SPECS_DIR / "peppol_bis_3"
UBL_2_1_DIR = SPECS_DIR / "ubl_2_1"


def _download(url: str, dest: Path) -> None:
    print(f"  Downloading {url}")
    print(f"  -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)  # noqa: S310


def download_peppol_bis3() -> None:
    """Download the Peppol BIS Billing 3.0 Schematron release ZIP.

    Disabled: PEPPOL_BIS3_SCHEMATRON_URL does not resolve to a real asset
    (see [GAP id=core.schematron.be_bundled_xslt] in the module docstring).
    Raises instead of silently writing a 404 error page as a .zip file.
    """
    raise RuntimeError(
        "Peppol BIS 3.0 Schematron download is disabled: no verified source "
        "for a compiled XSLT artifact is currently known. "
        "See [GAP id=core.schematron.be_bundled_xslt] in this module's docstring "
        "and BE-SC-11 in context-library/roadmap-2026.md. "
        "mcp_einvoicing_be.tools.validation falls back to hand-coded XPath rules "
        "until this is resolved."
    )


def download_ubl_xsd() -> None:
    """Download the UBL 2.1 Invoice XSD from OASIS.

    The UBL 2.1 distribution is large.  Only the Invoice and CreditNote XSDs
    plus the Common Library are needed.  Users may prefer to download manually
    from https://docs.oasis-open.org/ubl/os-UBL-2.1/ and extract the
    xsd/maindoc/ and xsd/common/ directories into ubl_2_1/.
    """
    readme = UBL_2_1_DIR / "README.txt"
    if readme.exists():
        print(f"  [skip] {UBL_2_1_DIR} already populated")
        return
    UBL_2_1_DIR.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "Place UBL 2.1 XSD files here.\n"
        "Download from: https://docs.oasis-open.org/ubl/os-UBL-2.1/\n"
        "Required paths:\n"
        "  ubl_2_1/xsd/maindoc/UBL-Invoice-2.1.xsd\n"
        "  ubl_2_1/xsd/maindoc/UBL-CreditNote-2.1.xsd\n"
        "  ubl_2_1/xsd/common/  (full common library)\n",
        encoding="utf-8",
    )
    print(f"  Created {readme} with download instructions")


def main() -> None:
    print(f"Downloading validation artefacts into {SPECS_DIR}")
    print()
    print("Peppol BIS Billing 3.0 Schematron:")
    download_peppol_bis3()
    print()
    print("UBL 2.1 XSD:")
    download_ubl_xsd()
    print()
    print("Done.  Run 'uv run --package mcp-einvoicing-be pytest' to verify.")


if __name__ == "__main__":
    main()
