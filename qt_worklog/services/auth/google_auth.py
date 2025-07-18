from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import requests
from google.auth.transport.requests import Request as GARequest
from google_auth_oauthlib.flow import InstalledAppFlow

from ... import config

# Scopes required to receive an ID token that includes the user's identity.
# Use the canonical userinfo scope URIs to avoid scope mismatch warnings.
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Location where the user should drop the downloaded *Desktop app* client JSON.
_GOOGLE_OAUTH_PATH = config.get_config_dir() / "google_oauth_client.json"


def _client_secrets_path() -> Path:
    """Return the path to the client_secret JSON; raise if missing."""
    if _GOOGLE_OAUTH_PATH.exists():
        return _GOOGLE_OAUTH_PATH
    raise RuntimeError(
        f"Google OAuth client secrets not found at {_GOOGLE_OAUTH_PATH}.\n"
        "Download the *Desktop app* (Installed) client JSON from Google Cloud "
        "and save it there."
    )


def do_google_oauth() -> Tuple[str, str | None]:
    """Run the InstalledAppFlow and return (google_id_token, refresh_token?)."""
    secrets = _client_secrets_path()
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)

    google_id_token = getattr(creds, "id_token", None)
    if not google_id_token:
        try:  # pragma: no cover - defensive
            creds.refresh(GARequest())
            google_id_token = getattr(creds, "id_token", None)
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(
                f"Google OAuth succeeded but no ID token available: {exc}"
            ) from exc

    if not google_id_token:
        raise RuntimeError("Google OAuth succeeded but ID token missing.")

    google_refresh_token = getattr(creds, "refresh_token", None)
    return google_id_token, google_refresh_token


def exchange_google_to_firebase(api_key: str, google_id_token: str) -> Tuple[str, str]:
    """Exchange a Google ID token for Firebase ID/refresh tokens.

    Args:
        api_key: Firebase Web API Key (Project settings > General > Web API Key).
        google_id_token: ID token from Google OAuth (do_google_oauth()).

    Returns:
        (firebase_id_token, firebase_refresh_token)
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}"
    payload = {
        # For manual credential exchange, Google docs allow http://localhost.
        "requestUri": "http://localhost",
        "postBody": f"id_token={google_id_token}&providerId=google.com",
        "returnSecureToken": True,
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    try:
        fb_id_token = data["idToken"]
        fb_refresh_token = data["refreshToken"]
    except KeyError as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            f"Firebase exchange response missing field: {exc}; payload={json.dumps(data)[:200]}"
        ) from exc

    return fb_id_token, fb_refresh_token


def refresh_firebase_token(api_key: str, refresh_token: str) -> dict:
    """Refresh a Firebase ID token using the Secure Token Service.

    Args:
        api_key: Firebase Web API Key from your project settings.
        refresh_token: The Firebase refresh token.

    Returns:
        A dictionary containing the new token data from Google, e.g.,
        `id_token`, `refresh_token`, `expires_in`.
    """
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    resp = requests.post(url, data=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # The key names from Google are camelCase with a leading lowercase letter.
    # For consistency with the rest of the app, convert to snake_case.
    return {
        "id_token": data["id_token"],
        "refresh_token": data["refresh_token"],
        "expires_in": data["expires_in"],
    }
