from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

class DayCard(QWidget):
    def __init__(self, date_str):
        super().__init__()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        date_label = QLabel(f"<b>{date_str}</b>")
        self.layout.addWidget(date_label)

        self.setLayout(self.layout)
        self.setObjectName("DayCard")

    def add_worklog_card(self, card):
        self.layout.addWidget(card)
