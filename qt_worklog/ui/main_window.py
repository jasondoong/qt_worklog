from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon

import datetime as _dt
from collections import defaultdict
from typing import Any, Iterable, Mapping
from ..services import api_client
from .login_window import LoginWindow
from .worklog_card import WorklogCard
from .day_card import DayCard
from .flow_layout import FlowLayout


class MainWindow(QMainWindow):
    def __init__(self, token_manager):
        super().__init__()
        self.token_manager = token_manager
        self._current_month: _dt.date | None = None
        self._logs: list[Mapping[str, Any]] = []

        self.setWindowTitle("Worklog")
        self.setMinimumSize(1024, 768)

        # Header
        header = QWidget()
        header.setObjectName("Header")
        header_layout = QGridLayout()
        header.setLayout(header_layout)

        self._month_lbl = QLabel("Month")
        prev_btn = QPushButton(QIcon.fromTheme("go-previous"), "")
        next_btn = QPushButton(QIcon.fromTheme("go-next"), "")
        logout_btn = QPushButton(QIcon.fromTheme("system-log-out"), "")

        prev_btn.clicked.connect(self._on_prev_month)
        next_btn.clicked.connect(self._on_next_month)
        logout_btn.clicked.connect(self.on_logout)

        # Add left spacer
        header_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 0
        )

        # Center controls
        header_layout.addWidget(prev_btn, 0, 1)
        header_layout.addWidget(self._month_lbl, 0, 2)
        header_layout.addWidget(next_btn, 0, 3)

        # Add right spacer
        header_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 4
        )

        # Right-aligned logout button
        header_layout.addWidget(logout_btn, 0, 5)


        # Main content area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_content = QWidget()
        self.main_content_layout = FlowLayout(self.main_content, 10, 10)
        self.main_content.setLayout(self.main_content_layout)
        self.scroll_area.setWidget(self.main_content)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(header)
        main_layout.addWidget(self.scroll_area)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setStatusBar(QStatusBar(self))

        self.refresh()

    @Slot()
    def on_logout(self):
        self.token_manager.clear_token()
        self.login_window = LoginWindow(self.token_manager)
        self.login_window.show()
        self.close()

    def refresh(self):
        self.statusBar().showMessage("Refreshing worklogs...")
        token = self.token_manager.get_token()
        if not token:
            return
        try:
            logs = api_client.get_worklogs(token, sign_out=self.on_logout) or []
        except Exception as e:
            self.statusBar().showMessage(f"Error refreshing worklogs: {e}", 5000)
            return

        if not isinstance(logs, Iterable):
            return

        self._logs = list(logs)

        if self._current_month is None:
            self._current_month = self._get_newest_month(self._logs)

        self._build_grid()

    def _get_newest_month(self, logs: Iterable[Mapping[str, Any]]) -> _dt.date:
        newest: _dt.date | None = None
        for rec in logs:
            rt = rec.get("record_time")
            if not rt:
                continue
            s = str(rt)
            try:
                dt = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
            except Exception:
                try:
                    dt = _dt.datetime.fromisoformat(s[:19])
                except Exception:
                    continue
            d = dt.date()
            if newest is None or d > newest:
                newest = d
        if newest is None:
            newest = _dt.date.today()
        return newest.replace(day=1)

    def _build_grid(self):
        groups: dict[_dt.date, list[Mapping[str, Any]]] = defaultdict(list)
        for rec in self._logs:
            rt = rec.get("record_time")
            if rt:
                s = str(rt)
                try:
                    dt = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
                    d = dt.date()
                except Exception:
                    try:
                        d = _dt.date.fromisoformat(s[:10])
                    except Exception:
                        d = _dt.date.today()
            else:
                d = _dt.date.today()

            if (
                self._current_month
                and d.year == self._current_month.year
                and d.month == self._current_month.month
            ):
                groups[d].append(rec)

        # Clear existing widgets
        while self.main_content_layout.count():
            child = self.main_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for d in sorted(groups.keys(), reverse=True):
            day_card = DayCard(d.strftime('%A, %B %d, %Y'))
            for log in groups[d]:
                card = WorklogCard(log)
                day_card.add_worklog_card(card)
            self.main_content_layout.addWidget(day_card)

        self._month_lbl.setText(
            self._current_month.strftime("%B %Y")
            if self._current_month
            else "No date"
        )
        self.statusBar().clearMessage()

    def _shift_month(self, delta: int):
        if self._current_month is None:
            self._current_month = _dt.date.today().replace(day=1)
        month = self._current_month.month + delta
        year = self._current_month.year
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        self._current_month = _dt.date(year, month, 1)
        self._build_grid()

    @Slot()
    def _on_prev_month(self):
        self._shift_month(-1)

    @Slot()
    def _on_next_month(self):
        self._shift_month(1)
