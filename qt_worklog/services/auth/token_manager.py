from PySide6.QtCore import QObject, QTimer, Signal

from . import google_auth
from . import credentials


class TokenManager(QObject):
    login_required = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_token)
        self.timer.start(55 * 60 * 1000)  # 55 minutes

    def get_token(self) -> str | None:
        """Return the current ID token if available."""
        creds = credentials.get_credentials()
        if creds:
            return creds.get("id_token")
        return None

    def clear_token(self) -> None:
        """Remove any stored credentials."""
        credentials.delete_credentials()

    def refresh_token(self):
        creds = credentials.get_credentials()
        if not creds:
            self.login_required.emit()
            return

        try:
            new_token_data = google_auth.refresh_id_token(creds["refresh_token"])
            creds.update(new_token_data)
            credentials.store_credentials(creds)
            print("Token refreshed successfully.")
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            credentials.delete_credentials()
            self.login_required.emit()
