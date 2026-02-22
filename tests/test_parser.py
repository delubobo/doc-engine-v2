"""Tests for document parsing logic in src/parser.py."""

import pytest

from src.exceptions import DocEngineEncodingError, DocEngineFormatError
from src.models import DocumentMetadata, ParseOptions
from src.parser import (
    _parse_csv_document,
    _parse_json_document,
    _parse_plain_text,
    detect_document_type,
    detect_encoding,
    parse_document,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def plain_metadata():
    """Return a DocumentMetadata instance pre-set for plain-text tests."""
    return DocumentMetadata(file_path="/tmp/test.txt", document_type="plain")


@pytest.fixture
def csv_metadata():
    """Return a DocumentMetadata instance pre-set for CSV tests."""
    return DocumentMetadata(file_path="/tmp/test.csv", document_type="csv")


@pytest.fixture
def json_metadata():
    """Return a DocumentMetadata instance pre-set for JSON tests."""
    return DocumentMetadata(file_path="/tmp/test.json", document_type="json")


# ---------------------------------------------------------------------------
# detect_encoding
# ---------------------------------------------------------------------------


class TestDetectEncoding:
    """Tests for detect_encoding."""

    def test_utf8_bom_detected(self):
        """A UTF-8 BOM prefix should be identified as 'utf-8-sig'."""
        content = b"\xef\xbb\xbfHello"
        assert detect_encoding(content) == "utf-8-sig"

    def test_plain_ascii_detected_as_utf8(self):
        """Pure ASCII bytes are valid UTF-8 and should be identified as such."""
        content = b"Hello world"
        assert detect_encoding(content) == "utf-8"

    def test_utf8_multibyte_detected(self):
        """Multi-byte UTF-8 sequences should be detected as 'utf-8'."""
        content = "Hello café".encode("utf-8")
        assert detect_encoding(content) == "utf-8"

    def test_pure_latin1_bytes_fall_back(self):
        """Bytes invalid in UTF-8 should produce 'latin-1' as fallback."""
        content = bytes([0x80, 0x90, 0xA0])
        assert detect_encoding(content) == "latin-1"

    def test_high_byte_without_bom_falls_back(self):
        """A high-byte sequence that is not valid UTF-8 should give 'latin-1'."""
        content = bytes([0xFF, 0xFE, 0x20, 0x00])
        encoding = detect_encoding(content)
        assert encoding in {"latin-1", "utf-8-sig"}


# ---------------------------------------------------------------------------
# detect_document_type
# ---------------------------------------------------------------------------


class TestDetectDocumentType:
    """Tests for detect_document_type."""

    def test_json_object_detected(self):
        """A text starting with '{' should be classified as JSON."""
        opts = ParseOptions(file_path="test.txt")
        assert detect_document_type('{"key": "value"}', opts) == "json"

    def test_json_array_detected(self):
        """A text starting with '[' should be classified as JSON."""
        opts = ParseOptions(file_path="test.txt")
        assert detect_document_type("[1, 2, 3]", opts) == "json"

    def test_json_with_leading_whitespace(self):
        """Leading whitespace before '{' should still be classified as JSON."""
        opts = ParseOptions(file_path="test.txt")
        assert detect_document_type('  \n{"k": 1}', opts) == "json"

    def test_csv_by_file_extension(self):
        """A .csv extension should be classified as CSV regardless of content."""
        opts = ParseOptions(file_path="data.csv")
        assert detect_document_type("name,age\nAlice,30", opts) == "csv"

    def test_csv_by_content_heuristic(self):
        """First non-empty line containing a comma should be classified as CSV."""
        opts = ParseOptions(file_path="data.txt")
        assert detect_document_type("name,age\nAlice,30", opts) == "csv"

    def test_plain_text_detected(self):
        """Text with no commas and no JSON syntax should be 'plain'."""
        opts = ParseOptions(file_path="notes.txt")
        assert detect_document_type("Just some text\nno commas here", opts) == "plain"

    def test_empty_string_detected_as_plain(self):
        """An empty document should default to 'plain'."""
        opts = ParseOptions(file_path="empty.txt")
        assert detect_document_type("", opts) == "plain"


# ---------------------------------------------------------------------------
# _parse_plain_text
# ---------------------------------------------------------------------------


class TestParsePlainText:
    """Tests for _parse_plain_text."""

    def test_single_contiguous_block(self, plain_metadata):
        """A text with no blank lines should produce one section."""
        text = "Hello world\nThis is a test."
        doc = _parse_plain_text(text, plain_metadata)
        assert len(doc.sections) == 1
        assert "Hello world" in doc.sections[0].content

    def test_multiple_blocks_separated_by_blank_lines(self, plain_metadata):
        """Blank-line-separated blocks should each become a section."""
        text = "Block one\n\nBlock two"
        doc = _parse_plain_text(text, plain_metadata)
        assert len(doc.sections) == 2

    def test_three_blocks(self, plain_metadata):
        """Three blank-line-separated blocks should produce three sections."""
        text = "A\n\nB\n\nC"
        doc = _parse_plain_text(text, plain_metadata)
        assert len(doc.sections) == 3

    def test_raw_text_preserved(self, plain_metadata):
        """raw_text on the returned document should equal the input text."""
        text = "Hello\n\nWorld"
        doc = _parse_plain_text(text, plain_metadata)
        assert doc.raw_text == text

    def test_empty_text_yields_no_sections(self, plain_metadata):
        """An empty input should produce an empty sections list."""
        doc = _parse_plain_text("", plain_metadata)
        assert doc.sections == []

    def test_section_titles_are_sequential(self, plain_metadata):
        """Section titles should be 'Section 1', 'Section 2', etc."""
        text = "A\n\nB\n\nC"
        doc = _parse_plain_text(text, plain_metadata)
        assert doc.sections[0].title == "Section 1"
        assert doc.sections[1].title == "Section 2"
        assert doc.sections[2].title == "Section 3"

    def test_section_indices_are_zero_based(self, plain_metadata):
        """Section index values should be 0, 1, 2, …"""
        text = "A\n\nB"
        doc = _parse_plain_text(text, plain_metadata)
        assert doc.sections[0].index == 0
        assert doc.sections[1].index == 1


# ---------------------------------------------------------------------------
# _parse_csv_document
# ---------------------------------------------------------------------------


class TestParseCsvDocument:
    """Tests for _parse_csv_document."""

    def test_parses_header_and_data_rows(self, csv_metadata):
        """Header + two data rows should yield three sections."""
        text = "name,age\nAlice,30\nBob,25"
        doc = _parse_csv_document(text, csv_metadata)
        assert len(doc.sections) == 3

    def test_row_titles_are_sequential(self, csv_metadata):
        """Section titles should be 'Row 1', 'Row 2', etc."""
        text = "col1,col2"
        doc = _parse_csv_document(text, csv_metadata)
        assert doc.sections[0].title == "Row 1"

    def test_row_content_is_joined(self, csv_metadata):
        """Section content should be the CSV values joined with ', '."""
        text = "a,b,c"
        doc = _parse_csv_document(text, csv_metadata)
        assert doc.sections[0].content == "a, b, c"

    def test_raw_text_preserved(self, csv_metadata):
        """raw_text on the returned document should equal the input text."""
        text = "a,b\n1,2"
        doc = _parse_csv_document(text, csv_metadata)
        assert doc.raw_text == text

    def test_empty_csv_yields_no_sections(self, csv_metadata):
        """An empty input should produce an empty sections list."""
        doc = _parse_csv_document("", csv_metadata)
        assert doc.sections == []


# ---------------------------------------------------------------------------
# _parse_json_document
# ---------------------------------------------------------------------------


class TestParseJsonDocument:
    """Tests for _parse_json_document."""

    def test_dict_creates_one_section_per_key(self, json_metadata):
        """Each key in a top-level dict should become one section."""
        text = '{"name": "Alice", "age": 30}'
        doc = _parse_json_document(text, json_metadata)
        titles = [s.title for s in doc.sections]
        assert "name" in titles
        assert "age" in titles

    def test_list_creates_one_section_per_item(self, json_metadata):
        """Each element of a top-level list should become one section."""
        text = "[1, 2, 3]"
        doc = _parse_json_document(text, json_metadata)
        assert len(doc.sections) == 3

    def test_list_section_titles(self, json_metadata):
        """List-element sections should be titled 'Item 1', 'Item 2', etc."""
        text = "[1, 2]"
        doc = _parse_json_document(text, json_metadata)
        assert doc.sections[0].title == "Item 1"
        assert doc.sections[1].title == "Item 2"

    def test_invalid_json_raises_format_error(self, json_metadata):
        """Malformed JSON should raise DocEngineFormatError."""
        with pytest.raises(DocEngineFormatError):
            _parse_json_document("{invalid json}", json_metadata)

    def test_raw_text_preserved(self, json_metadata):
        """raw_text on the returned document should equal the input text."""
        text = '{"key": "value"}'
        doc = _parse_json_document(text, json_metadata)
        assert doc.raw_text == text

    def test_scalar_json_creates_single_section(self, json_metadata):
        """A top-level scalar (string, number, etc.) should produce one section."""
        text = '"just a string"'
        doc = _parse_json_document(text, json_metadata)
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Value"


# ---------------------------------------------------------------------------
# parse_document (integration)
# ---------------------------------------------------------------------------


class TestParseDocument:
    """Integration tests for parse_document."""

    def test_plain_text_document(self, tmp_path):
        """Plain text bytes should produce a document typed 'plain'."""
        opts = ParseOptions(file_path=str(tmp_path / "test.txt"))
        doc = parse_document(b"Hello world", opts)
        assert doc.metadata.document_type == "plain"

    def test_json_document(self, tmp_path):
        """JSON bytes should produce a document typed 'json'."""
        opts = ParseOptions(file_path=str(tmp_path / "test.json"))
        doc = parse_document(b'{"key": "value"}', opts)
        assert doc.metadata.document_type == "json"

    def test_csv_document(self, tmp_path):
        """CSV bytes should produce a document typed 'csv'."""
        opts = ParseOptions(file_path=str(tmp_path / "test.csv"))
        doc = parse_document(b"name,age\nAlice,30", opts)
        assert doc.metadata.document_type == "csv"

    def test_encoding_error_raised_for_bad_encoding(self, tmp_path):
        """Specifying 'ascii' for bytes containing non-ASCII should raise."""
        opts = ParseOptions(file_path=str(tmp_path / "test.txt"), encoding="ascii")
        with pytest.raises(DocEngineEncodingError):
            parse_document(b"\xff\xfe invalid", opts)

    def test_metadata_file_size_populated(self, tmp_path):
        """metadata.file_size should equal len(content)."""
        opts = ParseOptions(file_path=str(tmp_path / "test.txt"))
        content = b"Hello world\nLine two"
        doc = parse_document(content, opts)
        assert doc.metadata.file_size == len(content)

    def test_metadata_word_count_populated(self, tmp_path):
        """metadata.word_count should reflect actual word count."""
        opts = ParseOptions(file_path=str(tmp_path / "test.txt"))
        content = b"Hello world\nLine two"
        doc = parse_document(content, opts)
        assert doc.metadata.word_count == 4

    def test_metadata_line_count_populated(self, tmp_path):
        """metadata.line_count should reflect actual line count."""
        opts = ParseOptions(file_path=str(tmp_path / "test.txt"))
        content = b"Hello world\nLine two"
        doc = parse_document(content, opts)
        assert doc.metadata.line_count == 2

    def test_utf8_bom_file_encoding_detected(self, tmp_path):
        """A file with a UTF-8 BOM should report encoding as 'utf-8-sig'."""
        opts = ParseOptions(file_path=str(tmp_path / "bom.txt"), encoding="")
        content = b"\xef\xbb\xbfHello BOM world"
        doc = parse_document(content, opts)
        assert doc.metadata.encoding == "utf-8-sig"

    def test_encoding_hint_used_when_provided(self, tmp_path):
        """opts.encoding should override auto-detection when non-empty."""
        opts = ParseOptions(
            file_path=str(tmp_path / "latin.txt"), encoding="latin-1"
        )
        content = "Héllo".encode("latin-1")
        doc = parse_document(content, opts)
        assert doc.metadata.encoding == "latin-1"
