"""Lookup tools: lookup_vat_be, check_peppol_participant_be, get_invoice_types_be."""

import os
from typing import Annotated

import httpx

from mcp_einvoicing_be.standards.peppol_bis_3 import INVOICE_TYPES
from mcp_einvoicing_be.utils.helpers import normalize_vat_be

_BCE_API_BASE = "https://api.kbo-bce.be/v1"
_PEPPOL_SML_BASE = "https://edelivery.tech.ec.europa.eu/edelivery-smp"


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

    Requires the ``BCE_API_KEY`` environment variable.
    """
    normalized = normalize_vat_be(vat_number)
    api_key = os.environ.get("BCE_API_KEY", "")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{_BCE_API_BASE}/enterprises/{normalized}",
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    if response.status_code == 404:
        return {"found": False, "vat_number": normalized, "error": "Enterprise number not found"}

    response.raise_for_status()
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
        "Peppol participant ID (e.g. '0088:BE0123456789') or plain Belgian VAT number",
    ],
) -> dict[str, object]:
    """Check whether a Belgian company is registered as a Peppol participant.

    Queries the Peppol SMP/SML network. If a plain VAT number is provided it
    is converted to the Belgian Peppol scheme (ICD 0208 for KBO/BCE numbers).

    Returns registration status, supported document type identifiers, and the
    SMP access point endpoint URL.
    """
    if ":" not in identifier:
        normalized = normalize_vat_be(identifier).lstrip("BE")
        participant_id = f"0208:{normalized}"
    else:
        participant_id = identifier

    scheme, value = participant_id.split(":", 1)
    smp_url = f"{_PEPPOL_SML_BASE}/iso6523-actorid-upis::{scheme}:{value}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(smp_url, follow_redirects=True)

    if response.status_code == 404:
        return {
            "registered": False,
            "participant_id": participant_id,
            "error": "Participant not found on Peppol network",
        }

    response.raise_for_status()

    return {
        "registered": True,
        "participant_id": participant_id,
        "smp_url": str(response.url),
        "raw": response.text,
    }


async def get_invoice_types_be() -> dict[str, object]:
    """Return the supported Belgian e-invoice document types.

    Includes invoice (380), credit note (381), and debit note (383) with their
    UBL ``customizationID`` and ``profileID`` values for each supported profile
    (Peppol BIS Billing 3.0 and PINT-BE).
    """
    return {"invoice_types": INVOICE_TYPES}
