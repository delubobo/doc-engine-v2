"""Stateless helper utilities for DocEngine.

All functions in this module are pure or side-effect-free with respect to
application state.  The only side effects permitted are filesystem reads.
"""

import os

from src.exceptions import (
    DocEngineFileError,
    DocEngineFileNotFoundError,
    DocEnginePermissionError,
)


def read_file_bytes(file_path: str) -> bytes:
    """Read the raw bytes of a file from disk.

    Args:
        file_path: Path to the file to read.  May be relative or absolute.

    Returns:
        The complete contents of the file as a :class:`bytes` object.

    Raises:
        DocEngineFileNotFoundError: If no file exists at *file_path*.
        DocEnginePermissionError: If the process lacks read permission.
        DocEngineFileError: For any other OS-level I/O error.
    """
    normalized = normalize_path(file_path)
    try:
        with open(normalized, "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        raise DocEngineFileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise DocEnginePermissionError(f"Permission denied: {file_path}")
    except OSError as exc:
        raise DocEngineFileError(f"Error reading file '{file_path}': {exc}")


def normalize_path(file_path: str) -> str:
    """Return an absolute, normalised version of *file_path*.

    Resolves ``..`` components and converts relative paths to absolute using
    the current working directory.

    Args:
        file_path: The path to normalise.

    Returns:
        A :class:`str` containing the normalised absolute path.
    """
    return os.path.normpath(os.path.abspath(file_path))


def is_readable_file(file_path: str) -> bool:
    """Return *True* if *file_path* points to an existing, readable file.

    Directories and missing paths both return *False*.

    Args:
        file_path: Path to check.

    Returns:
        *True* when the path is a regular file that the current process can
        read; *False* otherwise.
    """
    normalized = normalize_path(file_path)
    return os.path.isfile(normalized) and os.access(normalized, os.R_OK)


def count_words(text: str) -> int:
    """Count the number of whitespace-delimited words in *text*.

    An empty string or a string containing only whitespace returns 0.

    Args:
        text: The text to analyse.

    Returns:
        The number of words found.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Count the number of lines in *text*.

    Uses :meth:`str.splitlines` so that a trailing newline does *not* add an
    extra empty line.  An empty string returns 0.

    Args:
        text: The text to analyse.

    Returns:
        The number of lines.  Returns 0 for an empty string.
    """
    if not text:
        return 0
    return len(text.splitlines())
