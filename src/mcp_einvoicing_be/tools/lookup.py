"""Lookup tools: lookup_vat_be, get_invoice_types_be.

BE-LC-2 (partial): a structured warning is emitted when BCE_API_KEY is absent.

ARCH-CONVERGE-BE (resolved): Peppol participant lookup moved to the shared
core Peppol tool plugin (``mcp_einvoicing_core.peppol.tools.register_peppol_tools``,
mounted in server.py). The BE-local ``check_peppol_participant_be`` wrapper
was removed; use ``peppol_lookup_participant`` instead.
"""

import os
from typing import Annotated

from mcp_einvoicing_core import AuthMode, BaseEInvoicingClient, PlatformError

from mcp_einvoicing_be.standards.peppol_bis_3 import INVOICE_TYPES
from mcp_einvoicing_be.utils.helpers import normalize_vat_be

# [GAP id=BE-KBO-ENDPOINT] Base URL and response-field mapping (legalForm,
# activities, startDate) are [Unverified] against an authoritative BCE/KBO API
# document — see context-library/countries/be.md.
_BCE_API_BASE = "https://api.kbo-bce.be/v1"


def _bce_client() -> BaseEInvoicingClient:
    api_key = os.environ.get("BCE_API_KEY", "")
    if not api_key:
        import warnings  # noqa: PLC0415

        warnings.warn(
            "BCE_API_KEY environment variable is not set.  Requests to the BCE/KBO API "
            "will be unauthenticated and may be rate-limited or refused.",
            stacklevel=2,
        )
    if api_key:
        return BaseEInvoicingClient(
            base_url=_BCE_API_BASE,
            auth_mode=AuthMode.BEARER_TOKEN,
            static_bearer_token=api_key,
        )
    return BaseEInvoicingClient(base_url=_BCE_API_BASE, auth_mode=AuthMode.NONE)


async def lookup_vat_be(
    vat_number: Annotated[
        str,
        "Belgian VAT/enterprise number, e.g. 'BE0123456789' or '0123456789'",
    ],
) -> dict[str, object]:
    """Look up a Belgian enterprise number against the BCE/KBO public database.

    Accepts the number with or without the 'BE' prefix and with or without
    dots/spaces.  Returns the enterprise's legal name, registered address,
    legal form, status, and NACE activity codes.

    Optionally set the ``BCE_API_KEY`` environment variable for authenticated
    access to the full BCE dataset.
    """
    normalized = normalize_vat_be(vat_number)
    digits = normalized[2:]  # strip 'BE' for the path segment

    client = _bce_client()
    try:
        response = await client.request("GET", f"/enterprises/{digits}")
    except PlatformError as exc:
        if exc.status_code == 404:
            not_found: dict[str, object] = {
                "found": False,
                "vat_number": normalized,
                "error": "Enterprise number not found",
            }
            if not os.environ.get("BCE_API_KEY"):
                not_found["warning"] = {
                    "code": "BCE_API_KEY_MISSING",
                    "message": (
                        "BCE_API_KEY is not set. Results may be incomplete or rate-limited. "
                        "Set the BCE_API_KEY environment variable for full BCE/KBO access."
                    ),
                }
            return not_found
        raise

    data: dict[str, object] = response.json()
    result: dict[str, object] = {
        "found": True,
        "vat_number": normalized,
        "name": data.get("name"),
        "legal_form": data.get("legalForm"),
        "status": data.get("status"),
        "address": data.get("address"),
        "nace_codes": data.get("activities", []),
        "start_date": data.get("startDate"),
    }
    if not os.environ.get("BCE_API_KEY"):
        result["warning"] = {
            "code": "BCE_API_KEY_MISSING",
            "message": (
                "BCE_API_KEY is not set. Results may be incomplete or rate-limited. "
                "Set the BCE_API_KEY environment variable for full BCE/KBO access."
            ),
        }
    return result


async def get_invoice_types_be() -> dict[str, object]:
    """Return the supported Belgian e-invoice document types.

    Includes invoice (380), credit note (381), and debit note (383) with their
    UBL ``customizationID`` and ``profileID`` values for each supported profile
    (Peppol BIS Billing 3.0).
    """
    return {"invoice_types": INVOICE_TYPES}
