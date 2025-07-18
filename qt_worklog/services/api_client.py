import base64
import json
import requests
from typing import Any, Callable, Dict, Optional

from ..config import FIREBASE_CONFIG

API_URL = "https://work-log.cc/api"


def _handle_auth(resp: requests.Response, sign_out: Optional[Callable[[], None]] = None) -> None:
    """Trigger sign out if response indicates authentication failure."""
    if resp.status_code in (401, 403):
        if sign_out:
            sign_out()


def authenticate_user(id_token: str) -> dict:
    """Create or update the user on the backend using the Firebase ID token."""

    # Decode the JWT without verification to extract basic user info. This
    # avoids pulling in heavy dependencies solely for base64 decoding.
    try:
        payload = id_token.split(".")[1]
        padded = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except Exception:
        claims = {}

    data = {
        "id": claims.get("user_id"),
        "avatar_link": claims.get("picture"),
        "email": claims.get("email"),
        "name": claims.get("name"),
    }

    response = requests.post(
        f"{API_URL}/users/",
        json=data,
        headers={"Authorization": f"Bearer {id_token}"},
    )
    response.raise_for_status()
    return response.json()


def get_worklogs(token: str, *, sign_out: Optional[Callable[[], None]] = None, **params: Any) -> Dict[str, Any]:
    """Return worklogs JSON from the backend.

    Parameters
    ----------
    token:
        ID token for the current user.
    sign_out:
        Optional callback invoked when the server responds with 401 or 403.
    params:
        Query parameters forwarded to the API.
    """
    url = f"{API_URL}/worklogs"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    _handle_auth(resp, sign_out)
    resp.raise_for_status()
    return resp.json()


def update_worklog(
    token: str,
    worklog_id: str,
    *,
    content: str,
    record_time: str,
    tag_id: str = None,
    sign_out: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """PATCH update a single worklog entry.

    Parameters
    ----------
    token: Bearer token
    worklog_id: worklog id string
    content: new content
    record_time: ISO8601 string
    tag_id: (optional) tag id
    sign_out: optional callback for 401/403
    """
    url = f"{API_URL}/worklogs/{worklog_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
    }
    data = {
        "content": content,
        "record_time": record_time,
    }
    if tag_id:
        data["tag_id"] = tag_id
    resp = requests.patch(url, headers=headers, json=data, timeout=10)
    _handle_auth(resp, sign_out)
    resp.raise_for_status()
    print(resp.json())
    return resp.json()


def delete_worklog(
    token: str,
    worklog_id: str,
    *,
    sign_out: Optional[Callable[[], None]] = None,
) -> None:
    """DELETE a single worklog entry.

    Parameters
    ----------
    token: Bearer token
    worklog_id: worklog id string
    sign_out: optional callback for 401/403
    """
    url = f"{API_URL}/worklogs/{worklog_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/plain, */*",
    }
    resp = requests.delete(url, headers=headers, timeout=10)
    _handle_auth(resp, sign_out)
    resp.raise_for_status()
    # 通常刪除不回傳內容
    return None
