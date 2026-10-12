"""Проверки реестра поддерживаемых расширений файлов."""

from file_manager.services.file_formats import FileKind, is_windows_only_video, kind_for_path


def test_extensions_are_matched_case_insensitively() -> None:
    assert kind_for_path("PHOTO.JPEG") == FileKind.IMAGE
    assert kind_for_path("notes.MD") == FileKind.MARKDOWN


def test_supported_media_kinds() -> None:
    assert kind_for_path("song.mp3") == FileKind.AUDIO


def test_unknown_extension_is_not_previewed() -> None:
    assert kind_for_path("archive.7z") is None


def test_video_is_not_in_in_app_preview_registry() -> None:
    assert kind_for_path("movie.mp4") is None
    assert is_windows_only_video("movie.MP4")
