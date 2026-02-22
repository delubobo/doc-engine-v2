# DocEngine v2

> A deterministic, zero-dependency CLI tool for parsing and inspecting structured documents.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Version](https://img.shields.io/badge/version-0.1.0-informational)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![PEP8](https://img.shields.io/badge/style-PEP%208-orange)

---

## Overview

DocEngine v2 reads a document file, auto-detects its format and encoding, parses it into a structured in-memory representation, and renders the result to stdout in your choice of output format. Every stage of the pipeline is stateless and deterministic: given the same input bytes, the output is always identical.

**Supported document types:** plain text, CSV, JSON

**Supported output formats:** `plain`, `json`, `table`

---

## Features

- **Automatic format detection** — identifies plain text, CSV, and JSON from content heuristics and file extension, with no user configuration required.
- **Automatic encoding detection** — detects UTF-8 BOM, UTF-8, and Latin-1; accepts an optional `--encoding` override.
- **Three output renderers** — human-readable plain text, machine-readable JSON, and a dynamic-width ASCII table.
- **Two subcommands** — `process` emits full document content; `inspect` emits metadata only (file size, word count, line count, encoding, type).
- **Typed exception hierarchy** — every error condition maps to a specific exception subclass, each carrying its own CLI exit code.
- **Zero runtime dependencies** — the standard library is sufficient; `pytest` and `pytest-cov` are the only development dependencies.

---

## Architecture

DocEngine v2 follows a strict layered architecture. Data flows in one direction — from the CLI inward through parsing, then outward through formatting — with no circular imports.

```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│  cli.py  ·  Argument parsing, validation, dispatch,     │
│             sys.exit — the only I/O boundary            │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │    Parser Layer      │
          │  parser.py           │
          │  · Encoding detect   │
          │  · Format detect     │
          │  · Plain / CSV / JSON│
          │    sub-parsers       │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Formatter Layer     │
          │  formatter.py        │
          │  · plain renderer    │
          │  · json renderer     │
          │  · table renderer    │
          └─────────────────────┘

  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

  Support modules (imported by any layer above):

  models.py     Pure dataclasses — ParseOptions,
                DocumentMetadata, DocumentSection,
                ParsedDocument, ProcessingResult

  utils.py      Pure helpers — read_file_bytes,
                normalize_path, count_words, count_lines

  exceptions.py Typed exception hierarchy rooted at
                DocEngineError
```

### Module summary

| Module | Responsibility |
|---|---|
| `cli.py` | Entry point, argument parsing, subcommand dispatch |
| `parser.py` | Encoding detection, type detection, format-specific parsers |
| `formatter.py` | Stateless output renderers (`plain`, `json`, `table`) |
| `models.py` | Pure data containers (no I/O, no logic) |
| `utils.py` | Filesystem helpers and text statistics |
| `exceptions.py` | Typed exception hierarchy with exit-code metadata |

### Exception hierarchy

```
DocEngineError
├── DocEngineConfigError        # Invalid CLI arguments
├── DocEngineFileError          # Filesystem problems
│   ├── DocEngineFileNotFoundError
│   └── DocEnginePermissionError
├── DocEngineParseError         # Document-level parse failures
│   ├── DocEngineEncodingError  # Cannot decode bytes
│   └── DocEngineFormatError    # Structurally invalid content
└── DocEngineFormatterError     # Unknown output format requested
```

---

## Setup

### Prerequisites

- Python 3.9 or later
- `pip`

### Create and activate a virtual environment

```bash
# Create the virtual environment
python -m venv venv

# Activate — macOS / Linux
source venv/bin/activate

# Activate — Windows (PowerShell)
venv\Scripts\Activate.ps1

# Activate — Windows (Command Prompt)
venv\Scripts\activate.bat
```

### Install the package

Install DocEngine in editable mode along with its development dependencies:

```bash
pip install -e ".[dev]"
```

This registers the `docengine` command on your `PATH` for the duration of your virtual-environment session.

---

## Usage

### `process` — parse and render a document

```bash
# Plain-text output (default)
docengine process data/sample.txt

# JSON output
docengine process data/sample.txt --format json

# ASCII table output
docengine process data/sample.txt --format table

# Override encoding
docengine process legacy.txt --encoding latin-1

# Verbose mode (includes warnings in output)
docengine process data/sample.txt --verbose
```

### `inspect` — display metadata only

```bash
# Plain metadata summary
docengine inspect data/sample.txt

# Machine-readable metadata
docengine inspect data/sample.txt --format json
```

**Example `inspect` output (plain):**

```
File:     /path/to/data/sample.txt
Type:     plain
Encoding: utf-8
Size:     344 bytes
Words:    57
Lines:    13
```

**Example `process` output (JSON, truncated):**

```json
{
  "metadata": {
    "file_path": "/path/to/data/sample.txt",
    "document_type": "plain",
    "encoding": "utf-8",
    "file_size": 344,
    "word_count": 57,
    "line_count": 13
  },
  "sections": [
    {
      "title": "Section 1",
      "content": "DocEngine v2 Sample Document\n=============================",
      "index": 0
    }
  ],
  "success": true,
  "errors": [],
  "warnings": []
}
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Any `DocEngineError` (file not found, parse failure, bad arguments, etc.) |

---

## Running the Tests

### Full test suite

```bash
pytest
```

### With coverage report

```bash
pytest --cov=src --cov-report=term-missing
```

### Single test file

```bash
pytest tests/test_parser.py
```

### Single test by name

```bash
pytest tests/test_cli.py::TestMain::test_main_exits_0_on_success
```

### Smoke test against the bundled sample file

Run the `process` and `inspect` subcommands against the included `data/sample.txt` to confirm end-to-end functionality:

```bash
# Smoke test: process (plain)
docengine process data/sample.txt

# Smoke test: process (JSON)
docengine process data/sample.txt --format json

# Smoke test: process (table)
docengine process data/sample.txt --format table

# Smoke test: inspect (plain)
docengine inspect data/sample.txt

# Smoke test: inspect (JSON)
docengine inspect data/sample.txt --format json
```

All five commands should complete with exit code `0` and produce non-empty output.

---

## Project Structure

```
doc-engine-v2/
├── data/
│   └── sample.txt          # Bundled smoke-test document
├── src/
│   ├── __init__.py         # Package version (__version__ = "0.1.0")
│   ├── __main__.py         # python -m src entry point
│   ├── cli.py              # Argument parser, subcommand dispatch, entry point
│   ├── exceptions.py       # Typed exception hierarchy
│   ├── formatter.py        # Output renderers (plain / json / table)
│   ├── models.py           # Pure dataclasses
│   ├── parser.py           # Encoding detection, format detection, sub-parsers
│   └── utils.py            # Filesystem helpers and text statistics
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_exceptions.py
│   ├── test_formatter.py
│   ├── test_models.py
│   ├── test_parser.py
│   └── test_utils.py
├── pyproject.toml
├── pytest.ini
└── requirements.txt
```

---

## Development Notes

- All code conforms to **PEP 8**.
- Every public function and class carries a **docstring** describing purpose, arguments, return values, and raised exceptions.
- All tests use **pytest** exclusively.
- The formatter, parser, and utils layers perform **no I/O** — only `cli.py` and `utils.read_file_bytes` interact with the filesystem or stdout/stderr.
