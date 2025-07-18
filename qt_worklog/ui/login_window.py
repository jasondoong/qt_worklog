import sys

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QPixmap, QScreen

from ..services.auth import google_auth
from ..services.auth.callback_server import CallbackServer
from ..services import api_client
from ..services.auth import credentials


class LoginWindow(QWidget):
    login_successful = Signal()

    def __init__(self, token_manager=None):
        super().__init__()
        self.token_manager = token_manager

        self.setWindowTitle("Login to Worklog")
        self.setFixedSize(300, 200)

        # Center the window
        primary_screen = self.screen().virtualSiblings()[0]
        screen_geometry = primary_screen.availableGeometry()
        self.move(screen_geometry.center() - self.rect().center())


        # Logo
        logo_label = QLabel()
        pixmap = QPixmap("qt_worklog/ui/google_logo.svg")
        logo_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)

        # Welcome message
        welcome_label = QLabel("Welcome to Worklog")
        welcome_label.setAlignment(Qt.AlignCenter)

        # Login button
        self.login_button = QPushButton("Sign in with Google")
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #357ae8;
            }
        """)

        # Layout
        layout = QGridLayout()
        layout.addWidget(logo_label, 0, 0, 1, 2)
        layout.addWidget(welcome_label, 1, 0, 1, 2)
        layout.addWidget(self.login_button, 2, 0, 1, 2)
        self.setLayout(layout)


        self.callback_server = CallbackServer()
        self.callback_server.authorization_code_received.connect(self.handle_auth_code)

    @Slot()
    def login(self):
        self.callback_server.start()
        self.code_verifier = google_auth.open_browser_for_login(self.callback_server.port)

    @Slot(str)
    def handle_auth_code(self, code):
        self.callback_server.stop()
        try:
            token_data = google_auth.exchange_code_for_token(code, self.code_verifier, self.callback_server.port)
            id_token = token_data["id_token"]
            api_client.authenticate_user(id_token)
            credentials.store_credentials(token_data)
            print("User authenticated and credentials stored.")
            self.login_successful.emit()
            self.close()
        except Exception as e:
            print(f"An error occurred: {e}")
