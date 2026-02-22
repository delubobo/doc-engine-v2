"""Output formatting for DocEngine processing results.

All public functions accept a :class:`~src.models.ProcessingResult` and return
a plain :class:`str`.  No I/O is performed here.
"""

import json

from src.exceptions import DocEngineFormatterError
from src.models import ProcessingResult

_SUPPORTED_FORMATS = {"plain", "json", "table"}


def _format_plain(result: ProcessingResult) -> str:
    """Render *result* as a human-readable plain-text string.

    Outputs a metadata header block followed by each document section
    delimited by a title banner.

    Args:
        result: The :class:`~src.models.ProcessingResult` to render.

    Returns:
        A multi-line plain-text string.
    """
    doc = result.document
    meta = doc.metadata
    lines = [
        f"File:     {meta.file_path}",
        f"Type:     {meta.document_type}",
        f"Encoding: {meta.encoding}",
        f"Size:     {meta.file_size} bytes",
        f"Words:    {meta.word_count}",
        f"Lines:    {meta.line_count}",
        "",
    ]
    for section in doc.sections:
        lines.append(f"--- {section.title} ---")
        lines.append(section.content)
        lines.append("")
    return "\n".join(lines)


def _format_json(result: ProcessingResult) -> str:
    """Render *result* as an indented JSON string.

    Serialises document metadata and all sections into a top-level JSON
    object.  The output is guaranteed to be valid JSON.

    Args:
        result: The :class:`~src.models.ProcessingResult` to render.

    Returns:
        A valid, indented JSON string.
    """
    doc = result.document
    meta = doc.metadata
    data = {
        "metadata": {
            "file_path": meta.file_path,
            "document_type": meta.document_type,
            "encoding": meta.encoding,
            "file_size": meta.file_size,
            "word_count": meta.word_count,
            "line_count": meta.line_count,
        },
        "sections": [
            {"title": s.title, "content": s.content, "index": s.index}
            for s in doc.sections
        ],
        "success": result.success,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    return json.dumps(data, indent=2)


def _format_table(result: ProcessingResult) -> str:
    """Render *result* as an ASCII table.

    Produces a metadata table and, if sections are present, a sections
    preview table.  Column widths are computed dynamically from content.

    Args:
        result: The :class:`~src.models.ProcessingResult` to render.

    Returns:
        An ASCII-table string.
    """
    doc = result.document
    meta = doc.metadata

    def make_table(headers: list[str], rows: list[list[str]]) -> str:
        """Build a fixed-width ASCII table from *headers* and *rows*.

        Args:
            headers: Column header strings.
            rows: Each inner list is one data row; cells must match header
                count.

        Returns:
            A multi-line ASCII table string.
        """
        all_rows = [headers] + rows
        widths = [max(len(str(cell)) for cell in col) for col in zip(*all_rows)]
        sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"

        def fmt_row(cells: list[str]) -> str:
            """Format a single table row with padding."""
            return "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"

        lines = [sep, fmt_row(headers), sep]
        for row in rows:
            lines.append(fmt_row(row))
        lines.append(sep)
        return "\n".join(lines)

    meta_table = make_table(
        ["Property", "Value"],
        [
            ["File", meta.file_path],
            ["Type", meta.document_type],
            ["Encoding", meta.encoding],
            ["Size", f"{meta.file_size} bytes"],
            ["Words", str(meta.word_count)],
            ["Lines", str(meta.line_count)],
        ],
    )

    if doc.sections:
        section_rows = [
            [str(s.index), s.title, s.content[:60]] for s in doc.sections
        ]
        section_table = "\n\n" + make_table(
            ["#", "Title", "Content (preview)"], section_rows
        )
    else:
        section_table = ""

    return meta_table + section_table


def format_result(result: ProcessingResult, fmt: str) -> str:
    """Render *result* to a string in the requested output format.

    Args:
        result: The :class:`~src.models.ProcessingResult` to render.
        fmt: The desired output format.  Must be one of ``"plain"``,
            ``"json"``, or ``"table"``.

    Returns:
        A string representation of *result* in the requested format.

    Raises:
        DocEngineFormatterError: If *fmt* is not a supported format string.
    """
    if fmt not in _SUPPORTED_FORMATS:
        raise DocEngineFormatterError(
            f"Unknown output format: '{fmt}'. "
            f"Supported formats: {sorted(_SUPPORTED_FORMATS)}"
        )
    if fmt == "plain":
        return _format_plain(result)
    if fmt == "json":
        return _format_json(result)
    return _format_table(result)
