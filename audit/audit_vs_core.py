"""Pre-publish audit: verify mcp-einvoicing-be coherence against mcp-einvoicing-core.

Run standalone (from the workspace root):
    uv run python mcp-einvoicing-be/audit/audit_vs_core.py
    uv run python mcp-einvoicing-be/audit/audit_vs_core.py --output mcp-einvoicing-be/audit/report.json
    uv run python mcp-einvoicing-be/audit/audit_vs_core.py --fail-on blocking

Exit codes:
    0  All checks passed
    1  Warnings only (non-blocking)
    2  Blocking failures found

CHECK 1 and CHECK 4 are delegated to mcp_einvoicing_core.audit.
CHECK 2 (tool registry), CHECK 3 (BEInvoice field alignment), and CHECK 5
(BE-specific structural) are implemented here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mcp_einvoicing_core.audit import (
    SEVERITY_BLOCKING,
    SEVERITY_OK,
    SEVERITY_WARNING,
    AuditReport,
    CheckFinding,
    CheckResult,
    _try_import,
    make_report,
    parse_audit_args,
    render_summary_table,
    run_check_core_coverage,
    run_check_version_compatibility,
)

# ---------------------------------------------------------------------------
# CHECK 1 configuration — country-specific constants
# ---------------------------------------------------------------------------

# Peppol BIS 3.0 / PINT-BE is EN 16931 family.
# BE country audit 2026-05 (finding BE-SC-2) confirms:
#   - BEInvoice currently extends InvoiceDocument — WRONG BASE for PINT-BE pathway.
#   - BEInvoice(EN16931Invoice) must be scaffolded before this constant can be set True.
# Set to None to skip the canonical tree check until BEInvoice is migrated (Sprint 2).
# [GAP id=BE-SC-2]
_IS_EN16931_FAMILY: bool | None = None
_PRIMARY_INVOICE_CLASS: tuple[str, str] | None = None

_INTENTIONAL_OVERRIDES: dict[str, set[str]] = {
    "mcp_einvoicing_core.base_server": {
        # OVERRIDE-REASON: BE has no document parser class; InvoiceDocument.model_validate() is used inline in tool handlers
        "BaseDocumentParser",
        # OVERRIDE-REASON: Peppol BIS 3.0 is push-only submission; no session-based lifecycle API is required for BE
        "BaseLifecycleManager",
        # OVERRIDE-REASON: party validation is performed inline in BE tool handlers, not via the ABC party validator pattern
        "BasePartyValidator",
        # OVERRIDE-REASON: Peppol submission returns a plain dict; SubmitResult typed model not used in BE
        "SubmitResult",
        # OVERRIDE-REASON: TaxIdValidationResult not yet returned by BE tax-ID validation helpers; tracked as future work
        "TaxIdValidationResult",
        # OVERRIDE-REASON: BE uses EInvoicingMCPServer; raw FastMCP handle not needed in package code
        "FastMCP",
        # OVERRIDE-REASON: stdlib re-export; BE imports abstractmethod from abc directly
        "abstractmethod",
        # OVERRIDE-REASON: stdlib re-export; BE imports ABC from abc directly
        "ABC",
        # OVERRIDE-REASON: stdlib re-export; not used in BE package code
        "Any",
        # OVERRIDE-REASON: third-party re-export; pydantic BaseModel imported from pydantic directly in BE models
        "BaseModel",
        # OVERRIDE-REASON: third-party re-export; pydantic Field imported from pydantic directly in BE models
        "Field",
        # OVERRIDE-REASON: assert_not_read_only is an internal server guard not needed in BE tool handlers
        "assert_not_read_only",
        # OVERRIDE-REASON: scrub is a prompt-injection sanitiser helper; BE does not apply it at the tool boundary yet (BE-SH-1)
        "scrub",
    },
    "mcp_einvoicing_core.digital_signature": {
        # OVERRIDE-REASON: Peppol AS4 transport handles its own signing; XAdES-EPES envelope signing is not required for PINT-BE
        "BaseDocumentSigner",
        # OVERRIDE-REASON: XAdES signing config and signer not needed; Peppol BIS 3.0 uses AS4 transport-level signatures
        "XAdESSignerConfig",
        "XAdESEPESSigner",
        # OVERRIDE-REASON: stdlib/third-party re-exports in digital_signature; BE imports these from source directly
        "ABC",
        "abstractmethod",
        "dataclass",
        "datetime",
        "field",
        "safe_fromstring",
        "timezone",
    },
    "mcp_einvoicing_core.download_rules": {
        # OVERRIDE-REASON: BE spec artefacts (Schematron, XSDs) are bundled manually into specs/; the artefact-download framework is not used
        "DownloadSpec",
        "download_artefacts",
        # OVERRIDE-REASON: download_rules CLI entry point; not called from BE package code
        "main",
        # OVERRIDE-REASON: stdlib/third-party re-exports in download_rules; BE imports from source directly
        "Path",
        "dataclass",
        "field",
        "entry_points",
    },
    "mcp_einvoicing_core.en16931": {
        # OVERRIDE-REASON: BEInvoice(InvoiceDocument) pending migration to EN16931Invoice (BE-SC-2 Sprint 2);
        # EN16931 model tree not yet adopted by the BE package [GAP id=BE-SC-2]
        "EN16931Invoice",
        "EN16931Address",
        "EN16931Party",
        "EN16931Tax",
        "EN16931AllowanceCharge",
        "EN16931LineItem",
        "EN16931PaymentMeans",
        # OVERRIDE-REASON: stdlib/third-party re-exports in en16931; BE imports from pydantic/stdlib directly
        "BaseModel",
        "Decimal",
        "Field",
        "date",
        "field_validator",
        "model_validator",
    },
    "mcp_einvoicing_core.exceptions": {
        # OVERRIDE-REASON: BE raises specific exception subclasses directly; EInvoicingError base not re-raised at tool layer
        "EInvoicingError",
        # OVERRIDE-REASON: party validation in BE is inline and returns structured error dicts; PartyValidationError not raised
        "PartyValidationError",
        # OVERRIDE-REASON: UBL 2.1 validation in BE uses Schematron, not XSD; XSDValidationError is not applicable
        "XSDValidationError",
        # OVERRIDE-REASON: BE surfaces ValidationError from core; SchematronValidationError is not re-raised to the tool layer
        "SchematronValidationError",
        # OVERRIDE-REASON: Peppol SMP and BCE/KBO are public unauthenticated endpoints; AuthenticationError is not raised in BE
        "AuthenticationError",
    },
    "mcp_einvoicing_core.http_client": {
        # OVERRIDE-REASON: BE has no OAuth2 token exchange; Peppol SMP and BCE/KBO are public endpoints not requiring OAuth
        "OAuthConfig",
        "OAuthValues",
        "BaseEInvoicingConfig",
        # OVERRIDE-REASON: no session token caching needed; all BE lookups are stateless HTTP GET requests
        "TokenCache",
        # OVERRIDE-REASON: AuthenticationError re-exported by http_client; already overridden in exceptions — no auth path in BE
        "AuthenticationError",
        # OVERRIDE-REASON: stdlib/third-party re-exports in http_client; BE imports from source directly
        "Any",
        "BaseModel",
        "BaseSettings",
        "Enum",
        "Field",
        "Path",
        "field_validator",
        "parsedate_to_datetime",
        "urlparse",
    },
    "mcp_einvoicing_core.models": {
        # OVERRIDE-REASON: BE defines BEPaymentTerms(PaymentTerms) with IBAN and OGM fields; core PaymentTerms base not directly imported
        "PaymentTerms",
        # OVERRIDE-REASON: BE uses inline vat_summary as a list of dicts on BEInvoice; core VATSummary model is not imported
        "VATSummary",
        # OVERRIDE-REASON: TaxIdValidationResult not yet returned by BE tax-ID helpers; tracked as future work
        "TaxIdValidationResult",
        # OVERRIDE-REASON: stdlib/third-party re-exports in models; BE imports from pydantic/stdlib directly
        "BaseModel",
        "Decimal",
        "Field",
        "field_validator",
        "model_validator",
    },
    "mcp_einvoicing_core.pdf": {
        # OVERRIDE-REASON: Peppol BIS 3.0 / PINT-BE does not mandate PDF/A-3 embedding; PDFEmbedder is not applicable
        "PDFEmbedder",
    },
    "mcp_einvoicing_core.peppol": {
        # OVERRIDE-REASON: check_peppol_participant_be uses a hand-rolled BaseEInvoicingClient pointed at the EU SMP base URL;
        # migration to PeppolSMPClient deferred to BE-P-1 (Q3 2026) [GAP id=BE-P-1]
        "PeppolSMPClient",
        "PeppolLookupResult",
        "PeppolServiceInfo",
        "PeppolParticipantId",
        # OVERRIDE-REASON: BE uses string constants for Peppol environment rather than the PeppolEnvironment enum
        "PeppolEnvironment",
        # OVERRIDE-REASON: stdlib/third-party re-exports in peppol; BE imports from source directly
        "Enum",
        "dataclass",
        "field",
        "safe_fromstring",
    },
    "mcp_einvoicing_core.profile_registry": {
        # OVERRIDE-REASON: BE uses its own CUSTOMIZATION_IDS dict in peppol_bis_3.py; core ProfileRegistry not imported
        "ProfileEntry",
        "ProfileRegistry",
        # OVERRIDE-REASON: set_profile_registry replaces the global registry instance; BE does not customise the registry
        "set_profile_registry",
        # OVERRIDE-REASON: stdlib re-export; BE imports dataclass from dataclasses directly
        "dataclass",
    },
    "mcp_einvoicing_core.qr": {
        # OVERRIDE-REASON: Peppol BIS 3.0 / PINT-BE does not require QR code generation; generate_qr_png_base64 is not used
        "generate_qr_png_base64",
    },
    "mcp_einvoicing_core.schematron": {
        # OVERRIDE-REASON: BE implements lxml-based validation directly in tools/validation.py;
        # SchematronValidator ABC not sub-classed pending BE-SC-1 implementation
        "SchematronValidator",
        "BaseStructuredValidator",
        # OVERRIDE-REASON: UBL 2.1 uses Schematron (not XSD/JSON schema) for business rules; structured validators not applicable yet
        "BaseXSDValidator",
        "BaseJSONValidator",
        # OVERRIDE-REASON: BE uses ValidationResult from core; ValidationMessage detail type is not used in BE tools
        "ValidationMessage",
        # OVERRIDE-REASON: stdlib/third-party re-exports in schematron; BE imports from source directly
        "ABC",
        "abstractmethod",
        "Path",
        "dataclass",
        "field",
        "safe_fromstring",
        "safe_parser",
    },
    "mcp_einvoicing_core.xml_utils": {
        # OVERRIDE-REASON: BE UBL serializer uses its own lxml helper functions in standards/ubl.py; core xml_element/xml_optional not used
        "xml_element",
        "xml_optional",
        # OVERRIDE-REASON: BE-SH-1 tracks adding xml_escape from core to all UBL free-text fields; not yet applied
        "xml_escape",
        # OVERRIDE-REASON: BE tools return plain error strings; structured format_error dict not used
        "format_error",
        # OVERRIDE-REASON: BE UBL serializer omits None elements directly; filter_empty_values utility is not required
        "filter_empty_values",
        # OVERRIDE-REASON: BE tools accept raw XML bytes directly; resolve_xml_input indirection is not used
        "resolve_xml_input",
        # OVERRIDE-REASON: date validation handled by Pydantic date type on BEInvoice fields; validate_date_iso helper not needed
        "validate_date_iso",
        # OVERRIDE-REASON: mark_untrusted / mark_untrusted_fields prompt-injection helpers not yet applied in BE tools
        "mark_untrusted",
        "mark_untrusted_fields",
        # OVERRIDE-REASON: stdlib/third-party re-exports in xml_utils; BE imports from source directly
        "Any",
        "Decimal",
        "safe_fromstring",
        "safe_parser",
    },
}

_BE_MODULES: list[str] = [
    "mcp_einvoicing_be",
    "mcp_einvoicing_be.models.invoice",
    "mcp_einvoicing_be.models.party",
    "mcp_einvoicing_be.server",
    "mcp_einvoicing_be.standards.mercurius",
    "mcp_einvoicing_be.standards.peppol_bis_3",
    "mcp_einvoicing_be.standards.pint_be",
    "mcp_einvoicing_be.standards.ubl",
    "mcp_einvoicing_be.tools.generation",
    "mcp_einvoicing_be.tools.lookup",
    "mcp_einvoicing_be.tools.transformation",
    "mcp_einvoicing_be.tools.validation",
    "mcp_einvoicing_be.utils.helpers",
]

_PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


# ---------------------------------------------------------------------------
# CHECK 2 — Tool registry completeness
# ---------------------------------------------------------------------------

_REQUIRED_TOOL_CATEGORIES: dict[str, str] = {
    "validate_invoice_be": "Validate a Peppol BIS 3.0 / UBL 2.1 invoice",
    "validate_pint_be": "Validate against PINT-BE (NBB) business rules",
    "generate_invoice_be": "Generate a UBL 2.1 invoice document",
    "transform_to_ubl": "Transform invoice data to UBL 2.1 XML",
    "lookup_vat_be": "Look up Belgian company via BCE/KBO",
    "check_peppol_participant_be": "Check Peppol participant registration (BE)",
    "get_invoice_types_be": "List supported invoice types and profiles",
}


def _collect_registered_tools() -> set[str]:
    """Detect tool functions registered via mcp.tool() in the BE server."""
    registered: set[str] = set()

    standalone: list[tuple[str, str]] = [
        ("mcp_einvoicing_be.tools.transformation", "transform_to_ubl"),
        ("mcp_einvoicing_be.tools.lookup", "lookup_vat_be"),
        ("mcp_einvoicing_be.tools.lookup", "check_peppol_participant_be"),
        ("mcp_einvoicing_be.tools.lookup", "get_invoice_types_be"),
    ]
    for mod_path, fn_name in standalone:
        mod, _ = _try_import(mod_path)
        if mod and hasattr(mod, fn_name):
            registered.add(fn_name)

    val_mod, _ = _try_import("mcp_einvoicing_be.tools.validation")
    if val_mod:
        cls = getattr(val_mod, "BEDocumentValidator", None)
        if cls:
            try:
                inst = cls()
                for name in ("validate_invoice_be", "validate_pint_be"):
                    if hasattr(inst, name):
                        registered.add(name)
            except Exception:
                pass

    gen_mod, _ = _try_import("mcp_einvoicing_be.tools.generation")
    if gen_mod:
        cls = getattr(gen_mod, "BEDocumentGenerator", None)
        if cls:
            try:
                inst = cls()
                if hasattr(inst, "generate_invoice_be"):
                    registered.add("generate_invoice_be")
            except Exception:
                pass

    return registered


def run_check_2() -> CheckResult:
    """CHECK 2 — Tool registry completeness."""
    result = CheckResult(check_id="CHECK_2", name="Tool registry completeness")
    registered = _collect_registered_tools()

    for tool_name, description in _REQUIRED_TOOL_CATEGORIES.items():
        tag = "[OK]" if tool_name in registered else "[MISSING_TOOL]"
        sev = SEVERITY_OK if tool_name in registered else SEVERITY_BLOCKING
        result.findings.append(
            CheckFinding(
                check_id="CHECK_2",
                tag=tag,
                severity=sev,
                symbol=tool_name,
                message=(
                    f"Tool '{tool_name}' is registered. ({description})"
                    if tool_name in registered
                    else (
                        f"Required tool '{tool_name}' ({description}) could not be detected. "
                        "Ensure it is defined in the appropriate tools module and registered "
                        "in server.py via mcp.tool()()."
                    )
                ),
            )
        )

    for tool_name in sorted(registered - set(_REQUIRED_TOOL_CATEGORIES)):
        result.findings.append(
            CheckFinding(
                check_id="CHECK_2",
                tag="[EXTRA]",
                severity=SEVERITY_OK,
                symbol=tool_name,
                message=f"Tool '{tool_name}' is present but not in the required tool spec.",
            )
        )

    return result


# ---------------------------------------------------------------------------
# CHECK 3 — Model field alignment (BEInvoice)
# ---------------------------------------------------------------------------

# EN 16931 / PINT-BE mandatory fields that BEInvoice must expose.
# BEInvoice currently extends InvoiceDocument (BE-SC-2 pending); field names
# match InvoiceDocument field names, not EN16931Invoice names.
_CORE_MANDATORY_FIELDS: dict[str, str] = {
    "number": "BT-1  — Invoice number",
    "date": "BT-2  — Invoice issue date",
    "document_type": "BT-3  — Invoice type code (UNTDID 1001)",
    "currency": "BT-5  — Invoice currency",
    "seller": "BG-4  — Seller",
    "buyer": "BG-7  — Buyer",
    "lines": "BG-25 — Invoice lines",
    "vat_summary": "BG-23 — VAT breakdown",
}

_DEPRECATED_CORE_FIELDS: set[str] = set()


def run_check_3() -> CheckResult:
    """CHECK 3 — Model field alignment (BEInvoice)."""
    result = CheckResult(check_id="CHECK_3", name="Model field alignment")

    mod, err = _try_import("mcp_einvoicing_be.models.invoice")
    if mod is None:
        result.skipped = True
        result.skip_reason = f"Could not import BE invoice models: {err}"
        return result

    invoice_cls = getattr(mod, "BEInvoice", None)
    if invoice_cls is None:
        result.findings.append(
            CheckFinding(
                check_id="CHECK_3",
                tag="[MISSING]",
                severity=SEVERITY_BLOCKING,
                symbol="BEInvoice",
                message="BEInvoice class not found in mcp_einvoicing_be.models.invoice.",
            )
        )
        return result

    model_fields = set(invoice_cls.model_fields.keys())

    for field_name, description in _CORE_MANDATORY_FIELDS.items():
        tag = "[OK]" if field_name in model_fields else "[FIELD_MISSING]"
        sev = SEVERITY_OK if field_name in model_fields else SEVERITY_BLOCKING
        result.findings.append(
            CheckFinding(
                check_id="CHECK_3",
                tag=tag,
                severity=sev,
                symbol=f"BEInvoice.{field_name}",
                message=(
                    f"Mandatory field present. {description}"
                    if field_name in model_fields
                    else f"Mandatory field '{field_name}' ({description}) is absent from BEInvoice."
                ),
            )
        )

    for dep_field in _DEPRECATED_CORE_FIELDS:
        if dep_field in model_fields:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_3",
                    tag="[DEPRECATED_IN_USE]",
                    severity=SEVERITY_WARNING,
                    symbol=f"BEInvoice.{dep_field}",
                    message=(
                        f"Field '{dep_field}' is marked deprecated in mcp-einvoicing-core "
                        "but is still present in BEInvoice."
                    ),
                )
            )

    return result


# ---------------------------------------------------------------------------
# CHECK 5 — BE-specific structural checks
# ---------------------------------------------------------------------------


def run_check_5() -> CheckResult:
    """CHECK 5 — BE-specific structural and completeness checks."""
    result = CheckResult(check_id="CHECK_5", name="BE-specific structural checks")

    # 5a: server.py imports cleanly and exposes mcp + main
    server_mod, err = _try_import("mcp_einvoicing_be.server")
    if server_mod is None:
        result.findings.append(
            CheckFinding(
                check_id="CHECK_5",
                tag="[MISSING]",
                severity=SEVERITY_BLOCKING,
                symbol="mcp_einvoicing_be.server",
                message=f"Could not import server module: {err}",
            )
        )
    else:
        for attr in ("mcp", "main"):
            tag = "[OK]" if hasattr(server_mod, attr) else "[MISSING]"
            sev = SEVERITY_OK if hasattr(server_mod, attr) else SEVERITY_BLOCKING
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_5",
                    tag=tag,
                    severity=sev,
                    symbol=f"server.{attr}",
                    message=(
                        f"server.{attr} is present."
                        if hasattr(server_mod, attr)
                        else f"server.{attr} is missing — required for MCP server operation."
                    ),
                )
            )

        # 5b: mcp must be an EInvoicingMCPServer instance
        mcp_obj = getattr(server_mod, "mcp", None)
        core_mod, _ = _try_import("mcp_einvoicing_core")
        server_cls = getattr(core_mod, "EInvoicingMCPServer", None) if core_mod else None
        if mcp_obj is not None and server_cls is not None:
            if isinstance(mcp_obj, server_cls):
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_5",
                        tag="[OK]",
                        severity=SEVERITY_OK,
                        symbol="server.mcp",
                        message="server.mcp is an EInvoicingMCPServer instance.",
                    )
                )
            else:
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_5",
                        tag="[WRONG_TYPE]",
                        severity=SEVERITY_WARNING,
                        symbol="server.mcp",
                        message=(
                            f"server.mcp is {type(mcp_obj).__name__}, expected EInvoicingMCPServer."
                        ),
                    )
                )

    # 5c: CUSTOMIZATION_IDS covers both required Belgian profiles
    bis_mod, _ = _try_import("mcp_einvoicing_be.standards.peppol_bis_3")
    if bis_mod:
        cust_ids = getattr(bis_mod, "CUSTOMIZATION_IDS", None)
        required_profiles = {"peppol-bis-3", "pint-be"}
        if cust_ids is not None:
            for profile in sorted(required_profiles):
                tag = "[OK]" if profile in cust_ids else "[MISSING_PROFILE]"
                sev = SEVERITY_OK if profile in cust_ids else SEVERITY_BLOCKING
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_5",
                        tag=tag,
                        severity=sev,
                        symbol=f"CUSTOMIZATION_IDS[{profile!r}]",
                        message=(
                            f"Profile '{profile}' has a CUSTOMIZATION_IDS entry."
                            if profile in cust_ids
                            else (
                                f"Required Belgian profile '{profile}' has no entry in "
                                "CUSTOMIZATION_IDS — UBL generation will be incomplete."
                            )
                        ),
                    )
                )
        else:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_5",
                    tag="[MISSING]",
                    severity=SEVERITY_BLOCKING,
                    symbol="CUSTOMIZATION_IDS",
                    message="CUSTOMIZATION_IDS not found in mcp_einvoicing_be.standards.peppol_bis_3.",
                )
            )

    # 5d: BEPaymentTerms is importable with key IBAN/OGM fields
    models_mod, _ = _try_import("mcp_einvoicing_be.models.invoice")
    if models_mod:
        pt_cls = getattr(models_mod, "BEPaymentTerms", None)
        if pt_cls is None:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_5",
                    tag="[MISSING]",
                    severity=SEVERITY_WARNING,
                    symbol="BEPaymentTerms",
                    message="BEPaymentTerms not found in mcp_einvoicing_be.models.invoice.",
                )
            )
        else:
            pt_fields = set(pt_cls.model_fields.keys())
            for fname in ("iban", "ogm_reference"):
                tag = "[OK]" if fname in pt_fields else "[MISSING]"
                sev = SEVERITY_OK if fname in pt_fields else SEVERITY_WARNING
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_5",
                        tag=tag,
                        severity=sev,
                        symbol=f"BEPaymentTerms.{fname}",
                        message=(
                            f"Payment terms field '{fname}' is present."
                            if fname in pt_fields
                            else f"Expected payment terms field '{fname}' is absent."
                        ),
                    )
                )

    return result


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def run_audit() -> AuditReport:
    """Execute all checks and return the aggregated AuditReport. No side effects."""
    report = make_report("mcp-einvoicing-be", _PYPROJECT)

    report.checks.append(
        run_check_core_coverage(
            package_name="mcp-einvoicing-be",
            package_modules=_BE_MODULES,
            intentional_overrides=_INTENTIONAL_OVERRIDES,
            is_en16931_family=_IS_EN16931_FAMILY,
            primary_invoice_class=_PRIMARY_INVOICE_CLASS,
        )
    )
    report.checks.append(run_check_2())
    report.checks.append(run_check_3())
    report.checks.append(
        run_check_version_compatibility(
            package_name="mcp-einvoicing-be",
            pyproject_path=_PYPROJECT,
        )
    )
    report.checks.append(run_check_5())

    return report


def main(argv: list[str] | None = None) -> int:
    args = parse_audit_args("Pre-publish audit: mcp-einvoicing-be vs mcp-einvoicing-core", argv)
    report = run_audit()

    output_path = Path(args.output) if args.output else Path("audit/report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    if not args.quiet:
        print(render_summary_table(report))
        print(f"\nJSON report written to: {output_path}")

    if args.fail_on == "never":
        return 0
    if args.fail_on == "warnings":
        return min(report.exit_code, 2)
    return 2 if report.total_blocking > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
