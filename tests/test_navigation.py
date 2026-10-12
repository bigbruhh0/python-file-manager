"""Проверки переходов по папкам и предпросмотра выбранных файлов."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QTextEdit

from file_manager.ui.main_window import MainWindow


def test_up_and_history_navigation(qapp, tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = first / "second"
    second.mkdir(parents=True)

    window = MainWindow()
    try:
        window._navigate_to(first)
        window._navigate_to(second)
        assert Path(window.path_edit.text()) == second

        window._go_up()
        assert Path(window.path_edit.text()) == first

        window._go_back()
        assert Path(window.path_edit.text()) == second
        window._go_forward()
        assert Path(window.path_edit.text()) == first
    finally:
        window.close()


def test_up_is_disabled_at_drive_root(qapp, tmp_path: Path) -> None:
    window = MainWindow()
    try:
        window._navigate_to(Path(tmp_path.anchor))
        assert not window.up_button.isEnabled()
    finally:
        window.close()


def test_selecting_text_shows_preview_and_windows_button(qapp, tmp_path: Path, monkeypatch) -> None:
    sample = tmp_path / "preview.txt"
    sample.write_text("Preview works", encoding="utf-8")
    opened: list[Path] = []

    window = MainWindow()
    try:
        window.show()
        window._navigate_to(tmp_path)
        index = window.model.index(str(sample))
        assert index.isValid()
        window.tree.setCurrentIndex(index)
        qapp.processEvents()

        viewer = window.preview.content.findChild(QTextEdit)
        assert window.preview.path == sample
        assert viewer is not None
        assert viewer.toPlainText() == "Preview works"
        assert window.preview.open_button.isEnabled()

        monkeypatch.setattr(window, "_open_with_windows", lambda path: opened.append(path))
        QTest.mouseClick(window.preview.open_button, Qt.LeftButton)
        assert opened == [sample]
    finally:
        window.close()
