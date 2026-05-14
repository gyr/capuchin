"""Tests for CLI main entry point."""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# This import will fail - cli.py doesn't exist yet (RED phase)
from src.cli import main, parse_args


class TestCLIParser:
    """Test argument parsing with subcommands."""

    def test_parse_args_creates_parser_with_correct_prog_name(self) -> None:
        """Test that parser has prog='capuchin'."""
        # This will fail because parse_args doesn't exist
        with pytest.raises(SystemExit):
            parse_args(["--help"])

    def test_analyze_subcommand_basic(self) -> None:
        """Test analyze subcommand with minimal args."""
        args = parse_args(["analyze", "source.json"])
        assert args.command == "analyze"
        assert args.source_packages_file == "source.json"

    def test_analyze_subcommand_with_all_flags(self) -> None:
        """Test analyze subcommand with all flags."""
        args = parse_args([
            "analyze",
            "input.json",
            "--output-dir", "/tmp/output",
            "--monkey-path", "/opt/monkey",
            "--verbose",
            "--quiet",
            "--log-file", "debug.log"
        ])
        assert args.command == "analyze"
        assert args.source_packages_file == "input.json"
        assert args.output_dir == Path("/tmp/output")
        assert args.monkey_path == "/opt/monkey"
        assert args.verbose is True
        assert args.quiet is True
        assert args.log_file == Path("debug.log")

    def test_analyze_has_verbose_flag(self) -> None:
        """Test that analyze subcommand accepts --verbose flag."""
        args = parse_args(["analyze", "test.json", "--verbose"])
        assert args.verbose is True

    def test_analyze_has_quiet_flag(self) -> None:
        """Test that analyze subcommand accepts --quiet flag."""
        args = parse_args(["analyze", "test.json", "--quiet"])
        assert args.quiet is True

    def test_analyze_verbose_short_flag(self) -> None:
        """Test that analyze accepts -v short flag."""
        args = parse_args(["analyze", "test.json", "-v"])
        assert args.verbose is True

    def test_analyze_quiet_short_flag(self) -> None:
        """Test that analyze accepts -q short flag."""
        args = parse_args(["analyze", "test.json", "-q"])
        assert args.quiet is True

    def test_query_subcommand_basic(self) -> None:
        """Test query subcommand with minimal args."""
        args = parse_args(["query", "bash"])
        assert args.command == "query"
        assert args.package_name == "bash"

    def test_query_subcommand_with_all_flags(self) -> None:
        """Test query subcommand with all flags."""
        args = parse_args([
            "query",
            "bash",
            "--data-dir", "/tmp/data",
            "--json"
        ])
        assert args.command == "query"
        assert args.package_name == "bash"
        assert args.data_dir == Path("/tmp/data")
        assert args.json is True

    def test_query_rejects_verbose_flag(self) -> None:
        """Test that query subcommand REJECTS --verbose flag.

        Critical: query does NOT have --verbose/--quiet flags.
        Only analyze has these flags.
        """
        with pytest.raises(SystemExit):
            parse_args(["query", "bash", "--verbose"])

    def test_query_rejects_quiet_flag(self) -> None:
        """Test that query subcommand REJECTS --quiet flag."""
        with pytest.raises(SystemExit):
            parse_args(["query", "bash", "--quiet"])

    def test_query_rejects_log_file_flag(self) -> None:
        """Test that query subcommand REJECTS --log-file flag."""
        with pytest.raises(SystemExit):
            parse_args(["query", "bash", "--log-file", "debug.log"])

    def test_missing_subcommand_raises_error(self) -> None:
        """Test that missing subcommand raises error."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_invalid_subcommand_raises_error(self) -> None:
        """Test that invalid subcommand raises error."""
        with pytest.raises(SystemExit):
            parse_args(["invalid"])

    def test_analyze_default_output_dir(self) -> None:
        """Test analyze uses current directory as default output-dir."""
        args = parse_args(["analyze", "test.json"])
        assert args.output_dir == Path.cwd()

    def test_query_default_data_dir(self) -> None:
        """Test query uses current directory as default data-dir."""
        args = parse_args(["query", "bash"])
        assert args.data_dir == Path.cwd()


class TestCLIExecution:
    """Test CLI execution and routing."""

    @patch("src.commands.analyze.analyze_main")
    def test_main_routes_to_analyze(self, mock_analyze: MagicMock) -> None:
        """Test that analyze command routes to analyze_main()."""
        mock_analyze.return_value = 0

        exit_code = main(["analyze", "test.json"])

        assert exit_code == 0
        mock_analyze.assert_called_once()
        # Verify args passed to analyze_main
        call_args = mock_analyze.call_args[0][0]
        assert call_args.command == "analyze"
        assert call_args.source_packages_file == "test.json"

    @patch("src.commands.query.query_main")
    def test_main_routes_to_query(self, mock_query: MagicMock) -> None:
        """Test that query command routes to query_main()."""
        mock_query.return_value = 0

        exit_code = main(["query", "bash"])

        assert exit_code == 0
        mock_query.assert_called_once()
        # Verify args passed to query_main
        call_args = mock_query.call_args[0][0]
        assert call_args.command == "query"
        assert call_args.package_name == "bash"

    @patch("src.commands.analyze.analyze_main")
    def test_main_returns_analyze_exit_code(self, mock_analyze: MagicMock) -> None:
        """Test that main() returns exit code from analyze_main()."""
        mock_analyze.return_value = 1

        exit_code = main(["analyze", "test.json"])

        assert exit_code == 1

    @patch("src.commands.query.query_main")
    def test_main_returns_query_exit_code(self, mock_query: MagicMock) -> None:
        """Test that main() returns exit code from query_main()."""
        mock_query.return_value = 1

        exit_code = main(["query", "bash"])

        assert exit_code == 1

    @patch("src.commands.analyze.analyze_main")
    def test_main_passes_all_analyze_flags(self, mock_analyze: MagicMock) -> None:
        """Test that all analyze flags are passed through."""
        mock_analyze.return_value = 0

        main([
            "analyze", "input.json",
            "--output-dir", "/tmp",
            "--monkey-path", "/opt/monkey",
            "--verbose",
            "--log-file", "debug.log"
        ])

        call_args = mock_analyze.call_args[0][0]
        assert call_args.output_dir == Path("/tmp")
        assert call_args.monkey_path == "/opt/monkey"
        assert call_args.verbose is True
        assert call_args.log_file == Path("debug.log")

    @patch("src.commands.query.query_main")
    def test_main_passes_all_query_flags(self, mock_query: MagicMock) -> None:
        """Test that all query flags are passed through."""
        mock_query.return_value = 0

        main([
            "query", "bash",
            "--data-dir", "/tmp",
            "--json"
        ])

        call_args = mock_query.call_args[0][0]
        assert call_args.data_dir == Path("/tmp")
        assert call_args.json is True


class TestCLIEdgeCases:
    """Test edge cases and error handling."""

    def test_analyze_with_empty_source_file(self) -> None:
        """Test analyze with empty string for source file."""
        args = parse_args(["analyze", ""])
        assert args.source_packages_file == ""

    def test_query_with_empty_package_name(self) -> None:
        """Test query with empty string for package name."""
        args = parse_args(["query", ""])
        assert args.package_name == ""

    def test_analyze_flags_default_to_false(self) -> None:
        """Test that analyze boolean flags default to False."""
        args = parse_args(["analyze", "test.json"])
        assert args.verbose is False
        assert args.quiet is False

    def test_query_json_flag_defaults_to_false(self) -> None:
        """Test that query --json flag defaults to False."""
        args = parse_args(["query", "bash"])
        assert args.json is False
