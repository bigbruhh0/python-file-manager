"""Главное окно: навигация по папкам и связь с панелью предпросмотра."""

from pathlib import Path

from PyQt5.QtCore import QDir, QModelIndex, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QFileDialog, QFileSystemModel, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTreeView,
    QVBoxLayout, QWidget,
)

from file_manager.ui.preview_panel import PreviewPanel


class MainWindow(QMainWindow):
    """Окно файлового менеджера; файл открывается двойным щелчком или кнопкой Windows."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Python File Manager")
        self.setMinimumSize(800, 500)
        self.resize(1100, 700)
        self._build_ui()
        self.tree = self.directoryTree
        self.path_edit = self.pathEdit
        self.back_button = self.backButton
        self.forward_button = self.forwardButton
        self.up_button = self.upButton
        self._history: list[Path] = []
        self._history_index = -1

        self.model = QFileSystemModel(self)
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)

        self.directoryTree.setModel(self.model)
        self.directoryTree.doubleClicked.connect(self._open_selected)
        self.directoryTree.selectionModel().currentChanged.connect(self._selection_changed)

        self.preview = PreviewPanel(self.previewContainer)
        self.previewContainer.layout().addWidget(self.preview)
        self.preview.open_button.clicked.connect(self._open_previewed_in_windows)

        self.backButton.clicked.connect(self._go_back)
        self.forwardButton.clicked.connect(self._go_forward)
        self.upButton.clicked.connect(self._go_up)
        self.pathEdit.returnPressed.connect(lambda: self._navigate_to(self.pathEdit.text()))
        self.goButton.clicked.connect(lambda: self._navigate_to(self.pathEdit.text()))
        self.chooseButton.clicked.connect(self._choose_directory)
        self.statusbar.showMessage("Выберите файл для предпросмотра или папку для навигации")

        self._navigate_to(Path.home(), record_history=True)

    def _build_ui(self) -> None:
        """Собрать разметку окна средствами PyQt, без внешнего файла формы."""
        central = QWidget(self)
        main_layout = QVBoxLayout(central)

        navigation_layout = QHBoxLayout()
        self.backButton = QPushButton("Назад", central)
        self.forwardButton = QPushButton("Вперёд", central)
        self.upButton = QPushButton("Вверх", central)
        self.pathLabel = QLabel("Путь:", central)
        self.pathEdit = QLineEdit(central)
        self.goButton = QPushButton("Перейти", central)
        self.chooseButton = QPushButton("Выбрать папку…", central)
        for widget in (
            self.backButton, self.forwardButton, self.upButton, self.pathLabel,
            self.pathEdit, self.goButton, self.chooseButton,
        ):
            navigation_layout.addWidget(widget)
        main_layout.addLayout(navigation_layout)

        self.mainSplitter = QSplitter(Qt.Horizontal, central)
        self.directoryTree = QTreeView(self.mainSplitter)
        self.directoryTree.setMinimumWidth(250)
        self.directoryTree.setAnimated(False)
        self.previewContainer = QWidget(self.mainSplitter)
        self.previewContainerLayout = QVBoxLayout(self.previewContainer)
        self.mainSplitter.addWidget(self.directoryTree)
        self.mainSplitter.addWidget(self.previewContainer)
        self.mainSplitter.setSizes([600, 400])
        main_layout.addWidget(self.mainSplitter)

        self.setCentralWidget(central)
        self.statusbar = self.statusBar()

    def _navigate_to(self, target: str | Path, *, record_history: bool = True) -> None:
        path = Path(target).expanduser()
        if not path.is_dir():
            QMessageBox.warning(self, "Папка не найдена", f"Не удалось открыть папку:\n{path}")
            return
        path = path.resolve()
        self.path_edit.setText(str(path))
        self.directoryTree.setRootIndex(self.model.index(str(path)))
        self.preview.show_path(None)

        if record_history:
            # Новый путь после возврата назад делает старую «ветку вперёд» недействительной.
            del self._history[self._history_index + 1:]
            if not self._history or self._history[-1] != path:
                self._history.append(path)
                self._history_index = len(self._history) - 1
        self._update_navigation_buttons()

    def _choose_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Выберите папку", self.path_edit.text())
        if selected:
            self._navigate_to(selected)

    def _selection_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        path = Path(self.model.filePath(current)) if current.isValid() else None
        self.preview.show_path(path)

    def _open_selected(self, index: QModelIndex) -> None:
        path = Path(self.model.filePath(index))
        if path.is_dir():
            self._navigate_to(path)
        else:
            self._open_with_windows(path)

    def _go_up(self) -> None:
        current = Path(self.path_edit.text())
        parent = current.parent
        if parent != current:
            self._navigate_to(parent)

    def _go_back(self) -> None:
        if self._history_index > 0:
            self._history_index -= 1
            self._navigate_to(self._history[self._history_index], record_history=False)

    def _go_forward(self) -> None:
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._navigate_to(self._history[self._history_index], record_history=False)

    def _update_navigation_buttons(self) -> None:
        self.back_button.setEnabled(self._history_index > 0)
        self.forward_button.setEnabled(self._history_index < len(self._history) - 1)
        current = Path(self.path_edit.text())
        self.upButton.setEnabled(current.parent != current)

    def _open_previewed_in_windows(self) -> None:
        if self.preview.path is not None:
            self._open_with_windows(self.preview.path)

    def _open_with_windows(self, path: Path) -> None:
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve()))):
            QMessageBox.warning(self, "Не удалось открыть файл", f"Windows не смогла открыть:\n{path}")
