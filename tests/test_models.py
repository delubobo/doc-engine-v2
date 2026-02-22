"""Tests for the DocEngine dataclasses in src/models.py."""

import pytest

from src.models import (
    DocumentMetadata,
    DocumentSection,
    ParsedDocument,
    ParseOptions,
    ProcessingResult,
)


class TestParseOptions:
    """Tests for the ParseOptions dataclass."""

    def test_file_path_required_and_stored(self):
        """file_path must be provided and should be accessible."""
        opts = ParseOptions(file_path="/tmp/test.txt")
        assert opts.file_path == "/tmp/test.txt"

    def test_default_encoding_is_utf8(self):
        """encoding should default to 'utf-8'."""
        opts = ParseOptions(file_path="test.txt")
        assert opts.encoding == "utf-8"

    def test_default_format_is_plain(self):
        """format should default to 'plain'."""
        opts = ParseOptions(file_path="test.txt")
        assert opts.format == "plain"

    def test_default_verbose_is_false(self):
        """verbose should default to False."""
        opts = ParseOptions(file_path="test.txt")
        assert opts.verbose is False

    def test_custom_values_stored(self):
        """All fields should be independently settable."""
        opts = ParseOptions(
            file_path="/f",
            encoding="latin-1",
            format="json",
            verbose=True,
        )
        assert opts.encoding == "latin-1"
        assert opts.format == "json"
        assert opts.verbose is True

    def test_repr_contains_file_path(self):
        """repr should include the file_path value."""
        opts = ParseOptions(file_path="myfile.txt")
        assert "myfile.txt" in repr(opts)


class TestDocumentMetadata:
    """Tests for the DocumentMetadata dataclass."""

    def test_file_path_required_and_stored(self):
        """file_path must be provided and should be accessible."""
        meta = DocumentMetadata(file_path="/tmp/doc.txt")
        assert meta.file_path == "/tmp/doc.txt"

    def test_default_file_size_is_zero(self):
        """file_size should default to 0."""
        meta = DocumentMetadata(file_path="f")
        assert meta.file_size == 0

    def test_default_encoding_is_utf8(self):
        """encoding should default to 'utf-8'."""
        meta = DocumentMetadata(file_path="f")
        assert meta.encoding == "utf-8"

    def test_default_document_type_is_plain(self):
        """document_type should default to 'plain'."""
        meta = DocumentMetadata(file_path="f")
        assert meta.document_type == "plain"

    def test_default_word_count_is_zero(self):
        """word_count should default to 0."""
        meta = DocumentMetadata(file_path="f")
        assert meta.word_count == 0

    def test_default_line_count_is_zero(self):
        """line_count should default to 0."""
        meta = DocumentMetadata(file_path="f")
        assert meta.line_count == 0

    def test_custom_values_stored(self):
        """All fields should be independently settable."""
        meta = DocumentMetadata(
            file_path="/p",
            file_size=512,
            encoding="ascii",
            document_type="csv",
            word_count=7,
            line_count=3,
        )
        assert meta.file_size == 512
        assert meta.encoding == "ascii"
        assert meta.document_type == "csv"
        assert meta.word_count == 7
        assert meta.line_count == 3


class TestDocumentSection:
    """Tests for the DocumentSection dataclass."""

    def test_all_defaults(self):
        """All fields should default to empty/zero values."""
        section = DocumentSection()
        assert section.title == ""
        assert section.content == ""
        assert section.index == 0

    def test_custom_values_stored(self):
        """Explicitly set fields should be accessible."""
        section = DocumentSection(title="Intro", content="Hello world", index=2)
        assert section.title == "Intro"
        assert section.content == "Hello world"
        assert section.index == 2

    def test_repr_contains_title_and_content(self):
        """repr should include title and content values."""
        section = DocumentSection(title="MyTitle", content="MyContent", index=0)
        r = repr(section)
        assert "MyTitle" in r
        assert "MyContent" in r


class TestParsedDocument:
    """Tests for the ParsedDocument dataclass."""

    def test_default_raw_text_is_empty(self):
        """raw_text should default to an empty string."""
        doc = ParsedDocument()
        assert doc.raw_text == ""

    def test_default_sections_is_empty_list(self):
        """sections should default to an empty list."""
        doc = ParsedDocument()
        assert doc.sections == []

    def test_sections_list_is_independent_per_instance(self):
        """Mutating one instance's sections must not affect another."""
        doc1 = ParsedDocument()
        doc2 = ParsedDocument()
        doc1.sections.append(DocumentSection())
        assert len(doc2.sections) == 0

    def test_default_metadata_file_path_is_empty(self):
        """The default-constructed metadata should have an empty file_path."""
        doc = ParsedDocument()
        assert doc.metadata.file_path == ""

    def test_custom_values_stored(self):
        """Explicitly set fields should be accessible."""
        meta = DocumentMetadata(file_path="/tmp/f")
        sec = DocumentSection(title="S", content="C", index=0)
        doc = ParsedDocument(metadata=meta, sections=[sec], raw_text="C")
        assert doc.metadata.file_path == "/tmp/f"
        assert len(doc.sections) == 1
        assert doc.raw_text == "C"


class TestProcessingResult:
    """Tests for the ProcessingResult dataclass."""

    def test_default_success_is_true(self):
        """success should default to True."""
        result = ProcessingResult()
        assert result.success is True

    def test_default_errors_is_empty_list(self):
        """errors should default to an empty list."""
        result = ProcessingResult()
        assert result.errors == []

    def test_default_warnings_is_empty_list(self):
        """warnings should default to an empty list."""
        result = ProcessingResult()
        assert result.warnings == []

    def test_errors_list_is_independent_per_instance(self):
        """Mutating one instance's errors must not affect another."""
        r1 = ProcessingResult()
        r2 = ProcessingResult()
        r1.errors.append("oops")
        assert len(r2.errors) == 0

    def test_warnings_list_is_independent_per_instance(self):
        """Mutating one instance's warnings must not affect another."""
        r1 = ProcessingResult()
        r2 = ProcessingResult()
        r1.warnings.append("heads up")
        assert len(r2.warnings) == 0

    def test_failure_result_stores_errors(self):
        """A failed result should store the provided error messages."""
        result = ProcessingResult(success=False, errors=["something went wrong"])
        assert result.success is False
        assert "something went wrong" in result.errors
