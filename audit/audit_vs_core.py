"""Pre-publish audit: verify mcp-einvoicing-be coherence against mcp-einvoicing-core.

Run standalone:
    python audit/audit_vs_core.py
    python audit/audit_vs_core.py --output audit/report.json
    python audit/audit_vs_core.py --fail-on blocking   # exits 2 on blocking failures
    python audit/audit_vs_core.py --fail-on warnings   # exits 1 on warnings, 2 on blocking

Exit codes:
    0  All checks passed
    1  Warnings only (non-blocking)
    2  Blocking failures found

This script is designed to be importable with no side effects; all execution
is guarded by `if __name__ == "__main__"`.

[NEED: update CHECK 1 once mcp-einvoicing-core public API is finalised]
[NEED: update CHECK 5 once mcp-einvoicing-core tool category registry is defined]
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

SEVERITY_BLOCKING = "BLOCKING"
SEVERITY_WARNING = "WARNING"
SEVERITY_OK = "OK"
SEVERITY_SKIP = "SKIP"


@dataclass
class CheckFinding:
    check_id: str
    tag: str  # e.g. [MISSING], [OVERRIDE], [OK], [SKIP]
    severity: str  # SEVERITY_* constants
    symbol: str  # What was checked (class name, field name, etc.)
    message: str


@dataclass
class CheckResult:
    check_id: str
    name: str
    findings: list[CheckFinding] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SEVERITY_BLOCKING)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SEVERITY_WARNING)

    @property
    def passed(self) -> bool:
        return self.blocking_count == 0


@dataclass
class AuditReport:
    generated_at: str
    pkg_version: str
    core_version: str | None
    core_version_compatible: bool
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def total_blocking(self) -> int:
        return sum(c.blocking_count for c in self.checks)

    @property
    def total_warnings(self) -> int:
        return sum(c.warning_count for c in self.checks)

    @property
    def exit_code(self) -> int:
        if self.total_blocking > 0:
            return 2
        if self.total_warnings > 0:
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "pkg_version": self.pkg_version,
            "core_version": self.core_version,
            "core_version_compatible": self.core_version_compatible,
            "exit_code": self.exit_code,
            "total_blocking": self.total_blocking,
            "total_warnings": self.total_warnings,
            "checks": [
                {
                    "check_id": c.check_id,
                    "name": c.name,
                    "passed": c.passed,
                    "skipped": c.skipped,
                    "skip_reason": c.skip_reason,
                    "blocking_count": c.blocking_count,
                    "warning_count": c.warning_count,
                    "findings": [
                        {
                            "check_id": f.check_id,
                            "tag": f.tag,
                            "severity": f.severity,
                            "symbol": f.symbol,
                            "message": f.message,
                        }
                        for f in c.findings
                    ],
                }
                for c in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _try_import(module_path: str) -> tuple[Any | None, str | None]:
    """Attempt to import a module; return (module, None) or (None, error_message)."""
    try:
        return importlib.import_module(module_path), None
    except ImportError as exc:
        return None, str(exc)


def _get_public_symbols(module: Any) -> dict[str, Any]:
    """Return all public symbols from a module (respecting __all__ if defined)."""
    if hasattr(module, "__all__"):
        return {name: getattr(module, name) for name in module.__all__ if hasattr(module, name)}
    return {
        name: obj
        for name, obj in inspect.getmembers(module)
        if not name.startswith("_") and not inspect.ismodule(obj)
    }


def _get_installed_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a PEP 440 version string into a comparable tuple (major, minor, patch)."""
    parts = v.split(".")
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p.split("a")[0].split("b")[0].split("rc")[0]))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def _version_in_range(version: str, spec: str) -> bool:
    """
    Naive PEP 440 specifier check for >=X,<Y ranges.
    Only handles >= and < comparators (sufficient for typical ~= and range deps).
    [NEED: replace with packaging.version for full PEP 440 compliance]
    """
    v = _parse_version(version)
    for part in spec.split(","):
        part = part.strip()
        if part.startswith(">="):
            low = _parse_version(part[2:].strip())
            if v < low:
                return False
        elif part.startswith("<"):
            high = _parse_version(part[1:].strip())
            if v >= high:
                return False
        elif part.startswith("~="):
            base = _parse_version(part[2:].strip())
            if len(base) >= 2 and (v < base or v[0] != base[0]):
                return False
    return True


# ---------------------------------------------------------------------------
# CHECK 1 — Core interface coverage
# ---------------------------------------------------------------------------

_INTENTIONAL_OVERRIDES: dict[str, set[str]] = {
    # [NEED: populate once mcp-einvoicing-core public API is known]
}

_CORE_MODULES_TO_CHECK: list[str] = [
    "mcp_einvoicing_core",
    "mcp_einvoicing_core.models",
    "mcp_einvoicing_core.validators",
    "mcp_einvoicing_core.tools",
]

_PKG_MODULES: list[str] = [
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


def _collect_pkg_imports() -> set[str]:
    """Collect all symbol names imported from core into BE modules."""
    imported: set[str] = set()
    for mod_path in _PKG_MODULES:
        mod, err = _try_import(mod_path)
        if mod is None:
            continue
        for name, obj in inspect.getmembers(mod):
            if not name.startswith("_"):
                obj_module = getattr(obj, "__module__", "") or ""
                if "mcp_einvoicing_core" in obj_module:
                    imported.add(name)
    return imported


def run_check_1() -> CheckResult:
    """CHECK 1 — Core interface coverage."""
    result = CheckResult(check_id="CHECK_1", name="Core interface coverage")

    core_available = _get_installed_version("mcp-einvoicing-core") is not None
    if not core_available:
        result.skipped = True
        result.skip_reason = (
            "mcp-einvoicing-core is not installed. Install it with: pip install mcp-einvoicing-core"
        )
        result.findings.append(
            CheckFinding(
                check_id="CHECK_1",
                tag="[SKIP]",
                severity=SEVERITY_WARNING,
                symbol="mcp-einvoicing-core",
                message="Package not installed — cannot verify core interface coverage.",
            )
        )
        return result

    pkg_imports = _collect_pkg_imports()

    for mod_path in _CORE_MODULES_TO_CHECK:
        core_mod, err = _try_import(mod_path)
        if core_mod is None:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_1",
                    tag="[SKIP]",
                    severity=SEVERITY_WARNING,
                    symbol=mod_path,
                    message=f"Could not import core module: {err}",
                )
            )
            continue

        overrides_for_mod = _INTENTIONAL_OVERRIDES.get(mod_path, set())
        symbols = _get_public_symbols(core_mod)

        for sym_name, sym_obj in symbols.items():
            if not (inspect.isclass(sym_obj) or inspect.isfunction(sym_obj)):
                continue

            if sym_name in overrides_for_mod:
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_1",
                        tag="[OVERRIDE]",
                        severity=SEVERITY_OK,
                        symbol=f"{mod_path}.{sym_name}",
                        message="Intentionally overridden by BE package.",
                    )
                )
            elif sym_name in pkg_imports:
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_1",
                        tag="[OK]",
                        severity=SEVERITY_OK,
                        symbol=f"{mod_path}.{sym_name}",
                        message="Imported and used.",
                    )
                )
            else:
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_1",
                        tag="[MISSING]",
                        severity=SEVERITY_WARNING,
                        symbol=f"{mod_path}.{sym_name}",
                        message=(
                            f"Core symbol '{sym_name}' is neither imported by the BE package "
                            "nor marked as an intentional override. "
                            "Add to _INTENTIONAL_OVERRIDES if this is deliberate."
                        ),
                    )
                )

    return result


# ---------------------------------------------------------------------------
# CHECK 2 — Tool registry completeness
# ---------------------------------------------------------------------------

_REQUIRED_TOOL_CATEGORIES: dict[str, str] = {
    "validate_invoice_be": "Validate a Peppol BIS 3.0 invoice",
    "validate_pint_be": "Validate against PINT-BE (NBB) rules",
    "generate_invoice_be": "Generate a UBL 2.1 invoice document",
    "transform_to_ubl": "Transform invoice data to UBL 2.1 XML",
    "lookup_vat_be": "Look up Belgian company via BCE/KBO",
    "check_peppol_participant_be": "Check Peppol participant registration (BE)",
    "get_invoice_types_be": "List supported invoice types and profiles",
}


def _collect_registered_tools() -> set[str]:
    """
    Detect tool functions that the server registers via mcp.tool()().
    BE uses bound methods on validator/generator instances plus standalone functions.
    """
    registered: set[str] = set()

    # Standalone functions in lookup and transformation modules
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

    # Methods on BEDocumentValidator
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

    # Methods on BEDocumentGenerator
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
        if tool_name in registered:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_2",
                    tag="[OK]",
                    severity=SEVERITY_OK,
                    symbol=tool_name,
                    message=f"Tool '{tool_name}' is present. ({description})",
                )
            )
        else:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_2",
                    tag="[MISSING_TOOL]",
                    severity=SEVERITY_BLOCKING,
                    symbol=tool_name,
                    message=(
                        f"Required tool '{tool_name}' ({description}) could not be detected. "
                        "Ensure it is defined in the appropriate tools module and registered "
                        "in server.py via mcp.tool()()."
                    ),
                )
            )

    extra = registered - set(_REQUIRED_TOOL_CATEGORIES)
    for tool_name in sorted(extra):
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
# CHECK 3 — Model field alignment
# ---------------------------------------------------------------------------

# Mandatory fields for EN 16931 / PINT-BE that must be present in BEInvoice.
# Fields marked [Inference] are inherited from InvoiceDocument; exact names
# should be verified once mcp-einvoicing-core model fields are published.
# [NEED: derive complete list from mcp-einvoicing-core InvoiceDocument once finalised]
_CORE_MANDATORY_FIELDS: dict[str, str] = {
    "number": "BT-1  — Invoice number (InvoiceDocument.number)",
    "date": "BT-2  — Invoice issue date (InvoiceDocument.date)",
    "document_type": "BT-3  — Invoice type code (UNTDID 1001)",
    "currency": "BT-5  — Invoice currency (InvoiceDocument.currency)",
    "seller": "BG-4  — Seller",
    "buyer": "BG-7  — Buyer",
    "lines": "BG-25 — Invoice lines",
    "vat_summary": "BG-23 — VAT breakdown (InvoiceDocument.vat_summary)",
}

_DEPRECATED_CORE_FIELDS: set[str] = set()


def run_check_3() -> CheckResult:
    """CHECK 3 — Model field alignment."""
    result = CheckResult(check_id="CHECK_3", name="Model field alignment")

    mod, err = _try_import("mcp_einvoicing_be.models.invoice")
    if mod is None:
        result.skipped = True
        result.skip_reason = f"Could not import BE invoice models: {err}"
        return result

    be_invoice_cls = getattr(mod, "BEInvoice", None)
    if be_invoice_cls is None:
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

    model_fields = set(be_invoice_cls.model_fields.keys())

    for field_name, description in _CORE_MANDATORY_FIELDS.items():
        if field_name in model_fields:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_3",
                    tag="[OK]",
                    severity=SEVERITY_OK,
                    symbol=f"BEInvoice.{field_name}",
                    message=f"Mandatory field present. {description}",
                )
            )
        else:
            result.findings.append(
                CheckFinding(
                    check_id="CHECK_3",
                    tag="[FIELD_MISSING]",
                    severity=SEVERITY_BLOCKING,
                    symbol=f"BEInvoice.{field_name}",
                    message=(
                        f"Mandatory field '{field_name}' ({description}) is absent from BEInvoice."
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
# CHECK 4 — Version compatibility
# ---------------------------------------------------------------------------


def _read_core_version_spec_from_pyproject() -> str | None:
    """Extract the mcp-einvoicing-core version specifier from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    try:
        text = pyproject_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "mcp-einvoicing-core" in line:
                start = line.find("mcp-einvoicing-core")
                fragment = line[start:].strip().strip('",').strip("'")
                spec = fragment.replace("mcp-einvoicing-core", "").strip()
                return spec if spec else None
    except Exception:
        pass
    return None


def run_check_4() -> CheckResult:
    """CHECK 4 — Version compatibility."""
    result = CheckResult(check_id="CHECK_4", name="Version compatibility")

    installed_core = _get_installed_version("mcp-einvoicing-core")
    if installed_core is None:
        result.findings.append(
            CheckFinding(
                check_id="CHECK_4",
                tag="[SKIP]",
                severity=SEVERITY_WARNING,
                symbol="mcp-einvoicing-core",
                message=(
                    "mcp-einvoicing-core is not installed — cannot check version compatibility."
                ),
            )
        )
        return result

    declared_spec = _read_core_version_spec_from_pyproject()
    if declared_spec is None:
        result.findings.append(
            CheckFinding(
                check_id="CHECK_4",
                tag="[SKIP]",
                severity=SEVERITY_WARNING,
                symbol="pyproject.toml",
                message=(
                    "Could not parse mcp-einvoicing-core version spec from pyproject.toml. "
                    "[NEED: ensure pyproject.toml uses standard PEP 440 specifiers]"
                ),
            )
        )
        return result

    compatible = _version_in_range(installed_core, declared_spec)
    tag = "[OK]" if compatible else "[VERSION_MISMATCH]"
    severity = SEVERITY_OK if compatible else SEVERITY_BLOCKING

    result.findings.append(
        CheckFinding(
            check_id="CHECK_4",
            tag=tag,
            severity=severity,
            symbol="mcp-einvoicing-core",
            message=(
                f"Installed: {installed_core} | "
                f"Declared range: {declared_spec} | "
                f"Compatible: {compatible}"
            ),
        )
    )

    return result


# ---------------------------------------------------------------------------
# CHECK 5 — BE-specific structural checks
# [NEED: extend with additional checks once mcp-einvoicing-core interface is known]
# ---------------------------------------------------------------------------


def run_check_5() -> CheckResult:
    """CHECK 5 — BE-specific structural and completeness checks."""
    result = CheckResult(check_id="CHECK_5", name="BE-specific structural checks")

    # 5a: server.py imports cleanly and exports main + mcp
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
            if hasattr(server_mod, attr):
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_5",
                        tag="[OK]",
                        severity=SEVERITY_OK,
                        symbol=f"server.{attr}",
                        message=f"server.{attr} is present.",
                    )
                )
            else:
                result.findings.append(
                    CheckFinding(
                        check_id="CHECK_5",
                        tag="[MISSING]",
                        severity=SEVERITY_BLOCKING,
                        symbol=f"server.{attr}",
                        message=f"server.{attr} is missing — required for MCP server operation.",
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
                if profile in cust_ids:
                    result.findings.append(
                        CheckFinding(
                            check_id="CHECK_5",
                            tag="[OK]",
                            severity=SEVERITY_OK,
                            symbol=f"CUSTOMIZATION_IDS[{profile!r}]",
                            message=f"Profile '{profile}' has a CUSTOMIZATION_IDS entry.",
                        )
                    )
                else:
                    result.findings.append(
                        CheckFinding(
                            check_id="CHECK_5",
                            tag="[MISSING_PROFILE]",
                            severity=SEVERITY_BLOCKING,
                            symbol=f"CUSTOMIZATION_IDS[{profile!r}]",
                            message=(
                                f"Required Belgian profile '{profile}' has no entry in "
                                "CUSTOMIZATION_IDS — UBL generation will be incomplete."
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
                    message=(
                        "CUSTOMIZATION_IDS not found in mcp_einvoicing_be.standards.peppol_bis_3."
                    ),
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
                if fname in pt_fields:
                    result.findings.append(
                        CheckFinding(
                            check_id="CHECK_5",
                            tag="[OK]",
                            severity=SEVERITY_OK,
                            symbol=f"BEPaymentTerms.{fname}",
                            message=f"Payment terms field '{fname}' is present.",
                        )
                    )
                else:
                    result.findings.append(
                        CheckFinding(
                            check_id="CHECK_5",
                            tag="[MISSING]",
                            severity=SEVERITY_WARNING,
                            symbol=f"BEPaymentTerms.{fname}",
                            message=f"Expected payment terms field '{fname}' is absent.",
                        )
                    )

    return result


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def render_summary_table(report: AuditReport) -> str:
    """Render a human-readable ASCII summary table."""
    lines: list[str] = []
    sep = "─" * 80

    lines.append(sep)
    lines.append("  mcp-einvoicing-be  Pre-publish Audit Report")
    lines.append(f"  Generated : {report.generated_at}")
    lines.append(f"  BE version: {report.pkg_version}")
    lines.append(f"  Core ver  : {report.core_version or 'not installed'}")
    lines.append(sep)

    for check in report.checks:
        status = "SKIPPED" if check.skipped else ("PASS" if check.passed else "FAIL")
        lines.append(f"\n  [{status}] {check.check_id}: {check.name}")
        if check.skipped:
            lines.append(f"         ↳ {check.skip_reason}")
            continue
        lines.append(
            f"         Blocking: {check.blocking_count}  "
            f"Warnings: {check.warning_count}  "
            f"OK: {sum(1 for f in check.findings if f.severity == SEVERITY_OK)}"
        )
        for finding in check.findings:
            if finding.severity in (SEVERITY_BLOCKING, SEVERITY_WARNING):
                indent = "    "
                tag_str = f"{finding.tag:<24}"
                msg = textwrap.fill(
                    finding.message,
                    width=72,
                    initial_indent=indent + tag_str + " ",
                    subsequent_indent=indent + " " * 25,
                )
                lines.append(msg)

    lines.append(f"\n{sep}")
    lines.append(
        f"  TOTAL — Blocking: {report.total_blocking}  "
        f"Warnings: {report.total_warnings}  "
        f"Exit code: {report.exit_code}"
    )
    verdict = {0: "✅ PASS", 1: "⚠️  WARNINGS", 2: "❌ FAIL"}[report.exit_code]
    lines.append(f"  Verdict: {verdict}")
    lines.append(sep)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_audit() -> AuditReport:
    """Execute all checks and return the aggregated AuditReport. No side effects."""
    pkg_version = _get_installed_version("mcp-einvoicing-be") or "0.0.0-dev"
    core_version = _get_installed_version("mcp-einvoicing-core")

    core_compat = True
    if core_version:
        spec = _read_core_version_spec_from_pyproject()
        if spec:
            core_compat = _version_in_range(core_version, spec)

    report = AuditReport(
        generated_at=datetime.now(UTC).isoformat(),
        pkg_version=pkg_version,
        core_version=core_version,
        core_version_compatible=core_compat,
    )

    report.checks.append(run_check_1())
    report.checks.append(run_check_2())
    report.checks.append(run_check_3())
    report.checks.append(run_check_4())
    report.checks.append(run_check_5())

    return report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-publish audit: mcp-einvoicing-be vs mcp-einvoicing-core",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Exit codes:
          0  All checks passed
          1  Warnings only
          2  Blocking failures (publish should be blocked)
        """),
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write JSON report to this path (default: audit/report.json)",
        default=None,
    )
    parser.add_argument(
        "--fail-on",
        metavar="LEVEL",
        choices=["blocking", "warnings", "never"],
        default="blocking",
        help=(
            "When to exit non-zero: "
            "'blocking' (default) = only on BLOCKING findings; "
            "'warnings' = on any warning or blocking; "
            "'never' = always exit 0 (for informational runs)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable table; only write JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entrypoint — returns exit code."""
    args = _parse_args(argv)

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
