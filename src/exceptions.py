"""Custom exception hierarchy for DocEngine.

All exceptions carry an exit_code attribute for use by the CLI entry point.
No I/O or application logic lives in this module.
"""


class DocEngineError(Exception):
    """Base exception for all DocEngine errors.

    Args:
        message: Human-readable description of the error.
        exit_code: Integer exit code the CLI should use when this error
            propagates to the top level. Defaults to 1.
    """

    def __init__(self, message: str, exit_code: int = 1) -> None:
        """Initialise the exception with a message and optional exit code."""
        super().__init__(message)
        self.exit_code = exit_code


class DocEngineConfigError(DocEngineError):
    """Raised for invalid CLI arguments or options before any I/O occurs.

    Args:
        message: Description of the configuration problem.
        exit_code: Exit code for the CLI. Defaults to 1.
    """


class DocEngineFileError(DocEngineError):
    """Raised for filesystem-level problems.

    Args:
        message: Description of the filesystem error.
        exit_code: Exit code for the CLI. Defaults to 1.
    """


class DocEngineFileNotFoundError(DocEngineFileError):
    """Raised when the specified file does not exist.

    Args:
        message: Description including the missing path.
        exit_code: Exit code for the CLI. Defaults to 1.
    """


class DocEnginePermissionError(DocEngineFileError):
    """Raised when the process lacks permission to read the file.

    Args:
        message: Description of the permission problem.
        exit_code: Exit code for the CLI. Defaults to 1.
    """


class DocEngineParseError(DocEngineError):
    """Raised for errors encountered while parsing a document.

    Args:
        message: Description of the parse error.
        file_path: Path to the file being parsed. Defaults to "".
        line_number: Line number where the error occurred. Defaults to 0.
        column: Column number where the error occurred. Defaults to 0.
        exit_code: Exit code for the CLI. Defaults to 1.
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        line_number: int = 0,
        column: int = 0,
        exit_code: int = 1,
    ) -> None:
        """Initialise with location metadata in addition to message."""
        super().__init__(message, exit_code)
        self.file_path = file_path
        self.line_number = line_number
        self.column = column


class DocEngineEncodingError(DocEngineParseError):
    """Raised when a document cannot be decoded with the detected encoding.

    Args:
        message: Description of the encoding failure.
        file_path: Path to the file that could not be decoded.
        line_number: Line number where the error occurred. Defaults to 0.
        column: Column number where the error occurred. Defaults to 0.
        exit_code: Exit code for the CLI. Defaults to 1.
    """


class DocEngineFormatError(DocEngineParseError):
    """Raised when a document's format is unrecognised or structurally invalid.

    Args:
        message: Description of the format problem.
        file_path: Path to the offending file.
        line_number: Line number where the error occurred. Defaults to 0.
        column: Column number where the error occurred. Defaults to 0.
        exit_code: Exit code for the CLI. Defaults to 1.
    """


class DocEngineFormatterError(DocEngineError):
    """Raised when an unknown output format is requested from the formatter.

    Args:
        message: Description including the unsupported format name.
        exit_code: Exit code for the CLI. Defaults to 1.
    """
