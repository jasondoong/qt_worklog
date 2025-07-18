import sys

from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout, QMessageBox
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QPixmap

from ..services.auth import google_auth
from ..services import api_client
from ..services.auth import credentials
from .. import config


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
        self.login_button.setObjectName("LoginButton")
        self.login_button.clicked.connect(self.login)

        # Layout
        layout = QGridLayout()
        layout.addWidget(logo_label, 0, 0, 1, 2)
        layout.addWidget(welcome_label, 1, 0, 1, 2)
        layout.addWidget(self.login_button, 2, 0, 1, 2)
        self.setLayout(layout)


    @Slot()
    def login(self):
        try:
            google_id_token, _ = google_auth.do_google_oauth()
            api_key = config.FIREBASE_CONFIG["apiKey"]
            fb_id_token, fb_refresh = google_auth.exchange_google_to_firebase(api_key, google_id_token)
            token_data = {"id_token": fb_id_token, "refresh_token": fb_refresh}
            api_client.authenticate_user(fb_id_token)
            credentials.store_credentials(token_data)
            print("User authenticated and credentials stored.")
            self.login_successful.emit()
            self.close()
        except Exception as e:
            print(f"An error occurred: {e}")
            error_message = f"An error occurred during login: {e}"
            QMessageBox.critical(self, "Login Failed", error_message)
