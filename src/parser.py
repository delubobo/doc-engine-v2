"""Document parsing logic for DocEngine.

Responsible for encoding detection, document-type detection, and dispatching
to the appropriate format-specific parser.  All functions are stateless.
"""

import csv
import io
import json

from src.exceptions import (
    DocEngineEncodingError,
    DocEngineFormatError,
)
from src.models import DocumentMetadata, DocumentSection, ParsedDocument, ParseOptions
from src.utils import count_lines, count_words, normalize_path


def detect_encoding(content: bytes) -> str:
    """Detect the character encoding of a raw byte string.

    Checks for a UTF-8 BOM first, then attempts to decode as UTF-8.
    Falls back to ``"latin-1"`` if UTF-8 decoding fails (latin-1 can decode
    any single-byte sequence without error).

    Args:
        content: The raw bytes to inspect.

    Returns:
        A string naming the detected encoding, e.g. ``"utf-8"``,
        ``"utf-8-sig"``, or ``"latin-1"``.
    """
    if content.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        content.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def detect_document_type(text: str, opts: ParseOptions) -> str:
    """Detect the logical document type from decoded text and parse options.

    Detection priority:

    1. If the stripped text starts with ``{`` or ``[``, return ``"json"``.
    2. If *opts.file_path* ends with ``.csv``, return ``"csv"``.
    3. If the first non-empty line contains a comma, return ``"csv"``.
    4. Otherwise return ``"plain"``.

    Args:
        text: The decoded text content of the document.
        opts: :class:`~src.models.ParseOptions` carrying a ``file_path`` hint.

    Returns:
        One of ``"json"``, ``"csv"``, or ``"plain"``.
    """
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"

    if opts.file_path.lower().endswith(".csv"):
        return "csv"

    for line in text.splitlines():
        if line.strip():
            if "," in line:
                return "csv"
            break

    return "plain"


def _parse_plain_text(text: str, metadata: DocumentMetadata) -> ParsedDocument:
    """Parse plain-text content into a :class:`~src.models.ParsedDocument`.

    Splits the text on blank lines; each contiguous block of non-blank lines
    becomes one :class:`~src.models.DocumentSection`.

    Args:
        text: The decoded plain-text content.
        metadata: Pre-built :class:`~src.models.DocumentMetadata` for this
            document.

    Returns:
        A :class:`~src.models.ParsedDocument` with sections derived from
        blank-line splitting.
    """
    sections: list[DocumentSection] = []
    current_lines: list[str] = []
    index = 0

    for line in text.splitlines():
        if line.strip():
            current_lines.append(line)
        else:
            if current_lines:
                content = "\n".join(current_lines)
                sections.append(
                    DocumentSection(
                        title=f"Section {index + 1}",
                        content=content,
                        index=index,
                    )
                )
                index += 1
                current_lines = []

    if current_lines:
        content = "\n".join(current_lines)
        sections.append(
            DocumentSection(
                title=f"Section {index + 1}",
                content=content,
                index=index,
            )
        )

    return ParsedDocument(metadata=metadata, sections=sections, raw_text=text)


def _parse_csv_document(text: str, metadata: DocumentMetadata) -> ParsedDocument:
    """Parse CSV content into a :class:`~src.models.ParsedDocument`.

    Uses :mod:`csv`.reader to parse *text*.  Each row becomes a
    :class:`~src.models.DocumentSection` whose content is the row values
    joined with ``", "``.

    Args:
        text: The decoded CSV text content.
        metadata: Pre-built :class:`~src.models.DocumentMetadata` for this
            document.

    Returns:
        A :class:`~src.models.ParsedDocument` whose sections correspond to
        CSV rows.

    Raises:
        DocEngineFormatError: If :mod:`csv`.reader raises a parse error.
    """
    sections: list[DocumentSection] = []
    try:
        reader = csv.reader(io.StringIO(text))
        for index, row in enumerate(reader):
            content = ", ".join(row)
            sections.append(
                DocumentSection(
                    title=f"Row {index + 1}",
                    content=content,
                    index=index,
                )
            )
    except csv.Error as exc:
        raise DocEngineFormatError(
            f"CSV parsing error: {exc}",
            file_path=metadata.file_path,
        )
    return ParsedDocument(metadata=metadata, sections=sections, raw_text=text)


def _parse_json_document(text: str, metadata: DocumentMetadata) -> ParsedDocument:
    """Parse JSON content into a :class:`~src.models.ParsedDocument`.

    Decodes the JSON value.  The top-level structure determines section
    layout:

    * **list** — each element becomes one section.
    * **dict** — each key-value pair becomes one section.
    * **other** — a single section containing ``repr(value)`` is created.

    Args:
        text: The decoded JSON text content.
        metadata: Pre-built :class:`~src.models.DocumentMetadata` for this
            document.

    Returns:
        A :class:`~src.models.ParsedDocument` whose sections correspond to
        JSON elements.

    Raises:
        DocEngineFormatError: If *text* is not valid JSON.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DocEngineFormatError(
            f"JSON parsing error: {exc}",
            file_path=metadata.file_path,
            line_number=exc.lineno,
            column=exc.colno,
        )

    sections: list[DocumentSection] = []
    if isinstance(data, list):
        for index, item in enumerate(data):
            sections.append(
                DocumentSection(
                    title=f"Item {index + 1}",
                    content=json.dumps(item, indent=2),
                    index=index,
                )
            )
    elif isinstance(data, dict):
        for index, (key, value) in enumerate(data.items()):
            sections.append(
                DocumentSection(
                    title=str(key),
                    content=json.dumps(value, indent=2),
                    index=index,
                )
            )
    else:
        sections.append(
            DocumentSection(title="Value", content=repr(data), index=0)
        )

    return ParsedDocument(metadata=metadata, sections=sections, raw_text=text)


def parse_document(content: bytes, opts: ParseOptions) -> ParsedDocument:
    """Parse raw document bytes into a fully structured :class:`~src.models.ParsedDocument`.

    Steps:

    1. Determine encoding (honouring ``opts.encoding`` if provided).
    2. Decode *content* to text.
    3. Detect the document type.
    4. Build :class:`~src.models.DocumentMetadata`.
    5. Dispatch to the appropriate format-specific parser.

    Args:
        content: The raw bytes of the document file.
        opts: :class:`~src.models.ParseOptions` controlling encoding hints
            and carrying the file path.

    Returns:
        A fully populated :class:`~src.models.ParsedDocument`.

    Raises:
        DocEngineEncodingError: If the content cannot be decoded with the
            chosen encoding.
        DocEngineFormatError: If the document's format is structurally invalid.
    """
    encoding = opts.encoding if opts.encoding else detect_encoding(content)

    try:
        text = content.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise DocEngineEncodingError(
            f"Cannot decode file with encoding '{encoding}': {exc}",
            file_path=opts.file_path,
        )

    doc_type = detect_document_type(text, opts)

    metadata = DocumentMetadata(
        file_path=normalize_path(opts.file_path),
        file_size=len(content),
        encoding=encoding,
        document_type=doc_type,
        word_count=count_words(text),
        line_count=count_lines(text),
    )

    if doc_type == "plain":
        return _parse_plain_text(text, metadata)
    if doc_type == "csv":
        return _parse_csv_document(text, metadata)
    if doc_type == "json":
        return _parse_json_document(text, metadata)

    raise DocEngineFormatError(
        f"Unsupported document type: '{doc_type}'",
        file_path=opts.file_path,
    )
