"""Tests for the DocEngine exception hierarchy in src/exceptions.py."""

import pytest

from src.exceptions import (
    DocEngineConfigError,
    DocEngineEncodingError,
    DocEngineError,
    DocEngineFileError,
    DocEngineFileNotFoundError,
    DocEngineFormatterError,
    DocEngineFormatError,
    DocEngineParseError,
    DocEnginePermissionError,
)


class TestDocEngineError:
    """Tests for the base DocEngineError class."""

    def test_is_subclass_of_exception(self):
        """DocEngineError must derive from the built-in Exception class."""
        assert issubclass(DocEngineError, Exception)

    def test_default_exit_code_is_one(self):
        """When no exit_code is given, it defaults to 1."""
        err = DocEngineError("some error")
        assert err.exit_code == 1

    def test_custom_exit_code_stored(self):
        """A caller-supplied exit_code should be accessible on the instance."""
        err = DocEngineError("some error", exit_code=2)
        assert err.exit_code == 2

    def test_message_accessible_via_str(self):
        """The error message should appear in str() output."""
        err = DocEngineError("specific message")
        assert "specific message" in str(err)

    def test_can_be_caught_as_exception(self):
        """DocEngineError instances must be catchable as generic Exception."""
        with pytest.raises(Exception):
            raise DocEngineError("base error")


class TestDocEngineConfigError:
    """Tests for DocEngineConfigError."""

    def test_inherits_from_doc_engine_error(self):
        """DocEngineConfigError must be a subclass of DocEngineError."""
        assert issubclass(DocEngineConfigError, DocEngineError)

    def test_can_be_raised_and_caught(self):
        """Raising DocEngineConfigError should be catchable by its own type."""
        with pytest.raises(DocEngineConfigError):
            raise DocEngineConfigError("bad config")

    def test_caught_as_base_error(self):
        """DocEngineConfigError should also be catchable as DocEngineError."""
        with pytest.raises(DocEngineError):
            raise DocEngineConfigError("bad config")


class TestDocEngineFileErrors:
    """Tests for the file-error sub-hierarchy."""

    def test_file_error_inherits_base(self):
        """DocEngineFileError must be a subclass of DocEngineError."""
        assert issubclass(DocEngineFileError, DocEngineError)

    def test_not_found_inherits_file_error(self):
        """DocEngineFileNotFoundError must be a subclass of DocEngineFileError."""
        assert issubclass(DocEngineFileNotFoundError, DocEngineFileError)

    def test_permission_inherits_file_error(self):
        """DocEnginePermissionError must be a subclass of DocEngineFileError."""
        assert issubclass(DocEnginePermissionError, DocEngineFileError)

    def test_not_found_can_be_raised(self):
        """DocEngineFileNotFoundError should raise and be catchable."""
        with pytest.raises(DocEngineFileNotFoundError):
            raise DocEngineFileNotFoundError("not found")

    def test_permission_can_be_raised(self):
        """DocEnginePermissionError should raise and be catchable."""
        with pytest.raises(DocEnginePermissionError):
            raise DocEnginePermissionError("permission denied")

    def test_not_found_caught_as_file_error(self):
        """DocEngineFileNotFoundError should be catchable as DocEngineFileError."""
        with pytest.raises(DocEngineFileError):
            raise DocEngineFileNotFoundError("not found")

    def test_permission_caught_as_base(self):
        """DocEnginePermissionError should be catchable as DocEngineError."""
        with pytest.raises(DocEngineError):
            raise DocEnginePermissionError("denied")


class TestDocEngineParseError:
    """Tests for DocEngineParseError and its subclasses."""

    def test_inherits_base(self):
        """DocEngineParseError must be a subclass of DocEngineError."""
        assert issubclass(DocEngineParseError, DocEngineError)

    def test_stores_file_path(self):
        """file_path keyword argument should be stored on the instance."""
        err = DocEngineParseError("parse error", file_path="/tmp/test.txt")
        assert err.file_path == "/tmp/test.txt"

    def test_stores_line_number(self):
        """line_number keyword argument should be stored on the instance."""
        err = DocEngineParseError("parse error", line_number=5)
        assert err.line_number == 5

    def test_stores_column(self):
        """column keyword argument should be stored on the instance."""
        err = DocEngineParseError("parse error", column=10)
        assert err.column == 10

    def test_default_file_path_is_empty_string(self):
        """Default file_path should be an empty string."""
        err = DocEngineParseError("parse error")
        assert err.file_path == ""

    def test_default_line_number_is_zero(self):
        """Default line_number should be 0."""
        err = DocEngineParseError("parse error")
        assert err.line_number == 0

    def test_default_column_is_zero(self):
        """Default column should be 0."""
        err = DocEngineParseError("parse error")
        assert err.column == 0

    def test_encoding_error_inherits_parse_error(self):
        """DocEngineEncodingError must be a subclass of DocEngineParseError."""
        assert issubclass(DocEngineEncodingError, DocEngineParseError)

    def test_format_error_inherits_parse_error(self):
        """DocEngineFormatError must be a subclass of DocEngineParseError."""
        assert issubclass(DocEngineFormatError, DocEngineParseError)

    def test_encoding_error_carries_location(self):
        """DocEngineEncodingError should store file_path and line_number."""
        err = DocEngineEncodingError("bad encoding", file_path="/f", line_number=3)
        assert err.file_path == "/f"
        assert err.line_number == 3

    def test_format_error_carries_location(self):
        """DocEngineFormatError should store file_path and column."""
        err = DocEngineFormatError("bad format", file_path="/g", column=7)
        assert err.file_path == "/g"
        assert err.column == 7


class TestDocEngineFormatterError:
    """Tests for DocEngineFormatterError."""

    def test_inherits_from_base(self):
        """DocEngineFormatterError must be a subclass of DocEngineError."""
        assert issubclass(DocEngineFormatterError, DocEngineError)

    def test_can_be_raised_and_caught(self):
        """Raising DocEngineFormatterError should be catchable by its type."""
        with pytest.raises(DocEngineFormatterError):
            raise DocEngineFormatterError("unknown format")

    def test_message_stored(self):
        """The error message should be accessible via str()."""
        err = DocEngineFormatterError("unsupported: xml")
        assert "xml" in str(err)
