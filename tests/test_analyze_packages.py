"""Tests for analyze_packages CLI."""

import json
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
            ["aaa_base", "bash", "coreutils"]
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

    @patch("src.analyze_packages.Config")
    def test_main_file_not_found(
        self, mock_config: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with non-existent source packages file."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        nonexistent = tmp_path / "nonexistent.json"

        with patch.object(
            sys, "argv", ["analyze_packages", str(nonexistent)]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Source packages file not found" in captured.err

    @patch("src.analyze_packages.Config")
    def test_main_invalid_json(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test main with invalid JSON file."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json {]")

        with patch.object(sys, "argv", ["analyze_packages", str(invalid_file)]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Failed to parse source packages file" in captured.err

    @patch("src.analyze_packages.Config")
    def test_main_not_a_list(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test main with JSON that is not a list."""
        mock_config.get_package_monkey_path.return_value = Path("/opt/monkey")
        invalid_file = tmp_path / "notlist.json"
        with open(invalid_file, "w") as f:
            json.dump({"key": "value"}, f)

        with patch.object(sys, "argv", ["analyze_packages", str(invalid_file)]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Source packages file must contain a JSON array" in captured.err

    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_config_error(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        sample_source_packages_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test main when Config raises an error."""
        mock_config.get_package_monkey_path.side_effect = ValueError(
            "PACKAGE_MONKEY_PATH not set"
        )

        with patch.object(
            sys, "argv", ["analyze_packages", str(sample_source_packages_file)]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: PACKAGE_MONKEY_PATH not set" in captured.err

    @patch("src.analyze_packages.PackageAnalyzer")
    @patch("src.analyze_packages.Config")
    def test_main_analyzer_error(
        self,
        mock_config: MagicMock,
        mock_analyzer_class: MagicMock,
        sample_source_packages_file: Path,
        capsys: pytest.CaptureFixture[str],
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
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Failed to run monkey command" in captured.err

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
        mock_analyzer.analyze_and_write.assert_called_once_with([])
