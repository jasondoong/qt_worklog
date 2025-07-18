import sys

from PySide6.QtWidgets import QApplication

from . import config
from .ui.login_window import LoginWindow
from .services.auth.token_manager import TokenManager
from .ui.main_window import MainWindow
from .logging_config import setup_logging


import os

def main():
    setup_logging()
    app = QApplication(sys.argv)

    # Load stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
    with open(style_path, "r") as f:
        app.setStyleSheet(f.read())

    try:
        config.load_all_configs()
    except config.ConfigError as e:
        config.handle_config_error(app, e)
        return

    token_manager = TokenManager()

    # These references are kept to prevent the windows from being garbage collected
    global main_window, login_window

    def show_main():
        global main_window
        main_window = MainWindow(token_manager)
        main_window.show()
        if 'login_window' in globals():
            login_window.close()

    def show_login():
        global login_window
        login_window = LoginWindow(token_manager)
        login_window.login_successful.connect(show_main)
        login_window.show()

    token_manager.login_required.connect(show_login)

    if token_manager.get_token():
        show_main()
    else:
        show_login()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
