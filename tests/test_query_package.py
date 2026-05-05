"""Tests for query_package CLI."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.query_package import main, parse_args


class TestParseArgs:
    """Test command-line argument parsing."""

    def test_parse_args_defaults(self) -> None:
        """Test parsing with default arguments."""
        args = parse_args(["aaa_base"])
        assert args.source_package == "aaa_base"
        assert args.data_dir == Path.cwd()
        assert args.json is False

    def test_parse_args_with_data_dir(self, tmp_path: Path) -> None:
        """Test parsing with custom data directory."""
        args = parse_args(["bash", "--data-dir", str(tmp_path)])
        assert args.source_package == "bash"
        assert args.data_dir == tmp_path
        assert args.json is False

    def test_parse_args_with_json_flag(self) -> None:
        """Test parsing with JSON output flag."""
        args = parse_args(["coreutils", "--json"])
        assert args.source_package == "coreutils"
        assert args.data_dir == Path.cwd()
        assert args.json is True

    def test_parse_args_with_all_options(self, tmp_path: Path) -> None:
        """Test parsing with all options specified."""
        args = parse_args(["fwts", "--data-dir", str(tmp_path), "--json"])
        assert args.source_package == "fwts"
        assert args.data_dir == tmp_path
        assert args.json is True


class TestMain:
    """Test main function."""

    @pytest.fixture
    def sample_data_dir(self, tmp_path: Path) -> Path:
        """Create sample data files."""
        # Create binary_packages.json
        binary_data = {
            "aaa_base": {"name": "aaa_base", "required_by": ["aaa_base-extras"]},
            "aaa_base-extras": {"name": "aaa_base-extras", "required_by": []},
        }
        binary_file = tmp_path / "binary_packages.json"
        with open(binary_file, "w") as f:
            json.dump(binary_data, f)

        # Create media_inclusion.json
        media_data = {
            "aaa_base": {
                "SLE-15-SP7-Full-x86_64-GM-Media1": [
                    {
                        "reason_chain": ["aaa_base include"],
                        "required_by_rpm": "filesystem",
                    }
                ]
            },
            "aaa_base-extras": {
                "SLE-15-SP7-Full-x86_64-GM-Media1": [
                    {"reason_chain": ["aaa_base-extras include"], "required_by_rpm": None}
                ]
            },
        }
        media_file = tmp_path / "media_inclusion.json"
        with open(media_file, "w") as f:
            json.dump(media_data, f)

        return tmp_path

    def test_main_text_output(
        self, sample_data_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with text output."""
        with patch.object(
            sys, "argv", ["query-package", "aaa_base", "--data-dir", str(sample_data_dir)]
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        output = captured.out

        # Verify output contains key information
        assert "aaa_base" in output
        assert "aaa_base-extras" in output
        assert "Required by: aaa_base-extras" in output
        assert "SLE-15-SP7-Full-x86_64-GM-Media1" in output
        assert "filesystem" in output

    def test_main_json_output(
        self, sample_data_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with JSON output."""
        with patch.object(
            sys,
            "argv",
            ["query-package", "aaa_base", "--data-dir", str(sample_data_dir), "--json"],
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        output_json = json.loads(captured.out)

        # Verify JSON structure
        assert output_json["source_package"] == "aaa_base"
        assert output_json["found"] is True
        assert len(output_json["binary_packages"]) == 2

        # Verify first package
        pkg1 = output_json["binary_packages"][0]
        assert pkg1["binary_package"]["name"] == "aaa_base"
        assert pkg1["binary_package"]["required_by"] == ["aaa_base-extras"]
        assert pkg1["required_by_packages"] == ["aaa_base-extras"]
        assert "SLE-15-SP7-Full-x86_64-GM-Media1" in pkg1["media_inclusions"]

    def test_main_source_package_not_found(
        self, sample_data_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with non-existent source package."""
        with patch.object(
            sys,
            "argv",
            ["query-package", "nonexistent", "--data-dir", str(sample_data_dir)],
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        output = captured.out
        assert "Source package: nonexistent" in output
        assert "No binary packages found" in output

    def test_main_source_package_not_found_json(
        self, sample_data_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with non-existent source package (JSON output)."""
        with patch.object(
            sys,
            "argv",
            ["query-package", "nonexistent", "--data-dir", str(sample_data_dir), "--json"],
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        output_json = json.loads(captured.out)

        assert output_json["source_package"] == "nonexistent"
        assert output_json["found"] is False
        assert output_json["binary_packages"] == []

    def test_main_binary_packages_file_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main when binary_packages.json is missing."""
        with patch.object(
            sys, "argv", ["query-package", "test", "--data-dir", str(tmp_path)]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: binary_packages.json not found" in captured.err

    def test_main_media_inclusion_file_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main when media_inclusion.json is missing."""
        # Create only binary_packages.json
        binary_file = tmp_path / "binary_packages.json"
        with open(binary_file, "w") as f:
            json.dump({}, f)

        with patch.object(
            sys, "argv", ["query-package", "test", "--data-dir", str(tmp_path)]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: media_inclusion.json not found" in captured.err

    def test_main_invalid_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with invalid JSON files."""
        binary_file = tmp_path / "binary_packages.json"
        binary_file.write_text("invalid json {]")

        media_file = tmp_path / "media_inclusion.json"
        with open(media_file, "w") as f:
            json.dump({}, f)

        with patch.object(
            sys, "argv", ["query-package", "test", "--data-dir", str(tmp_path)]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Failed to parse" in captured.err

    def test_main_package_not_in_media(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with package that's not in any media."""
        binary_data = {"test-pkg": {"name": "test-pkg", "required_by": []}}
        binary_file = tmp_path / "binary_packages.json"
        with open(binary_file, "w") as f:
            json.dump(binary_data, f)

        media_data = {}  # Empty - package not in media
        media_file = tmp_path / "media_inclusion.json"
        with open(media_file, "w") as f:
            json.dump(media_data, f)

        with patch.object(
            sys, "argv", ["query-package", "test", "--data-dir", str(tmp_path)]
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        output = captured.out
        assert "test-pkg" in output
        assert "Not in media" in output

    def test_main_multiple_media(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main with package in multiple media."""
        binary_data = {"multi-pkg": {"name": "multi-pkg", "required_by": []}}
        binary_file = tmp_path / "binary_packages.json"
        with open(binary_file, "w") as f:
            json.dump(binary_data, f)

        media_data = {
            "multi-pkg": {
                "SLE-15-SP7-Full-x86_64-GM-Media1": [
                    {"reason_chain": ["multi-pkg include"], "required_by_rpm": None}
                ],
                "SLE-15-SP7-Full-aarch64-GM-Media1": [
                    {"reason_chain": ["multi-pkg include"], "required_by_rpm": "other-pkg"}
                ],
            }
        }
        media_file = tmp_path / "media_inclusion.json"
        with open(media_file, "w") as f:
            json.dump(media_data, f)

        with patch.object(
            sys, "argv", ["query-package", "multi", "--data-dir", str(tmp_path)]
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        output = captured.out
        assert "SLE-15-SP7-Full-x86_64-GM-Media1" in output
        assert "SLE-15-SP7-Full-aarch64-GM-Media1" in output
        assert "other-pkg" in output
