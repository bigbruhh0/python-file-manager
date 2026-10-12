"""Общие фикстуры для запуска тестов Qt без реального окна на экране."""

import os

import pytest


@pytest.fixture(scope="session")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
