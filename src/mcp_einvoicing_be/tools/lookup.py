"""Lookup tools: lookup_vat_be, check_peppol_participant_be, get_invoice_types_be.

BE-LC-1 (resolved): check_peppol_participant_be now uses PeppolSMPClient from
mcp-einvoicing-core instead of a hand-rolled BaseEInvoicingClient.  PeppolSMPClient
performs correct DNS-over-HTTPS U-NAPTR resolution followed by an SMP service-group
HTTP request, exactly as the Peppol BDMSL specification requires.

BE-LC-2 (partial): a structured warning is emitted when BCE_API_KEY is absent.
"""

import os
from typing import Annotated

from mcp_einvoicing_core import AuthMode, BaseEInvoicingClient, PlatformError
from mcp_einvoicing_core.peppol import PeppolParticipantId, PeppolSMPClient

from mcp_einvoicing_be.standards.peppol_bis_3 import INVOICE_TYPES
from mcp_einvoicing_be.utils.helpers import normalize_vat_be

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
        response = await client._request("GET", f"/enterprises/{digits}")
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


async def check_peppol_participant_be(
    identifier: Annotated[
        str,
        "Peppol participant ID (e.g. '0208:0123456789') or plain Belgian VAT number",
    ],
) -> dict[str, object]:
    """Check whether a Belgian company is registered as a Peppol participant.

    Queries the Peppol BDMSL network using the standard DNS-over-HTTPS U-NAPTR
    lookup followed by an SMP service-group request, as required by the Peppol
    Policy for Use of Identifiers.  If a plain VAT number is provided it is
    converted to the Belgian Peppol scheme (ICD 0208 = KBO/BCE).

    BE-LC-1 (resolved): uses PeppolSMPClient from mcp-einvoicing-core, replacing
    the previous hand-rolled HTTP client which called a non-standard SMP endpoint
    and did not implement DNS-based SMP discovery.

    Returns registration status, supported document type identifiers, and the
    SMP hostname resolved during the lookup.
    """
    if ":" not in identifier:
        digits = normalize_vat_be(identifier)[2:]  # strip 'BE'
        participant_id_str = f"0208:{digits}"
    else:
        participant_id_str = identifier

    try:
        participant_id = PeppolParticipantId.parse(participant_id_str)
    except ValueError as exc:
        return {
            "registered": False,
            "participant_id": participant_id_str,
            "error": f"Invalid participant identifier: {exc}",
        }

    client = PeppolSMPClient()
    try:
        result = await client.lookup_participant(participant_id)
    except Exception as exc:
        return {
            "registered": False,
            "participant_id": participant_id_str,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return result.to_dict()


async def get_invoice_types_be() -> dict[str, object]:
    """Return the supported Belgian e-invoice document types.

    Includes invoice (380), credit note (381), and debit note (383) with their
    UBL ``customizationID`` and ``profileID`` values for each supported profile
    (Peppol BIS Billing 3.0).
    """
    return {"invoice_types": INVOICE_TYPES}
