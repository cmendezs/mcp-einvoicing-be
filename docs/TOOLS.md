# Tool reference — `mcp_einvoicing_be`

This file is generated from the MCP server's tool registry by `scripts/gen_tool_reference.py`. Do not edit it by hand; run the script instead.

**Tools:** 18

## `check_document_type_id_in_codelist`

Check whether a (scheme, value) pair is a recognized Peppol document type identifier.

Requires EINVOICING_PEPPOL_CODELIST_DIR (see `list_participant_id_schemes`).
Searches all entries regardless of state, so a historical (deprecated
or removed) document type is still reported as found.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `scheme` | string | yes |  |  |
| `value` | string | yes |  |  |

## `check_participant_id_scheme_in_codelist`

Check whether a 4-digit ISO 6523 ICD code (e.g. "0208") is a recognized Peppol scheme.

Requires EINVOICING_PEPPOL_CODELIST_DIR (see `list_participant_id_schemes`).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `icd` | string | yes |  |  |

## `check_process_id_in_codelist`

Check whether a (scheme, value) pair is a recognized Peppol process identifier.

Requires EINVOICING_PEPPOL_CODELIST_DIR (see `list_participant_id_schemes`).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `scheme` | string | yes |  |  |
| `value` | string | yes |  |  |

## `generate_invoice_be`

Generate a valid UBL 2.1 Belgian e-invoice XML document from structured data.

Applies the correct customizationID and profileID for the selected Belgian
Peppol profile. The output XML is ready for submission to the Peppol network
or the Mercurius platform.

Returns a dict with:
- ``xml``: the generated UBL 2.1 XML string
- ``customization_id``: the UBL customizationID applied (BT-24)
- ``profile_id``: the UBL profileID applied (BT-23)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `invoice_data` | object | yes |  | Invoice fields matching the BEInvoice schema |
| `profile` | string | no | `'peppol-bis-3'` | Target profile: 'peppol-bis-3' (default) or 'pint-eu' (EU PINT v1.0.1) |

## `get_invoice_types_be`

Return the supported Belgian e-invoice document types.

Includes invoice (380), credit note (381), and debit note (383) with their
UBL ``customizationID`` and ``profileID`` values for each supported profile
(Peppol BIS Billing 3.0).

_No parameters._

## `get_peppol_codelist_version`

Report the OpenPeppol eDEC code list release version(s) currently configured locally.

_No parameters._

## `list_document_type_ids`

List Peppol document type identifiers from the OpenPeppol eDEC code list.

Requires EINVOICING_PEPPOL_CODELIST_DIR (see `list_participant_id_schemes`).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `active_only` | boolean | no | `True` | When True (default), omit deprecated/removed entries. |

## `list_participant_id_schemes`

List Peppol participant identifier (ICD) schemes from the OpenPeppol eDEC code list.

Requires EINVOICING_PEPPOL_CODELIST_DIR to point at a local copy of
the eDEC "Participant Identifier Schemes" GeneriCode export (not
bundled with this package, no confirmed redistribution rights, see
`mcp_einvoicing_core.peppol.codelists` module docstring).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `active_only` | boolean | no | `True` | When True (default), omit deprecated/removed entries. |

## `list_process_ids`

List Peppol process identifiers from the OpenPeppol eDEC code list.

Requires EINVOICING_PEPPOL_CODELIST_DIR (see `list_participant_id_schemes`).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `active_only` | boolean | no | `True` | When True (default), omit deprecated/removed entries. |

## `list_spis_use_case_ids`

List Peppol SPIS use case identifiers from the OpenPeppol eDEC code list.

Requires EINVOICING_PEPPOL_CODELIST_DIR (see `list_participant_id_schemes`).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `active_only` | boolean | no | `True` | When True (default), omit deprecated/removed entries. |

## `lookup_vat_be`

Look up a Belgian enterprise number against the BCE/KBO public database.

Accepts the number with or without the 'BE' prefix and with or without
dots/spaces.  Returns the enterprise's legal name, registered address,
legal form, status, and NACE activity codes.

Optionally set the ``BCE_API_KEY`` environment variable for authenticated
access to the full BCE dataset.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `vat_number` | string | yes |  | Belgian VAT/enterprise number, e.g. 'BE0123456789' or '0123456789' |

## `parse_ubl_invoice_be`

Parse a UBL 2.1 XML invoice into a structured dict.

Accepts a Peppol BIS Billing 3.0 or EU PINT v1.0.1 UBL 2.1 document and
extracts the EN 16931 core field set (header, parties, lines, tax breakdown,
totals) plus Belgian extensions (OGM/VCS reference, endpoint scheme info).

Returns ``{"success": true, "invoice": {...}, "be_extensions": {...}, "warnings": []}``
on success, or ``{"success": false, "error": "..."}`` on parse failure.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `xml_content` | string | yes |  | Raw UBL 2.1 XML invoice content (Peppol BIS 3.0) |

## `peppol_get_service_endpoint`

Fetch the AS4 endpoint for a Peppol participant's document type.

Resolves the SMP hostname via DNS, then fetches service metadata for
*document_type_id*. If the SMP returns a redirect, the result's
`redirect_url` is set and `endpoint_url` is None; callers must not
follow more than one redirect hop (SMP 1.4.0 §3.2).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `identifier` | string | yes |  | Peppol participant ID or adaptable national identifier. |
| `document_type_id` | string | no | `'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1'` | Peppol document type identifier URN (default: BIS Billing 3.0 invoice). |
| `environment` | string | no | `'production'` | "production" or "test". |

## `peppol_lookup_participant`

Check whether a business is registered on the Peppol network.

Performs a DNS-over-HTTPS U-NAPTR lookup followed by an SMP
service-group request to determine registration status and the list
of supported document type identifiers.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `identifier` | string | yes |  | Peppol participant ID ("<scheme>:<value>") or a bare national identifier this server knows how to adapt (e.g. a VAT number, if a national identifier adapter is configured). |
| `environment` | string | no | `'production'` | "production" or "test". |

## `peppol_send`

Send a UBL/CII invoice to a Peppol participant via AS4.

Looks up the recipient's AS4 endpoint (SMP), builds the ebMS3/AS4
envelope, and transmits it using the supplied signing credentials.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `invoice_xml_base64` | string | yes |  | Base64-encoded UBL or CII invoice XML. |
| `recipient_identifier` | string | yes |  | Peppol participant ID or adaptable national identifier of the receiver. |
| `sender_id` | string | yes |  | Peppol AP identifier of the sender. |
| `certificate_path` | string | yes |  | Path to the PEM-encoded signing certificate. |
| `private_key_path` | string | yes |  | Path to the PEM-encoded private key. |
| `private_key_password` | string | no | `''` | Optional password for the private key. |
| `document_type_id` | string | no | `'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1'` | Peppol document type identifier URN (default: BIS Billing 3.0 invoice). |
| `environment` | string | no | `'test'` | "production" or "test". |

## `resolve_peppol_dns`

Resolve the SMP hostname for a Peppol participant via DNS only.

Performs the raw U-NAPTR (SML) lookup without fetching the SMP
service group, useful for diagnosing whether a participant is
registered in the SML independently of SMP reachability.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `identifier` | string | yes |  | Peppol participant ID or adaptable national identifier. |
| `environment` | string | no | `'production'` | "production" or "test". |

## `transform_to_ubl`

Convert a structured JSON invoice payload to UBL 2.1 XML.

Unlike ``generate_invoice_be``, this tool does not run validation after
transformation. Intended as a conversion step when the caller will validate
separately or submit directly to a platform that performs its own validation.

Returns a dict with:
- ``xml``: the generated UBL 2.1 XML string
- ``warnings``: list of non-fatal issues detected during transformation

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `data` | object | yes |  | Source invoice data matching the BEInvoice schema |

## `validate_invoice_be`

Validate a UBL 2.1 XML invoice against Belgian business rules.

For 'peppol-bis-3'/'pint-eu': checks the CEN EN16931 base rules
(structural + arithmetic/totals, ~50 BR-* rules) via a compiled
Schematron. Does NOT check the Peppol-specific overlay (profile ID
registration, EndpointID scheme, narrowed code lists) — the result's
metadata.scope is "en16931-base-only", and a warning is included. This
is not a full Peppol BIS3 conformance check; a document that passes
may still be rejected by a real Peppol Access Point. See
context-library/decisions/peppol-schematron-artifact.md for why.
For 'mercurius': applies the Mercurius-specific overlay rules only
(endpoint scheme, PO reference) — also not full EN16931/Peppol base
compliance.
Returns a structured result with per-rule error and warning messages.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `xml` | string | yes |  | Raw UBL 2.1 XML invoice content |
| `profile` | string | no | `'peppol-bis-3'` | Validation profile: 'peppol-bis-3' (default), 'pint-eu', or 'mercurius' |
