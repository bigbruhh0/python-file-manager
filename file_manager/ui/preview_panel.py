"""Правая панель предпросмотра текста, Markdown, изображений и аудио."""

from pathlib import Path

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QImageReader, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QTextBrowser, QTextEdit,
    QVBoxLayout, QWidget,
)

from file_manager.services.file_formats import FileKind, is_windows_only_video, kind_for_path
from file_manager.services.file_reader import TextPreviewError, read_text_file


class PreviewPanel(QWidget):
    """Показывает поддерживаемый файл внутри приложения и предлагает открыть его в Windows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.path: Path | None = None
        self._image: QPixmap | None = None
        self._player: QMediaPlayer | None = None
        self._media_error: QLabel | None = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)

        heading = QLabel("Предпросмотр", self)
        heading.setStyleSheet("font-size: 16px; font-weight: bold")
        self._layout.addWidget(heading)

        self.name_label = QLabel("Выберите файл", self)
        self.name_label.setWordWrap(True)
        self._layout.addWidget(self.name_label)

        self.open_button = QPushButton("Открыть в Windows", self)
        self.open_button.setEnabled(False)
        self._layout.addWidget(self.open_button)

        self.content = QWidget(self)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.content, 1)

    def show_path(self, path: Path | None) -> None:
        # При смене выбора важно остановить старое аудио и удалить его виджеты.
        self._stop_player()
        self.path = path
        self._image = None
        self._clear_content()

        self.open_button.setEnabled(path is not None and path.is_file())

        if path is None:
            self.name_label.setText("Выберите файл")
            return
        if path.is_dir():
            self.name_label.setText(path.name or str(path))
            self._show_message("Это папка. Откройте её двойным щелчком.")
            return

        self.name_label.setText(path.name)
        kind = kind_for_path(path)
        if kind == FileKind.TEXT:
            self._show_text(path)
        elif kind == FileKind.MARKDOWN:
            self._show_markdown(path)
        elif kind == FileKind.IMAGE:
            self._show_image(path)
        elif kind == FileKind.AUDIO:
            self._show_audio(path)
        elif is_windows_only_video(path):
            # Видео намеренно не запускается во встроенном плеере: предлагаем Windows.
            self._show_message("Встроенный просмотр видео отключён. Нажмите «Открыть в Windows».")
        else:
            self._show_message("Предпросмотр этого формата недоступен. Можно открыть файл в Windows.")

    def _clear_content(self) -> None:
        self._stop_player()
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_message(self, message: str) -> None:
        """Показать подсказку в области предпросмотра вместо содержимого файла."""
        # Родитель content позволяет удалить эту надпись вместе с предыдущим просмотром.
        label = QLabel(message, self.content)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(label)

    def _show_text(self, path: Path) -> None:
        viewer = QTextEdit(self.content)
        viewer.setReadOnly(True)
        try:
            viewer.setPlainText(read_text_file(path))
        except (OSError, UnicodeError, TextPreviewError) as error:
            viewer.setPlainText(f"Не удалось прочитать файл: {error}")
        self.content_layout.addWidget(viewer)

    def _show_markdown(self, path: Path) -> None:
        viewer = QTextBrowser(self.content)
        viewer.setOpenExternalLinks(True)
        # Без базовой папки относительные ссылки на картинки внутри Markdown не найдутся.
        viewer.document().setBaseUrl(QUrl.fromLocalFile(str(path.resolve().parent) + "/"))
        viewer.setSearchPaths([str(path.resolve().parent)])
        try:
            viewer.setMarkdown(read_text_file(path))
        except (OSError, UnicodeError, TextPreviewError) as error:
            viewer.setPlainText(f"Не удалось прочитать файл: {error}")
        self.content_layout.addWidget(viewer)

    def _show_image(self, path: Path) -> None:
        viewer = QLabel(self.content)
        viewer.setAlignment(Qt.AlignCenter)
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image_size = reader.size()
        if image_size.isValid():
            # Уменьшаем до чтения, чтобы огромная фотография не загружалась целиком в память.
            image_size.scale(1600, 1200, Qt.KeepAspectRatio)
            reader.setScaledSize(image_size)
        image = reader.read()
        self._image = QPixmap.fromImage(image) if not image.isNull() else None
        if self._image is None:
            self._image = None
            viewer.setText(f"Не удалось показать изображение: {reader.errorString()}")
        else:
            self._set_scaled_image(viewer)
        viewer.setProperty("is_image_preview", True)
        self.content_layout.addWidget(viewer)

    def _set_scaled_image(self, viewer: QLabel) -> None:
        if self._image is not None:
            viewer.setPixmap(self._image.scaled(
                self.content.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ))

    def _show_audio(self, path: Path) -> None:
        player = QMediaPlayer(self)
        # Сохраняем ссылку на плеер: иначе сборщик мусора может остановить воспроизведение.
        self._player = player
        player.setMedia(QMediaContent(QUrl.fromLocalFile(str(path.resolve()))))

        description = QLabel("Аудиофайл. Нажмите «Воспроизвести» для прослушивания.", self.content)
        description.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(description, 1)

        controls = QHBoxLayout()
        play = QPushButton("Воспроизвести", self.content)
        pause = QPushButton("Пауза", self.content)
        position = QSlider(Qt.Horizontal, self.content)
        position.setRange(0, 0)
        play.clicked.connect(player.play)
        pause.clicked.connect(player.pause)
        player.durationChanged.connect(lambda duration: position.setRange(0, duration))
        player.positionChanged.connect(position.setValue)
        position.sliderMoved.connect(player.setPosition)
        controls.addWidget(play)
        controls.addWidget(pause)
        controls.addWidget(position, 1)
        self.content_layout.addLayout(controls)

        self._media_error = QLabel("", self.content)
        self._media_error.setWordWrap(True)
        self._media_error.hide()
        self.content_layout.addWidget(self._media_error)
        player.error.connect(self._show_audio_error)

    def _show_audio_error(self, _error) -> None:
        if self._player is not None and self._media_error is not None:
            self._media_error.setText(
                f"Не удалось воспроизвести аудио: {self._player.errorString()}\n"
                "Попробуйте открыть файл в Windows."
            )
            self._media_error.show()

    def _stop_player(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._player.deleteLater()
            self._player = None
        self._media_error = None

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        super().resizeEvent(event)
        if self._image is not None:
            for index in range(self.content_layout.count()):
                widget = self.content_layout.itemAt(index).widget()
                if isinstance(widget, QLabel) and widget.property("is_image_preview"):
                    self._set_scaled_image(widget)
                    break
