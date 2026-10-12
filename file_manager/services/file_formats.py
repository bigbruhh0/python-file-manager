"""Единый список расширений и определение формата для предпросмотра."""

from enum import Enum
from pathlib import Path


class FileKind(str, Enum):
    """Виды данных, для которых приложение умеет показывать предпросмотр."""

    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    AUDIO = "audio"


FORMAT_GROUPS: dict[FileKind, frozenset[str]] = {
    FileKind.TEXT: frozenset({
        ".txt", ".log", ".csv", ".tsv", ".json", ".xml", ".yaml",
        ".yml", ".ini", ".cfg", ".toml", ".py", ".html", ".css",
        ".js", ".sql", ".bat", ".ps1",
    }),
    FileKind.MARKDOWN: frozenset({".md", ".markdown", ".mdown", ".mkd"}),
    FileKind.IMAGE: frozenset({
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff",
    }),
    FileKind.AUDIO: frozenset({
        ".mp3", ".wav", ".ogg", ".oga", ".m4a", ".aac", ".flac", ".wma",
    }),
}

# Видео вынесено отдельно: его можно распознать и подсказать открыть в Windows,
# но оно не относится к форматам встроенного предпросмотра.
WINDOWS_ONLY_VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".mpeg", ".mpg", ".webm",
})


def kind_for_path(path: str | Path) -> FileKind | None:
    """Вернуть вид предпросмотра по расширению или None для неподдерживаемого файла."""
    suffix = Path(path).suffix.lower()
    return next((kind for kind, extensions in FORMAT_GROUPS.items() if suffix in extensions), None)


def is_windows_only_video(path: str | Path) -> bool:
    """Определить видеоформат, который можно открыть только внешним проигрывателем."""
    return Path(path).suffix.lower() in WINDOWS_ONLY_VIDEO_EXTENSIONS
