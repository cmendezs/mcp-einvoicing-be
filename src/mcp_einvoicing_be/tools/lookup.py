"""Lookup tools: lookup_vat_be, check_peppol_participant_be, get_invoice_types_be."""

import os
from typing import Annotated

from mcp_einvoicing_core import AuthMode, BaseEInvoicingClient, PlatformError

from mcp_einvoicing_be.standards.peppol_bis_3 import INVOICE_TYPES
from mcp_einvoicing_be.utils.helpers import normalize_vat_be

_BCE_API_BASE = "https://api.kbo-bce.be/v1"
_PEPPOL_SML_BASE = "https://edelivery.tech.ec.europa.eu/edelivery-smp"


def _bce_client() -> BaseEInvoicingClient:
    api_key = os.environ.get("BCE_API_KEY", "")
    if api_key:
        return BaseEInvoicingClient(
            base_url=_BCE_API_BASE,
            auth_mode=AuthMode.BEARER_TOKEN,
            static_bearer_token=api_key,
        )
    return BaseEInvoicingClient(base_url=_BCE_API_BASE, auth_mode=AuthMode.NONE)


def _peppol_client() -> BaseEInvoicingClient:
    return BaseEInvoicingClient(base_url=_PEPPOL_SML_BASE, auth_mode=AuthMode.NONE)


async def lookup_vat_be(
    vat_number: Annotated[
        str,
        "Belgian VAT/enterprise number, e.g. 'BE0123456789' or '0123456789'",
    ],
) -> dict[str, object]:
    """Look up a Belgian enterprise number against the BCE/KBO public database.

    Accepts the number with or without the 'BE' prefix and with or without
    dots/spaces. Returns the enterprise's legal name, registered address,
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
            return {
                "found": False,
                "vat_number": normalized,
                "error": "Enterprise number not found",
            }  # noqa: E501
        raise

    data: dict[str, object] = response.json()
    return {
        "found": True,
        "vat_number": normalized,
        "name": data.get("name"),
        "legal_form": data.get("legalForm"),
        "status": data.get("status"),
        "address": data.get("address"),
        "nace_codes": data.get("activities", []),
        "start_date": data.get("startDate"),
    }


async def check_peppol_participant_be(
    identifier: Annotated[
        str,
        "Peppol participant ID (e.g. '0208:0123456789') or plain Belgian VAT number",
    ],
) -> dict[str, object]:
    """Check whether a Belgian company is registered as a Peppol participant.

    Queries the Peppol SMP/SML network. If a plain VAT number is provided it
    is converted to the Belgian Peppol scheme (ICD 0208 for KBO/BCE numbers).

    Returns registration status, supported document type identifiers, and the
    SMP access point endpoint URL.
    """
    if ":" not in identifier:
        digits = normalize_vat_be(identifier)[2:]  # strip 'BE'
        participant_id = f"0208:{digits}"
    else:
        participant_id = identifier

    scheme, value = participant_id.split(":", 1)
    path = f"/iso6523-actorid-upis::{scheme}:{value}"

    client = _peppol_client()
    try:
        response = await client._request("GET", path)
    except PlatformError as exc:
        if exc.status_code == 404:
            return {
                "registered": False,
                "participant_id": participant_id,
                "error": "Participant not found on Peppol network",
            }
        raise

    return {
        "registered": True,
        "participant_id": participant_id,
        "raw": response.text,
    }


async def get_invoice_types_be() -> dict[str, object]:
    """Return the supported Belgian e-invoice document types.

    Includes invoice (380), credit note (381), and debit note (383) with their
    UBL ``customizationID`` and ``profileID`` values for each supported profile
    (Peppol BIS Billing 3.0 and PINT-BE).
    """
    return {"invoice_types": INVOICE_TYPES}
