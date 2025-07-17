import requests

from ..config import FIREBASE_CONFIG

API_URL = "https://work-log.cc/api"


def authenticate_user(id_token: str) -> dict:
    response = requests.post(
        f"{API_URL}/users/",
        headers={"Authorization": f"Bearer {id_token}"},
    )
    response.raise_for_status()
    return response.json()
