from PySide6.QtWidgets import QMainWindow, QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Worklog")
        label = QLabel("Welcome to Worklog!")
        self.setCentralWidget(label)
