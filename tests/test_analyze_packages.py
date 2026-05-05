"""Tests for analyze_packages CLI."""

import json
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.analyze_packages import main, parse_args


class TestParseArgs:
    """Test command-line argument parsing."""

    def test_parse_args_defaults(self) -> None:
        """Test parsing with default arguments."""
        args = parse_args(["source_packages.json"])
        assert args.source_packages_file == "source_packages.json"
        assert args.output_dir == Path.cwd()
        assert args.monkey_path is None

    def test_parse_args_with_output_dir(self, tmp_path: Path) -> None:
        """Test parsing with custom output directory."""
        args = parse_args(["source_packages.json", "--output-dir", str(tmp_path)])
        assert args.source_packages_file == "source_packages.json"
        assert args.output_dir == tmp_path

    def test_parse_args_with_monkey_path(self) -> None:
        """Test parsing with custom monkey path."""
        args = parse_args(
            ["source_packages.json", "--monkey-path", "/custom/monkey"]
        )
        assert args.source_packages_file == "source_packages.json"
        assert args.monkey_path == "/custom/monkey"

    def test_parse_args_with_all_options(self, tmp_path: Path) -> None:
        """Test parsing with all options specified."""
        args = parse_args(
            [
                "input.json",
                "--output-dir",
                str(tmp_path),
                "--monkey-path",
                "/opt/monkey",
            ]
        )
        assert args.source_packages_file == "input.json"
        assert args.output_dir == tmp_path
        assert args.monkey_path == "/opt/monkey"

    def test_parse_args_with_verbose_flag(self) -> None:
        """Test parsing with --verbose flag."""
        args = parse_args(["source_packages.json", "--verbose"])
        assert args.verbose is True

    def test_parse_args_with_verbose_short_flag(self) -> None:
        """Test parsing with -v short flag."""
        args = parse_args(["source_packages.json", "-v"])
        assert args.verbose is True

    def test_parse_args_with_quiet_flag(self) -> None:
        """Test parsing with --quiet flag."""
        args = parse_args(["source_packages.json", "--quiet"])
        assert args.quiet is True

    def test_parse_args_with_quiet_short_flag(self) -> None:
        """Test parsing with -q short flag."""
        args = parse_args(["source_packages.json", "-q"])
        assert args.quiet is True

    def test_parse_args_with_log_file(self, tmp_path: Path) -> None:
        """Test parsing with --log-file option."""
        log_file = tmp_path / "analysis.log"
        args = parse_args(["source_packages.json", "--log-file", str(log_file)])
        assert args.log_file == log_file

    def test_parse_args_defaults_no_logging_flags(self) -> None:
        """Test that logging flags default to False/None."""
        args = parse_args(["source_packages.json"])
        assert args.verbose is False
        assert args.quiet is False
        assert args.log_file is None


class TestMain:
    """Test main function."""

    @pytest.fixture
    def sample_source_packages_file(self, tmp_path: Path) -> Path:
        """Create a sample source_packages.json file."""
        source_file = tmp_path / "source_packages.json"
        data = ["aaa_base", "bash", "coreutils"]
        with open(source_file, "w") as f:
            json.dump(data, f)
        return source_file

    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_success(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        sample_source_packages_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test successful execution of main."""
        # Setup mocks
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        # Run main
        with patch.object(
            sys,
            "argv",
            ["analyze_packages", str(sample_source_packages_file), "--output-dir", str(tmp_path)],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_config.get_package_monkey_path.assert_called_once()
        mock_analyzer_class.assert_called_once_with(
            monkey_path=str(Path("/opt/monkey")), output_dir=tmp_path
        )
        mock_analyzer.analyze_and_write.assert_called_once_with(
            ["aaa_base", "bash", "coreutils"], show_progress=True
        )

    @patch("src.analyze_packages.Config")
    def test_main_with_custom_monkey_path(
        self,
        mock_config: MagicMock,
        sample_source_packages_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test main with custom monkey path (should not call Config)."""
        with patch("src.analyze_packages.PackageAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer

            with patch.object(
                sys,
                "argv",
                [
                    "analyze_packages",
                    str(sample_source_packages_file),
                    "--monkey-path",
                    "/custom/monkey",
                ],
            ):
                result = main()

            # Config should NOT be called when monkey_path is provided
            mock_config.get_package_monkey_path.assert_not_called()
            mock_analyzer_class.assert_called_once_with(
                monkey_path="/custom/monkey", output_dir=Path.cwd()
            )
            assert result == 0

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.Config")
    def test_main_file_not_found(
        self,
        mock_config: MagicMock,
        mock_setup_logging: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test main with non-existent source packages file."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        nonexistent = tmp_path / "nonexistent.json"

        with patch.object(
            sys, "argv", ["analyze_packages", str(nonexistent)]
        ):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "Source packages file not found" in caplog.text

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.Config")
    def test_main_invalid_json(
        self,
        mock_config: MagicMock,
        mock_setup_logging: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test main with invalid JSON file."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json {]")

        with patch.object(sys, "argv", ["analyze_packages", str(invalid_file)]):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "Failed to parse source packages file" in caplog.text

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.Config")
    def test_main_not_a_list(
        self,
        mock_config: MagicMock,
        mock_setup_logging: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test main with JSON that is not a list."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        invalid_file = tmp_path / "notlist.json"
        with open(invalid_file, "w") as f:
            json.dump({"key": "value"}, f)

        with patch.object(sys, "argv", ["analyze_packages", str(invalid_file)]):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "Source packages file must contain a JSON array" in caplog.text

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_config_error(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test main when Config raises an error."""
        mock_config.get_package_monkey_path.side_effect = ValueError(
            "PACKAGE_MONKEY_PATH not set"
        )

        with patch.object(
            sys, "argv", ["analyze_packages", str(sample_source_packages_file)]
        ):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "PACKAGE_MONKEY_PATH not set" in caplog.text

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_analyzer_error(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test main when PackageAnalyzer raises an error."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_and_write.side_effect = RuntimeError(
            "Failed to run monkey command"
        )

        with patch.object(
            sys, "argv", ["analyze_packages", str(sample_source_packages_file)]
        ):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "Failed to run monkey command" in caplog.text

    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_empty_package_list(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test main with empty package list (should still succeed)."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        empty_file = tmp_path / "empty.json"
        with open(empty_file, "w") as f:
            json.dump([], f)

        with patch.object(sys, "argv", ["analyze_packages", str(empty_file)]):
            result = main()

        assert result == 0
        mock_analyzer.analyze_and_write.assert_called_once_with([], show_progress=True)

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_calls_setup_logging_default(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
    ) -> None:
        """Test that main calls setup_logging with default parameters."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        with patch.object(sys, "argv", ["analyze_packages", str(sample_source_packages_file)]):
            main()

        mock_setup_logging.assert_called_once_with(
            verbose=False, log_file=None, quiet=False
        )

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_calls_setup_logging_verbose(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
    ) -> None:
        """Test that main calls setup_logging with verbose=True."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        with patch.object(
            sys, "argv", ["analyze_packages", str(sample_source_packages_file), "--verbose"]
        ):
            main()

        mock_setup_logging.assert_called_once_with(
            verbose=True, log_file=None, quiet=False
        )

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_calls_setup_logging_quiet(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
    ) -> None:
        """Test that main calls setup_logging with quiet=True."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        with patch.object(
            sys, "argv", ["analyze_packages", str(sample_source_packages_file), "--quiet"]
        ):
            main()

        mock_setup_logging.assert_called_once_with(
            verbose=False, log_file=None, quiet=True
        )

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_calls_setup_logging_with_log_file(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test that main calls setup_logging with log_file."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        log_file = tmp_path / "test.log"

        with patch.object(
            sys,
            "argv",
            [
                "analyze_packages",
                str(sample_source_packages_file),
                "--log-file",
                str(log_file),
            ],
        ):
            main()

        mock_setup_logging.assert_called_once_with(
            verbose=False, log_file=log_file, quiet=False
        )

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.Config")
    def test_main_logs_error_on_file_not_found(
        self,
        mock_config: MagicMock,
        mock_setup_logging: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that errors are logged when file not found."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")

        with patch.object(sys, "argv", ["analyze_packages", "nonexistent.json"]):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "Source packages file not found" in caplog.text

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.Config")
    def test_main_logs_error_on_invalid_json(
        self,
        mock_config: MagicMock,
        mock_setup_logging: MagicMock,
        caplog: pytest.LogCaptureFixture,
        tmp_path: Path,
    ) -> None:
        """Test that errors are logged when JSON is invalid."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")

        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("{invalid json")

        with patch.object(sys, "argv", ["analyze_packages", str(invalid_file)]):
            with caplog.at_level(logging.ERROR):
                result = main()

        assert result == 1
        assert "Failed to parse source packages file" in caplog.text

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_progress_bar_enabled_by_default(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
    ) -> None:
        """Test that progress bar is enabled by default."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        with patch.object(sys, "argv", ["analyze_packages", str(sample_source_packages_file)]):
            main()

        # Verify analyze_and_write was called with show_progress=True
        mock_analyzer.analyze_and_write.assert_called_once()
        call_args = mock_analyzer.analyze_and_write.call_args
        assert call_args[1]["show_progress"] is True

    @patch("src.analyze_packages.setup_logging")
    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_quiet_disables_progress_bar(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_setup_logging: MagicMock,
        sample_source_packages_file: Path,
    ) -> None:
        """Test that --quiet flag disables progress bar."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer

        with patch.object(
            sys, "argv", ["analyze_packages", str(sample_source_packages_file), "--quiet"]
        ):
            main()

        # Verify analyze_and_write was called with show_progress=False
        mock_analyzer.analyze_and_write.assert_called_once()
        call_args = mock_analyzer.analyze_and_write.call_args
        assert call_args[1]["show_progress"] is False
