"""Validation artefact registry for mcp-einvoicing-be.

Belgium does not publish Belgian-specific XSD or Schematron files.  The normative
validation artefacts are the standard OpenPeppol ones.  Run ``download.py`` to
fetch them from the official sources.

Sources:
- UBL 2.1 Invoice XSD: https://docs.oasis-open.org/ubl/os-UBL-2.1/
- Peppol BIS 3.0 Schematron: https://github.com/OpenPeppol/poacc-upgrade-3/
- PINT-BE Schematron (optional): https://github.com/OpenPeppol/pint-be/

Authority references (from Royal Decree of 8 July 2025, MB/BS N. 157):
- Art. 13ter: Peppol BIS 3.0 UBL is the mandatory base format.
- Validation artefacts: BOSA developer portal links to OpenPeppol artefacts.
"""

from pathlib import Path

SPECS_DIR = Path(__file__).parent
PEPPOL_BIS3_DIR = SPECS_DIR / "peppol_bis_3"
UBL_2_1_DIR = SPECS_DIR / "ubl_2_1"

__all__ = ["SPECS_DIR", "PEPPOL_BIS3_DIR", "UBL_2_1_DIR"]
