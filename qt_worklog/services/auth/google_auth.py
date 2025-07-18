import base64
import hashlib
import os

import json
import requests
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from ... import config


def generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("utf-8")


def generate_code_challenge(verifier: str) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("utf-8")
    )


def _client_conf() -> dict:
    """Return the Google OAuth client configuration regardless of source."""
    cfg = config.GOOGLE_OAUTH_CLIENT_CONFIG
    return cfg.get("installed", cfg)


def get_authorization_url(code_challenge: str, port: int) -> str:
    client_conf = _client_conf()
    client_id = client_conf["client_id"]
    redirect_uri_base = client_conf["redirect_uris"][0]

    # If the configured redirect URI is http://localhost with no port specified,
    # use the dynamically chosen port from the callback server.
    parsed = QUrl(redirect_uri_base)
    if parsed.scheme() == "http" and parsed.host() == "localhost" and parsed.port() == -1:
        redirect_uri = f"http://localhost:{port}"
    else:
        redirect_uri = redirect_uri_base

    return (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20https://www.googleapis.com/auth/userinfo.email%20https://www.googleapis.com/auth/userinfo.profile&"
        f"code_challenge={code_challenge}&"
        "code_challenge_method=S256"
    )


def exchange_code_for_token(code: str, code_verifier: str, port: int) -> dict:
    """Exchange OAuth authorization code for a Firebase ID token."""

    client_conf = _client_conf()
    client_id = client_conf["client_id"]
    redirect_uri_base = client_conf["redirect_uris"][0]

    parsed = QUrl(redirect_uri_base)
    if parsed.scheme() == "http" and parsed.host() == "localhost" and parsed.port() == -1:
        redirect_uri = f"http://localhost:{port}"
    else:
        redirect_uri = redirect_uri_base

    api_key = config.FIREBASE_CONFIG["apiKey"]

    payload = {
        "requestUri": redirect_uri,
        "postBody": (
            f"providerId=google.com&code={code}&code_verifier={code_verifier}&"
            f"client_id={client_id}&redirect_uri={redirect_uri}"
        ),
        "returnSecureToken": True,
    }

    response = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    try:
        id_token = data["idToken"]
        refresh_token = data["refreshToken"]
    except KeyError as exc:  # defensive
        raise RuntimeError(
            f"Firebase exchange response missing field: {exc}; payload={json.dumps(data)[:200]}"
        ) from exc

    # Return keys in snake_case to match the rest of the application
    result = {"id_token": id_token, "refresh_token": refresh_token}
    if "expiresIn" in data:
        result["expires_in"] = data["expiresIn"]
    return result


def refresh_id_token(refresh_token: str) -> dict:
    """Refresh the Firebase ID token using the secure token endpoint."""

    api_key = config.FIREBASE_CONFIG["apiKey"]

    response = requests.post(
        f"https://securetoken.googleapis.com/v1/token?key={api_key}",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    response.raise_for_status()
    return response.json()


def open_browser_for_login(port: int):
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    url = get_authorization_url(code_challenge, port)
    QDesktopServices.openUrl(QUrl(url))
    return code_verifier
