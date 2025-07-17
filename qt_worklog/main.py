"""Entry point for the Qt Worklog application."""

from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QLabel


def main() -> None:
    """Run the main application."""
    app = QApplication(sys.argv)
    label = QLabel("Hello, PySide6!")
    label.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
