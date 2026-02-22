"""Tests for output formatting logic in src/formatter.py."""

import json

import pytest

from src.exceptions import DocEngineFormatterError
from src.formatter import _format_json, _format_plain, _format_table, format_result
from src.models import DocumentMetadata, DocumentSection, ParsedDocument, ProcessingResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_result() -> ProcessingResult:
    """Return a ProcessingResult with metadata but no sections."""
    meta = DocumentMetadata(
        file_path="/tmp/test.txt",
        file_size=50,
        encoding="utf-8",
        document_type="plain",
        word_count=5,
        line_count=2,
    )
    doc = ParsedDocument(metadata=meta, sections=[], raw_text="")
    return ProcessingResult(document=doc, success=True)


@pytest.fixture
def result_with_sections() -> ProcessingResult:
    """Return a ProcessingResult containing two named sections."""
    meta = DocumentMetadata(
        file_path="/tmp/report.txt",
        file_size=200,
        encoding="utf-8",
        document_type="plain",
        word_count=20,
        line_count=5,
    )
    sections = [
        DocumentSection(title="Intro", content="Introduction text", index=0),
        DocumentSection(title="Body", content="Body text here", index=1),
    ]
    doc = ParsedDocument(metadata=meta, sections=sections, raw_text="")
    return ProcessingResult(document=doc, success=True)


# ---------------------------------------------------------------------------
# _format_plain
# ---------------------------------------------------------------------------


class TestFormatPlain:
    """Tests for _format_plain."""

    def test_contains_file_path(self, minimal_result):
        """Output should include the document file path."""
        output = _format_plain(minimal_result)
        assert "/tmp/test.txt" in output

    def test_contains_encoding(self, minimal_result):
        """Output should include the encoding field."""
        output = _format_plain(minimal_result)
        assert "utf-8" in output

    def test_contains_document_type(self, minimal_result):
        """Output should include the document type."""
        output = _format_plain(minimal_result)
        assert "plain" in output

    def test_contains_section_titles(self, result_with_sections):
        """Output should include each section title."""
        output = _format_plain(result_with_sections)
        assert "Intro" in output
        assert "Body" in output

    def test_contains_section_content(self, result_with_sections):
        """Output should include each section's content."""
        output = _format_plain(result_with_sections)
        assert "Introduction text" in output

    def test_returns_string(self, minimal_result):
        """Return type should be str."""
        assert isinstance(_format_plain(minimal_result), str)

    def test_no_sections_still_produces_metadata(self, minimal_result):
        """Even with no sections, metadata header should appear."""
        output = _format_plain(minimal_result)
        assert "Words:" in output


# ---------------------------------------------------------------------------
# _format_json
# ---------------------------------------------------------------------------


class TestFormatJson:
    """Tests for _format_json."""

    def test_output_is_valid_json(self, minimal_result):
        """Output should be parseable by json.loads."""
        output = _format_json(minimal_result)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_metadata_key_present(self, minimal_result):
        """Top-level 'metadata' key should exist."""
        parsed = json.loads(_format_json(minimal_result))
        assert "metadata" in parsed

    def test_metadata_file_path(self, minimal_result):
        """metadata.file_path should equal the document path."""
        parsed = json.loads(_format_json(minimal_result))
        assert parsed["metadata"]["file_path"] == "/tmp/test.txt"

    def test_sections_key_present(self, minimal_result):
        """Top-level 'sections' key should exist."""
        parsed = json.loads(_format_json(minimal_result))
        assert "sections" in parsed

    def test_sections_count_matches(self, result_with_sections):
        """sections array length should match the document's section count."""
        parsed = json.loads(_format_json(result_with_sections))
        assert len(parsed["sections"]) == 2

    def test_success_field_true(self, minimal_result):
        """'success' field should reflect the result's success attribute."""
        parsed = json.loads(_format_json(minimal_result))
        assert parsed["success"] is True

    def test_errors_field_present(self, minimal_result):
        """'errors' key should exist and be a list."""
        parsed = json.loads(_format_json(minimal_result))
        assert isinstance(parsed["errors"], list)

    def test_returns_string(self, minimal_result):
        """Return type should be str."""
        assert isinstance(_format_json(minimal_result), str)


# ---------------------------------------------------------------------------
# _format_table
# ---------------------------------------------------------------------------


class TestFormatTable:
    """Tests for _format_table."""

    def test_contains_file_path_fragment(self, minimal_result):
        """Output should include at least part of the file path."""
        output = _format_table(minimal_result)
        assert "test.txt" in output

    def test_contains_section_titles(self, result_with_sections):
        """Output should include each section title."""
        output = _format_table(result_with_sections)
        assert "Intro" in output

    def test_has_plus_borders(self, minimal_result):
        """ASCII table borders use '+'; at least one should be present."""
        output = _format_table(minimal_result)
        assert "+" in output

    def test_has_pipe_borders(self, minimal_result):
        """ASCII table column separators use '|'; at least one should be present."""
        output = _format_table(minimal_result)
        assert "|" in output

    def test_returns_string(self, minimal_result):
        """Return type should be str."""
        assert isinstance(_format_table(minimal_result), str)

    def test_no_sections_omits_section_table(self, minimal_result):
        """When there are no sections the sections table should not appear."""
        output = _format_table(minimal_result)
        assert "Content (preview)" not in output

    def test_sections_table_present_when_sections_exist(self, result_with_sections):
        """When sections exist the sections preview table should appear."""
        output = _format_table(result_with_sections)
        assert "Content (preview)" in output


# ---------------------------------------------------------------------------
# format_result dispatcher
# ---------------------------------------------------------------------------


class TestFormatResult:
    """Tests for the format_result dispatcher."""

    def test_plain_format_returns_string(self, minimal_result):
        """'plain' format should return a non-empty string."""
        output = format_result(minimal_result, "plain")
        assert isinstance(output, str)
        assert output

    def test_plain_format_contains_type(self, minimal_result):
        """'plain' output should contain the document type."""
        output = format_result(minimal_result, "plain")
        assert "plain" in output

    def test_json_format_is_valid_json(self, minimal_result):
        """'json' format should produce valid JSON."""
        output = format_result(minimal_result, "json")
        parsed = json.loads(output)
        assert "metadata" in parsed

    def test_table_format_has_borders(self, minimal_result):
        """'table' format should produce ASCII table borders."""
        output = format_result(minimal_result, "table")
        assert "+" in output

    def test_unknown_format_raises_formatter_error(self, minimal_result):
        """An unsupported format string should raise DocEngineFormatterError."""
        with pytest.raises(DocEngineFormatterError):
            format_result(minimal_result, "xml")

    def test_unknown_format_error_message_contains_format(self, minimal_result):
        """The error message should name the unsupported format."""
        with pytest.raises(DocEngineFormatterError, match="xml"):
            format_result(minimal_result, "xml")

    def test_unknown_format_yaml_raises(self, minimal_result):
        """'yaml' is not a supported format and should raise."""
        with pytest.raises(DocEngineFormatterError):
            format_result(minimal_result, "yaml")
