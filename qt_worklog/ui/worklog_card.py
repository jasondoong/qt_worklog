from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

class WorklogCard(QWidget):
    def __init__(self, worklog):
        super().__init__()
        self.worklog = worklog

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        content_label = QLabel(worklog.get("content", "No content"))
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        self.setLayout(layout)
        self.setObjectName("WorklogCard")
