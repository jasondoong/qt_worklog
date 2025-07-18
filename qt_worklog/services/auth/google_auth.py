import base64
import hashlib
import os
import webbrowser

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


def get_authorization_url(code_challenge: str) -> str:
    client_id = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["client_id"]
    redirect_uri = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["redirect_uris"][0]
    return (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20email%20profile&"
        f"code_challenge={code_challenge}&"
        "code_challenge_method=S256"
    )


def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    client_id = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["client_id"]
    client_secret = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["client_secret"]
    redirect_uri = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["redirect_uris"][0]

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        },
    )
    response.raise_for_status()
    return response.json()


def refresh_id_token(refresh_token: str) -> dict:
    client_id = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["client_id"]
    client_secret = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["client_secret"]

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    return response.json()


def open_browser_for_login():
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    url = get_authorization_url(code_challenge)
    QDesktopServices.openUrl(QUrl(url))
    return code_verifier
