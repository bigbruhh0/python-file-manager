"""Безопасное чтение небольших текстовых файлов без зависимости от Qt."""

from pathlib import Path

MAX_PREVIEW_BYTES = 2 * 1024 * 1024


class TextPreviewError(Exception):
    """The file cannot be safely shown as text in the preview panel."""


def read_text_file(path: str | Path) -> str:
    """Прочитать файл с лимитом размера и поддержкой распространённых кодировок."""
    file_path = Path(path)
    with file_path.open("rb") as source:
        # Читаем на один байт сверх лимита: этого достаточно узнать, что файл слишком большой.
        content = source.read(MAX_PREVIEW_BYTES + 1)
    if len(content) > MAX_PREVIEW_BYTES:
        raise TextPreviewError(
            f"Файл больше {MAX_PREVIEW_BYTES // (1024 * 1024)} МБ. "
            "Откройте его в стандартном приложении Windows."
        )

    try:
        # BOM позволяет надёжно распознать UTF-16; нулевой байт часто указывает на бинарный файл.
        if content.startswith((b"\xff\xfe", b"\xfe\xff")):
            return content.decode("utf-16")
        if b"\x00" in content:
            raise TextPreviewError("Файл похож на двоичный и не показывается как текст.")
        try:
            # Сначала пробуем UTF-8, затем типичную для Windows кириллическую кодировку.
            return content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return content.decode("cp1251")
    except UnicodeDecodeError as error:
        raise TextPreviewError("Не удалось определить кодировку файла.") from error
