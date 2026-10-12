"""Создание приложения Qt и показ главного окна файлового менеджера."""

import sys

from PyQt5.QtWidgets import QApplication

from file_manager.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Python File Manager")
    window = MainWindow()
    window.show()
    return app.exec_()
