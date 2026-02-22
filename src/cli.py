"""Command-line interface for DocEngine.

Provides ``main()`` as the entry point, two subcommands (``process`` and
``inspect``), and helper functions for argument parsing, validation, and
command dispatch.  This is the only module that writes to stdout/stderr or
calls ``sys.exit``.
"""

import json
import sys
from argparse import ArgumentParser, Namespace

from src import __version__
from src.exceptions import DocEngineConfigError, DocEngineError
from src.formatter import format_result
from src.models import ParseOptions, ProcessingResult
from src.parser import parse_document
from src.utils import read_file_bytes


def build_arg_parser() -> ArgumentParser:
    """Build and return the argument parser for the DocEngine CLI.

    Defines two subcommands (``process`` and ``inspect``) that share a common
    set of options: ``--format``, ``--verbose``, and ``--encoding``.  A
    top-level ``--version`` flag is also registered.

    Returns:
        A configured :class:`~argparse.ArgumentParser` instance ready to
        call :meth:`~argparse.ArgumentParser.parse_args` on.
    """
    parser = ArgumentParser(
        prog="docengine",
        description="Parse and process document files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"docengine {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # Shared parent parser for common file/output options.
    parent = ArgumentParser(add_help=False)
    parent.add_argument("file", help="Path to the document file")
    parent.add_argument(
        "--format",
        choices=["plain", "json", "table"],
        default="plain",
        help="Output format (default: plain)",
    )
    parent.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parent.add_argument(
        "--encoding",
        default="",
        help="Override encoding detection (e.g. utf-8)",
    )

    subparsers.add_parser(
        "process",
        parents=[parent],
        help="Parse and output document content",
    )
    subparsers.add_parser(
        "inspect",
        parents=[parent],
        help="Output document metadata only",
    )

    return parser


def validate_cli_args(args: Namespace) -> None:
    """Validate parsed CLI arguments and raise on invalid input.

    Currently checks that a subcommand has been provided.  Future validation
    (e.g. mutually exclusive flags) should be added here.

    Args:
        args: The :class:`~argparse.Namespace` returned by
            :meth:`~argparse.ArgumentParser.parse_args`.

    Raises:
        DocEngineConfigError: If no subcommand is provided or if arguments
            are otherwise invalid.
    """
    if not args.command:
        raise DocEngineConfigError(
            "No command specified. Use 'process' or 'inspect'."
        )


def run_process_command(opts: ParseOptions) -> int:
    """Execute the ``process`` subcommand: read, parse, format, and print.

    The formatted output is written to stdout via :func:`print`.  This is
    the **only** function besides :func:`main` permitted to produce output.

    Args:
        opts: :class:`~src.models.ParseOptions` describing the target file,
            encoding hint, and desired output format.

    Returns:
        ``0`` on success.

    Raises:
        DocEngineFileError: If the file cannot be read.
        DocEngineParseError: If the document cannot be parsed.
        DocEngineFormatterError: If the output format is unknown.
    """
    content = read_file_bytes(opts.file_path)
    document = parse_document(content, opts)
    result = ProcessingResult(document=document, success=True)
    output = format_result(result, opts.format)
    print(output)
    return 0


def run_inspect_command(opts: ParseOptions) -> int:
    """Execute the ``inspect`` subcommand: read, parse, and print metadata only.

    Produces a condensed metadata view rather than full section content.
    JSON output uses a flat metadata object; plain/table output uses a
    labelled key-value layout.

    Args:
        opts: :class:`~src.models.ParseOptions` describing the target file,
            encoding hint, and desired output format.

    Returns:
        ``0`` on success.

    Raises:
        DocEngineFileError: If the file cannot be read.
        DocEngineParseError: If the document cannot be parsed.
    """
    content = read_file_bytes(opts.file_path)
    document = parse_document(content, opts)
    result = ProcessingResult(document=document, success=True)
    meta = document.metadata

    if opts.format == "json":
        output = json.dumps(
            {
                "file_path": meta.file_path,
                "document_type": meta.document_type,
                "encoding": meta.encoding,
                "file_size": meta.file_size,
                "word_count": meta.word_count,
                "line_count": meta.line_count,
            },
            indent=2,
        )
    else:
        lines = [
            f"File:     {meta.file_path}",
            f"Type:     {meta.document_type}",
            f"Encoding: {meta.encoding}",
            f"Size:     {meta.file_size} bytes",
            f"Words:    {meta.word_count}",
            f"Lines:    {meta.line_count}",
        ]
        if opts.verbose and result.warnings:
            lines.append("\nWarnings:")
            lines.extend(f"  - {w}" for w in result.warnings)
        output = "\n".join(lines)

    print(output)
    return 0


def main() -> None:
    """Entry point for the DocEngine CLI.

    Parses command-line arguments, validates them, constructs a
    :class:`~src.models.ParseOptions` instance, and dispatches to
    :func:`run_process_command` or :func:`run_inspect_command`.

    Any :class:`~src.exceptions.DocEngineError` that propagates to this level
    is printed to stderr and causes ``sys.exit(1)``.  Successful execution
    calls ``sys.exit(0)``.
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        validate_cli_args(args)

        opts = ParseOptions(
            file_path=args.file,
            encoding=getattr(args, "encoding", ""),
            format=getattr(args, "format", "plain"),
            verbose=getattr(args, "verbose", False),
        )

        if args.command == "process":
            exit_code = run_process_command(opts)
        elif args.command == "inspect":
            exit_code = run_inspect_command(opts)
        else:
            raise DocEngineConfigError(f"Unknown command: '{args.command}'")

        sys.exit(exit_code)

    except DocEngineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(getattr(exc, "exit_code", 1))
