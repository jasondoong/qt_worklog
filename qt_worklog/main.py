import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

from . import config
from .ui.login_window import LoginWindow
from .services.auth import credentials
from .services.auth.token_manager import TokenManager
from .ui.main_window import MainWindow
from .logging_config import setup_logging


def main():
    setup_logging()
    # The QApplication instance must be created before any other Qt widgets.
    app = QApplication(sys.argv)

    # Load configuration
    try:
        config.load_all_configs()
    except config.ConfigError as e:
        config.handle_config_error(app, e)
        return

    # Check if we have stored credentials
    creds = credentials.get_credentials()

    if creds:
        main_window = MainWindow()
        main_window.show()
        token_manager = TokenManager()
        token_manager.login_required.connect(lambda: show_login_window(app))
    else:
        show_login_window(app)

    sys.exit(app.exec())


def show_login_window(app):
    login_window = LoginWindow()
    login_window.show()
    login_window.login_successful.connect(lambda: show_main_window(app))


def show_main_window(app):
    main_window = MainWindow()
    main_window.show()



if __name__ == "__main__":
    main()
