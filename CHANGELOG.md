# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial scaffolding and project structure
- `validate_invoice_be` tool: UBL 2.1 validation against Peppol BIS 3.0, PINT-BE, and Mercurius profiles
- `validate_pint_be` tool: PINT-BE specific Schematron rules (NBB)
- `generate_invoice_be` tool: UBL 2.1 invoice generation from structured data
- `transform_to_ubl` tool: JSON-to-UBL 2.1 XML transformation
- `lookup_vat_be` tool: BCE/KBO enterprise number lookup
- `check_peppol_participant_be` tool: Peppol SMP/SML participant lookup
- `get_invoice_types_be` tool: supported Belgian e-invoice document types

---

## [0.1.0] — TBD

_Initial release._

[Unreleased]: https://github.com/cmendezs/mcp-einvoicing-be/compare/HEAD
