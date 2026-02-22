"""Cross-module dataclasses for DocEngine.

This module contains only pure data containers.  No I/O or business logic
belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParseOptions:
    """Options that control how a document is parsed and presented.

    Attributes:
        file_path: Absolute or relative path to the document file.
        encoding: Encoding hint for the file (e.g. ``"utf-8"``).  An empty
            string means *auto-detect*.
        format: Desired output format; one of ``"plain"``, ``"json"``, or
            ``"table"``.
        verbose: When *True*, include extra diagnostic information in output.
    """

    file_path: str
    encoding: str = "utf-8"
    format: str = "plain"
    verbose: bool = False


@dataclass
class DocumentMetadata:
    """Metadata that describes a parsed document file.

    Attributes:
        file_path: Absolute path to the source file.
        file_size: Size of the raw file in bytes.
        encoding: Character encoding used to decode the file.
        document_type: Detected logical type; one of ``"plain"``, ``"csv"``,
            or ``"json"``.
        word_count: Total number of whitespace-delimited words in the document.
        line_count: Total number of lines in the document.
    """

    file_path: str
    file_size: int = 0
    encoding: str = "utf-8"
    document_type: str = "plain"
    word_count: int = 0
    line_count: int = 0


@dataclass
class DocumentSection:
    """A logical section within a parsed document.

    Attributes:
        title: Human-readable label for the section (e.g. ``"Section 1"``).
        content: Full text content of the section.
        index: Zero-based position of the section within the document.
    """

    title: str = ""
    content: str = ""
    index: int = 0


@dataclass
class ParsedDocument:
    """The structured result of parsing a single document file.

    Attributes:
        metadata: Descriptive metadata about the document.
        sections: Ordered list of logical sections extracted from the document.
        raw_text: The full decoded text of the document, unmodified.
    """

    metadata: DocumentMetadata = field(
        default_factory=lambda: DocumentMetadata(file_path="")
    )
    sections: list[DocumentSection] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ProcessingResult:
    """The complete result of a document processing operation.

    Attributes:
        document: The parsed document produced by the parser.
        success: *True* if processing completed without errors.
        errors: List of error message strings accumulated during processing.
        warnings: List of warning message strings accumulated during processing.
    """

    document: ParsedDocument = field(default_factory=ParsedDocument)
    success: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
