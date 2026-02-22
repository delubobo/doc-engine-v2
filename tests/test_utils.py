"""Tests for the helper utilities in src/utils.py."""

import os
import platform

import pytest

from src.exceptions import (
    DocEngineFileNotFoundError,
    DocEnginePermissionError,
)
from src.utils import (
    count_lines,
    count_words,
    is_readable_file,
    normalize_path,
    read_file_bytes,
)


class TestReadFileBytes:
    """Tests for read_file_bytes."""

    def test_reads_file_content(self, tmp_path):
        """Should return the exact bytes written to a file."""
        f = tmp_path / "hello.txt"
        f.write_bytes(b"hello bytes")
        assert read_file_bytes(str(f)) == b"hello bytes"

    def test_raises_not_found_for_missing_file(self, tmp_path):
        """Should raise DocEngineFileNotFoundError for a non-existent path."""
        missing = str(tmp_path / "nonexistent.txt")
        with pytest.raises(DocEngineFileNotFoundError):
            read_file_bytes(missing)

    def test_raises_permission_error(self, tmp_path):
        """Should raise DocEnginePermissionError when file is unreadable.

        Skipped on Windows because chmod(0o000) is not enforced.
        """
        if platform.system() == "Windows":
            pytest.skip("chmod not enforced on Windows")
        f = tmp_path / "noperm.txt"
        f.write_bytes(b"secret")
        os.chmod(str(f), 0o000)
        try:
            with pytest.raises(DocEnginePermissionError):
                read_file_bytes(str(f))
        finally:
            os.chmod(str(f), 0o644)

    def test_reads_empty_file_as_empty_bytes(self, tmp_path):
        """Should return empty bytes for an empty file."""
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        assert read_file_bytes(str(f)) == b""

    def test_reads_arbitrary_binary_content(self, tmp_path):
        """Should faithfully return binary content including null bytes."""
        data = bytes(range(256))
        f = tmp_path / "binary.bin"
        f.write_bytes(data)
        assert read_file_bytes(str(f)) == data

    def test_reads_unicode_text_file(self, tmp_path):
        """Should return the raw UTF-8 bytes of a text file."""
        text = "Héllo wörld"
        f = tmp_path / "unicode.txt"
        f.write_text(text, encoding="utf-8")
        result = read_file_bytes(str(f))
        assert result == text.encode("utf-8")


class TestNormalizePath:
    """Tests for normalize_path."""

    def test_returns_absolute_path(self):
        """Output must always be an absolute path."""
        result = normalize_path("some/relative/path.txt")
        assert os.path.isabs(result)

    def test_removes_double_dots(self):
        """Double-dot components should be resolved away."""
        result = normalize_path("/tmp/../tmp/test.txt")
        assert ".." not in result

    def test_removes_single_dot(self):
        """Single-dot components should be resolved away."""
        result = normalize_path("/tmp/./test.txt")
        assert "/." not in result

    def test_returns_string_type(self):
        """Return type must be str."""
        assert isinstance(normalize_path("/tmp/test.txt"), str)

    def test_absolute_path_normalised_consistently(self, tmp_path):
        """An absolute path should normalise to itself (modulo platform)."""
        absolute = str(tmp_path / "file.txt")
        result = normalize_path(absolute)
        assert os.path.normpath(result) == os.path.normpath(absolute)


class TestIsReadableFile:
    """Tests for is_readable_file."""

    def test_returns_true_for_readable_file(self, tmp_path):
        """Should return True for an existing, readable file."""
        f = tmp_path / "readable.txt"
        f.write_text("content")
        assert is_readable_file(str(f)) is True

    def test_returns_false_for_missing_file(self, tmp_path):
        """Should return False when the file does not exist."""
        missing = str(tmp_path / "missing.txt")
        assert is_readable_file(missing) is False

    def test_returns_false_for_directory(self, tmp_path):
        """Should return False when the path is a directory."""
        assert is_readable_file(str(tmp_path)) is False


class TestCountWords:
    """Tests for count_words."""

    def test_simple_sentence(self):
        """Should count space-separated words correctly."""
        assert count_words("hello world foo") == 3

    def test_empty_string_returns_zero(self):
        """An empty string has no words."""
        assert count_words("") == 0

    def test_whitespace_only_returns_zero(self):
        """A string of only whitespace has no words."""
        assert count_words("   \t\n  ") == 0

    def test_single_word(self):
        """A single word with no spaces should count as one."""
        assert count_words("hello") == 1

    def test_multiple_spaces_between_words(self):
        """Multiple spaces between words should not inflate the count."""
        assert count_words("one   two   three") == 3

    def test_newlines_as_separators(self):
        """Newline-separated tokens should each count as one word."""
        assert count_words("one\ntwo\nthree") == 3

    def test_tabs_as_separators(self):
        """Tab-separated tokens should each count as one word."""
        assert count_words("a\tb\tc") == 3


class TestCountLines:
    """Tests for count_lines."""

    def test_empty_string_returns_zero(self):
        """An empty string has zero lines."""
        assert count_lines("") == 0

    def test_single_line_without_newline(self):
        """A string with no newline should be one line."""
        assert count_lines("hello") == 1

    def test_single_line_with_trailing_newline(self):
        """A trailing newline should not add an extra line."""
        assert count_lines("hello\n") == 1

    def test_multiple_lines(self):
        """Should count each newline-separated segment as a line."""
        assert count_lines("line1\nline2\nline3") == 3

    def test_trailing_newline_does_not_add_line(self):
        """'a\\nb\\n' is two lines, not three."""
        assert count_lines("a\nb\n") == 2

    def test_only_newlines(self):
        """Three newlines produce three (empty) lines."""
        assert count_lines("\n\n\n") == 3

    def test_mixed_content(self):
        """A realistic multi-line text should be counted correctly."""
        text = "Hello world\nThis is line two\nAnd line three"
        assert count_lines(text) == 3
