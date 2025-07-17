import json
import secretstorage

SERVICE_NAME = "worklog-desktop"


def get_connection():
    try:
        return secretstorage.dbus_init()
    except secretstorage.exceptions.SecretServiceNotAvailableException:
        return None


def store_credentials(credentials: dict):
    conn = get_connection()
    if not conn:
        return

    collection = secretstorage.get_default_collection(conn)
    attributes = {"application": SERVICE_NAME}
    collection.create_item("User Credentials", attributes, json.dumps(credentials).encode("utf-8"))


def get_credentials() -> dict | None:
    conn = get_connection()
    if not conn:
        return None

    collection = secretstorage.get_default_collection(conn)
    items = collection.search_items({"application": SERVICE_NAME})
    for item in items:
        return json.loads(item.get_secret().decode("utf-8"))
    return None


def delete_credentials():
    conn = get_connection()
    if not conn:
        return

    collection = secretstorage.get_default_collection(conn)
    items = collection.search_items({"application": SERVICE_NAME})
    for item in items:
        item.delete()
