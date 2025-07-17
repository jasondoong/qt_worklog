import sys

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Slot, Signal

from ..services.auth import google_auth
from ..services.auth.callback_server import CallbackServer
from ..services import api_client
from ..services.auth import credentials


class LoginWindow(QWidget):
    login_successful = Signal()
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login to Worklog")

        self.login_button = QPushButton("Sign in with Google")
        self.login_button.clicked.connect(self.login)

        layout = QVBoxLayout()
        layout.addWidget(self.login_button)
        self.setLayout(layout)

        self.callback_server = CallbackServer()
        self.callback_server.authorization_code_received.connect(self.handle_auth_code)

    @Slot()
    def login(self):
        self.callback_server.start()
        self.code_verifier = google_auth.open_browser_for_login()

    @Slot(str)
    def handle_auth_code(self, code):
        self.callback_server.stop()
        try:
            token_data = google_auth.exchange_code_for_token(code, self.code_verifier)
            id_token = token_data["id_token"]
            api_client.authenticate_user(id_token)
            credentials.store_credentials(token_data)
            print("User authenticated and credentials stored.")
            self.login_successful.emit()
            self.close()
        except Exception as e:
            print(f"An error occurred: {e}")
