"""Tests for the CLI entry point and helpers in src/cli.py."""

import json
import sys
from argparse import ArgumentParser

import pytest

from src.cli import (
    build_arg_parser,
    main,
    run_inspect_command,
    run_process_command,
    validate_cli_args,
)
from src.exceptions import DocEngineConfigError, DocEngineFileNotFoundError
from src.models import ParseOptions


# ---------------------------------------------------------------------------
# build_arg_parser
# ---------------------------------------------------------------------------


class TestBuildArgParser:
    """Tests for build_arg_parser."""

    def test_returns_argument_parser(self):
        """build_arg_parser should return an ArgumentParser instance."""
        parser = build_arg_parser()
        assert isinstance(parser, ArgumentParser)

    def test_process_subcommand_parsed(self):
        """'process <file>' should set command='process' and file correctly."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt"])
        assert args.command == "process"
        assert args.file == "test.txt"

    def test_inspect_subcommand_parsed(self):
        """'inspect <file>' should set command='inspect'."""
        parser = build_arg_parser()
        args = parser.parse_args(["inspect", "test.txt"])
        assert args.command == "inspect"

    def test_default_format_is_plain(self):
        """--format should default to 'plain'."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt"])
        assert args.format == "plain"

    def test_format_option_json(self):
        """--format json should be stored correctly."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt", "--format", "json"])
        assert args.format == "json"

    def test_format_option_table(self):
        """--format table should be stored correctly."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt", "--format", "table"])
        assert args.format == "table"

    def test_verbose_flag_false_by_default(self):
        """--verbose should default to False."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt"])
        assert args.verbose is False

    def test_verbose_flag_set(self):
        """--verbose flag should set verbose to True."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt", "--verbose"])
        assert args.verbose is True

    def test_encoding_option_stored(self):
        """--encoding should be stored on the namespace."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "test.txt", "--encoding", "latin-1"])
        assert args.encoding == "latin-1"

    def test_no_command_sets_command_to_none(self):
        """Parsing with no subcommand should leave command as None."""
        parser = build_arg_parser()
        args = parser.parse_args([])
        assert args.command is None

    def test_inspect_with_json_format(self):
        """inspect subcommand should also accept --format json."""
        parser = build_arg_parser()
        args = parser.parse_args(["inspect", "doc.txt", "--format", "json"])
        assert args.command == "inspect"
        assert args.format == "json"


# ---------------------------------------------------------------------------
# validate_cli_args
# ---------------------------------------------------------------------------


class TestValidateCliArgs:
    """Tests for validate_cli_args."""

    def test_valid_process_command_does_not_raise(self):
        """A fully-specified 'process' command should pass validation."""
        parser = build_arg_parser()
        args = parser.parse_args(["process", "file.txt"])
        validate_cli_args(args)  # must not raise

    def test_valid_inspect_command_does_not_raise(self):
        """A fully-specified 'inspect' command should pass validation."""
        parser = build_arg_parser()
        args = parser.parse_args(["inspect", "file.txt"])
        validate_cli_args(args)  # must not raise

    def test_no_command_raises_config_error(self):
        """Missing subcommand should raise DocEngineConfigError."""
        parser = build_arg_parser()
        args = parser.parse_args([])
        with pytest.raises(DocEngineConfigError):
            validate_cli_args(args)

    def test_config_error_message_mentions_command(self):
        """The error message should mention subcommand names."""
        parser = build_arg_parser()
        args = parser.parse_args([])
        with pytest.raises(DocEngineConfigError, match="command"):
            validate_cli_args(args)


# ---------------------------------------------------------------------------
# run_process_command
# ---------------------------------------------------------------------------


class TestRunProcessCommand:
    """Tests for run_process_command."""

    def test_returns_zero_on_success(self, tmp_path):
        """Should return 0 when the file is processed successfully."""
        f = tmp_path / "test.txt"
        f.write_text("Hello world")
        opts = ParseOptions(file_path=str(f), format="plain")
        assert run_process_command(opts) == 0

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        """Should propagate DocEngineFileNotFoundError for missing files."""
        opts = ParseOptions(file_path=str(tmp_path / "nonexistent.txt"))
        with pytest.raises(DocEngineFileNotFoundError):
            run_process_command(opts)

    def test_json_output_is_valid_json(self, tmp_path, capsys):
        """With --format json the captured stdout should be valid JSON."""
        f = tmp_path / "test.txt"
        f.write_text("Hello world")
        opts = ParseOptions(file_path=str(f), format="json")
        run_process_command(opts)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "metadata" in parsed

    def test_plain_output_contains_type(self, tmp_path, capsys):
        """With --format plain the stdout should mention document type."""
        f = tmp_path / "test.txt"
        f.write_text("Hello world")
        opts = ParseOptions(file_path=str(f), format="plain")
        run_process_command(opts)
        captured = capsys.readouterr()
        assert "plain" in captured.out

    def test_csv_file_processed(self, tmp_path, capsys):
        """A CSV file should be processed and output without error."""
        f = tmp_path / "data.csv"
        f.write_text("name,age\nAlice,30")
        opts = ParseOptions(file_path=str(f), format="plain")
        result = run_process_command(opts)
        assert result == 0

    def test_json_file_processed(self, tmp_path, capsys):
        """A JSON file should be processed and output without error."""
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}')
        opts = ParseOptions(file_path=str(f), format="plain")
        result = run_process_command(opts)
        assert result == 0


# ---------------------------------------------------------------------------
# run_inspect_command
# ---------------------------------------------------------------------------


class TestRunInspectCommand:
    """Tests for run_inspect_command."""

    def test_returns_zero_on_success(self, tmp_path):
        """Should return 0 when metadata is successfully inspected."""
        f = tmp_path / "doc.txt"
        f.write_text("Test content")
        opts = ParseOptions(file_path=str(f), format="plain")
        assert run_inspect_command(opts) == 0

    def test_json_output_has_file_path(self, tmp_path, capsys):
        """--format json output should include file_path."""
        f = tmp_path / "doc.txt"
        f.write_text("Some text here")
        opts = ParseOptions(file_path=str(f), format="json")
        run_inspect_command(opts)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "file_path" in parsed

    def test_json_output_has_word_count(self, tmp_path, capsys):
        """--format json output should include word_count."""
        f = tmp_path / "doc.txt"
        f.write_text("Some text here")
        opts = ParseOptions(file_path=str(f), format="json")
        run_inspect_command(opts)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "word_count" in parsed

    def test_plain_output_contains_type_label(self, tmp_path, capsys):
        """Plain output should contain 'Type:' label."""
        f = tmp_path / "doc.txt"
        f.write_text("Some text here")
        opts = ParseOptions(file_path=str(f), format="plain")
        run_inspect_command(opts)
        captured = capsys.readouterr()
        assert "Type:" in captured.out

    def test_plain_output_contains_encoding_label(self, tmp_path, capsys):
        """Plain output should contain 'Encoding:' label."""
        f = tmp_path / "doc.txt"
        f.write_text("Some text here")
        opts = ParseOptions(file_path=str(f), format="plain")
        run_inspect_command(opts)
        captured = capsys.readouterr()
        assert "Encoding:" in captured.out


# ---------------------------------------------------------------------------
# main (integration)
# ---------------------------------------------------------------------------


class TestMain:
    """Integration tests for main()."""

    def test_main_exits_1_on_file_not_found(self, tmp_path, monkeypatch):
        """A missing file should cause main() to exit with code 1."""
        missing = str(tmp_path / "missing.txt")
        monkeypatch.setattr(sys, "argv", ["docengine", "process", missing])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_exits_0_on_success(self, tmp_path, monkeypatch):
        """A valid file should cause main() to exit with code 0."""
        f = tmp_path / "ok.txt"
        f.write_text("Hello world")
        monkeypatch.setattr(sys, "argv", ["docengine", "process", str(f)])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_main_no_command_exits_1(self, monkeypatch):
        """Invoking with no subcommand should exit with code 1."""
        monkeypatch.setattr(sys, "argv", ["docengine"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_version_exits_0(self, monkeypatch):
        """--version flag should exit with code 0."""
        monkeypatch.setattr(sys, "argv", ["docengine", "--version"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_main_inspect_exits_0(self, tmp_path, monkeypatch):
        """inspect subcommand on a valid file should exit with code 0."""
        f = tmp_path / "doc.txt"
        f.write_text("Inspecting this")
        monkeypatch.setattr(sys, "argv", ["docengine", "inspect", str(f)])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_main_process_json_format(self, tmp_path, monkeypatch, capsys):
        """process --format json should produce valid JSON on stdout."""
        f = tmp_path / "data.txt"
        f.write_text("Hello JSON world")
        monkeypatch.setattr(
            sys, "argv", ["docengine", "process", str(f), "--format", "json"]
        )
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "metadata" in parsed

    def test_main_error_written_to_stderr(self, tmp_path, monkeypatch, capsys):
        """Error messages from DocEngineError should appear on stderr, not stdout."""
        missing = str(tmp_path / "nope.txt")
        monkeypatch.setattr(sys, "argv", ["docengine", "process", missing])
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error:" in captured.err
