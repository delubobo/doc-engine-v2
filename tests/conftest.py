"""Shared pytest fixtures for DocEngine tests.

All fixtures in this module are available to every test module without
explicit import.
"""

import pytest

from src.models import (
    DocumentMetadata,
    DocumentSection,
    ParsedDocument,
    ParseOptions,
    ProcessingResult,
)


@pytest.fixture
def sample_plain_bytes() -> bytes:
    """Return raw bytes for a simple plain-text document."""
    return b"Hello world\n\nThis is a test document.\nWith multiple lines."


@pytest.fixture
def sample_csv_bytes() -> bytes:
    """Return raw bytes for a simple CSV document."""
    return b"name,age,city\nAlice,30,New York\nBob,25,Los Angeles"


@pytest.fixture
def sample_json_bytes() -> bytes:
    """Return raw bytes for a simple JSON object document."""
    return b'{"title": "Test", "value": 42}'


@pytest.fixture
def sample_json_list_bytes() -> bytes:
    """Return raw bytes for a JSON document whose top-level value is a list."""
    return b'[{"id": 1}, {"id": 2}]'


@pytest.fixture
def default_parse_options(tmp_path) -> ParseOptions:
    """Return a ParseOptions instance pointing at a real temporary file.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        A :class:`~src.models.ParseOptions` with default settings.
    """
    f = tmp_path / "test.txt"
    f.write_text("hello")
    return ParseOptions(file_path=str(f))


@pytest.fixture
def sample_metadata() -> DocumentMetadata:
    """Return a DocumentMetadata instance with realistic field values."""
    return DocumentMetadata(
        file_path="/tmp/test.txt",
        file_size=100,
        encoding="utf-8",
        document_type="plain",
        word_count=10,
        line_count=3,
    )


@pytest.fixture
def sample_section() -> DocumentSection:
    """Return a simple DocumentSection for use in document fixtures."""
    return DocumentSection(title="Section 1", content="Hello world", index=0)


@pytest.fixture
def sample_parsed_document(sample_metadata, sample_section) -> ParsedDocument:
    """Return a ParsedDocument containing one section."""
    return ParsedDocument(
        metadata=sample_metadata,
        sections=[sample_section],
        raw_text="Hello world",
    )


@pytest.fixture
def sample_processing_result(sample_parsed_document) -> ProcessingResult:
    """Return a successful ProcessingResult wrapping a sample document."""
    return ProcessingResult(document=sample_parsed_document, success=True)
