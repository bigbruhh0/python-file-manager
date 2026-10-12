"""Проверки чтения текста, кодировок и защиты от больших/двоичных файлов."""

from pathlib import Path

import pytest

from file_manager.services.file_reader import MAX_PREVIEW_BYTES, TextPreviewError, read_text_file


def test_reads_utf8_file(tmp_path: Path) -> None:
    sample = tmp_path / "hello.txt"
    sample.write_text("Привет, мир!", encoding="utf-8")
    assert read_text_file(sample) == "Привет, мир!"


def test_reads_cp1251_file(tmp_path: Path) -> None:
    sample = tmp_path / "legacy.txt"
    sample.write_bytes("Привет".encode("cp1251"))
    assert read_text_file(sample) == "Привет"


def test_reads_utf16_file_with_bom(tmp_path: Path) -> None:
    sample = tmp_path / "utf16.txt"
    sample.write_bytes("Привет".encode("utf-16"))
    assert read_text_file(sample) == "Привет"


def test_rejects_large_file_without_reading_it_all(tmp_path: Path) -> None:
    sample = tmp_path / "large.txt"
    sample.write_bytes(b"a" * (MAX_PREVIEW_BYTES + 10))
    with pytest.raises(TextPreviewError, match="больше 2 МБ"):
        read_text_file(sample)


def test_rejects_binary_content(tmp_path: Path) -> None:
    sample = tmp_path / "binary.txt"
    sample.write_bytes(b"header\x00payload")
    with pytest.raises(TextPreviewError, match="двоичный"):
        read_text_file(sample)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_text_file(tmp_path / "missing.txt")
