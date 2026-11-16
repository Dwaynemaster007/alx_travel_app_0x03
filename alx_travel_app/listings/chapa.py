"""Thin client for the Chapa payment API (https://developer.chapa.co)."""

import requests
from django.conf import settings


class ChapaError(Exception):
    """Chapa could not be reached or rejected the request."""


class ChapaNotConfigured(ChapaError):
    """CHAPA_SECRET_KEY is not set."""


def _headers():
    if not settings.CHAPA_SECRET_KEY:
        raise ChapaNotConfigured("CHAPA_SECRET_KEY is not set.")
    return {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def _parse(response):
    try:
        data = response.json()
    except ValueError as exc:
        raise ChapaError(f"Chapa returned a non-JSON response (HTTP {response.status_code}).") from exc
    if response.status_code >= 400 or data.get("status") != "success":
        message = data.get("message") or f"HTTP {response.status_code}"
        raise ChapaError(f"Chapa request failed: {message}")
    return data


def initialize_transaction(payload):
    """Start a transaction. Returns Chapa's JSON body (``data.checkout_url``)."""
    headers = _headers()
    try:
        response = requests.post(
            f"{settings.CHAPA_BASE_URL}/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=settings.CHAPA_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ChapaError(f"Could not reach Chapa: {exc}") from exc
    return _parse(response)


def verify_transaction(tx_ref):
    """Look up a transaction by our tx_ref. Returns Chapa's JSON body."""
    headers = _headers()
    try:
        response = requests.get(
            f"{settings.CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=headers,
            timeout=settings.CHAPA_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ChapaError(f"Could not reach Chapa: {exc}") from exc
    return _parse(response)
