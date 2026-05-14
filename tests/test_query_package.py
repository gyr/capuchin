"""Tests for query_package CLI."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.commands.query import (
    format_human_readable,
    load_packages,
    parse_args,
    query_main,
    query_package,
)


class TestParseArgs:
    """Test command-line argument parsing."""

    def test_parse_args_defaults(self) -> None:
        """Test parsing with default arguments."""
        args = parse_args(["bash"])
        assert args.package_name == "bash"
        assert args.data_dir == Path.cwd()
        assert args.json is False

    def test_parse_args_with_data_dir(self, tmp_path: Path) -> None:
        """Test parsing with custom data directory."""
        args = parse_args(["bash", "--data-dir", str(tmp_path)])
        assert args.package_name == "bash"
        assert args.data_dir == tmp_path

    def test_parse_args_with_json_flag(self) -> None:
        """Test parsing with JSON output flag."""
        args = parse_args(["bash", "--json"])
        assert args.package_name == "bash"
        assert args.json is True


class TestLoadPackages:
    """Test load_packages function."""

    @pytest.fixture
    def sample_packages_file(self, tmp_path: Path) -> Path:
        """Create a sample packages.json file."""
        packages_file = tmp_path / "packages.json"
        data = {
            "bash": {
                "bash": {
                    "required_by": ["bash-completion"],
                    "included": True,
                    "required_by_rpm": ["filesystem"],
                },
                "bash-doc": {
                    "required_by": [],
                    "included": False,
                    "required_by_rpm": [],
                },
            },
            "grep": {
                "grep": {
                    "required_by": [],
                    "included": False,
                    "required_by_rpm": [],
                }
            },
        }
        with open(packages_file, "w") as f:
            json.dump(data, f)
        return packages_file

    def test_load_packages_success(self, sample_packages_file: Path, tmp_path: Path) -> None:
        """Test successfully loading packages.json."""
        packages = load_packages(tmp_path)

        assert "bash" in packages
        assert "grep" in packages
        assert "bash" in packages["bash"]
        assert "bash-doc" in packages["bash"]

    def test_load_packages_file_not_found(self, tmp_path: Path) -> None:
        """Test loading when packages.json doesn't exist."""
        with pytest.raises(FileNotFoundError, match="packages.json not found"):
            load_packages(tmp_path)


class TestQueryPackage:
    """Test query_package function."""

    @pytest.fixture
    def sample_data(self) -> dict[str, dict[str, dict[str, object]]]:
        """Sample packages data."""
        return {
            "bash": {
                "bash": {
                    "required_by": ["bash-completion", "rpm"],
                    "included": True,
                    "required_by_rpm": ["filesystem"],
                },
                "bash-doc": {
                    "required_by": [],
                    "included": False,
                    "required_by_rpm": [],
                },
            },
            "gettext-runtime": {
                "gettext-runtime": {
                    "required_by": ["gettext-tools"],
                    "included": True,
                    "required_by_rpm": ["glibc"],
                },
                "envsubst": {
                    "required_by": ["gettext-runtime"],
                    "included": False,
                    "required_by_rpm": [],
                },
            },
        }

    def test_query_by_source_package(self, sample_data: dict) -> None:
        """Test querying by source package name."""
        result = query_package("bash", sample_data)

        assert result["type"] == "source"
        assert result["source_package"] == "bash"
        assert "bash" in result["binaries"]
        assert "bash-doc" in result["binaries"]

    def test_query_by_binary_package(self, sample_data: dict) -> None:
        """Test querying by binary package name (not same as source)."""
        result = query_package("envsubst", sample_data)

        assert result["type"] == "binary"
        assert result["source_package"] == "gettext-runtime"
        assert result["binary_package"] == "envsubst"
        assert result["data"]["required_by"] == ["gettext-runtime"]
        assert result["data"]["included"] is False

    def test_query_not_found(self, sample_data: dict) -> None:
        """Test querying for non-existent package."""
        result = query_package("nonexistent", sample_data)

        assert result["type"] == "not_found"
        assert result["package_name"] == "nonexistent"


class TestFormatHumanReadable:
    """Test format_human_readable function."""

    def test_format_source_package(self) -> None:
        """Test formatting source package result."""
        query_result = {
            "type": "source",
            "source_package": "bash",
            "binaries": {
                "bash": {
                    "required_by": ["rpm"],
                    "included": True,
                    "required_by_rpm": ["filesystem"],
                },
                "bash-doc": {
                    "required_by": [],
                    "included": False,
                    "required_by_rpm": [],
                },
            },
        }

        output = format_human_readable(query_result)

        assert "Source package: bash" in output
        assert "Binary packages:" in output
        assert "bash" in output
        assert "required_by: ['rpm']" in output or 'required_by: ["rpm"]' in output
        assert "included: True" in output
        assert "bash-doc" in output
        assert "included: False" in output

    def test_format_binary_package(self) -> None:
        """Test formatting binary package result."""
        query_result = {
            "type": "binary",
            "binary_package": "envsubst",
            "source_package": "gettext-runtime",
            "data": {
                "required_by": ["gettext-runtime"],
                "included": False,
                "required_by_rpm": [],
            },
        }

        output = format_human_readable(query_result)

        assert "Binary package: envsubst" in output
        assert "Source package: gettext-runtime" in output
        assert "required_by:" in output
        assert "included: False" in output

    def test_format_not_found(self) -> None:
        """Test formatting not found result."""
        query_result = {
            "type": "not_found",
            "package_name": "nonexistent",
        }

        output = format_human_readable(query_result)

        assert "Package not found: nonexistent" in output


class TestMain:
    """Test main function."""

    @pytest.fixture
    def sample_packages_file(self, tmp_path: Path) -> Path:
        """Create sample packages.json."""
        packages_file = tmp_path / "packages.json"
        data = {
            "bash": {
                "bash": {
                    "required_by": ["rpm"],
                    "included": True,
                    "required_by_rpm": ["filesystem"],
                }
            }
        }
        with open(packages_file, "w") as f:
            json.dump(data, f)
        return packages_file

    @patch("sys.argv", ["query_package", "bash", "--data-dir", "/tmp"])
    @patch("src.commands.query.load_packages")
    def test_main_success_human_readable(self, mock_load: MagicMock) -> None:
        """Test successful query with human-readable output."""
        mock_load.return_value = {
            "bash": {
                "bash": {
                    "required_by": ["rpm"],
                    "included": True,
                    "required_by_rpm": ["filesystem"],
                }
            }
        }

        result = query_main()

        assert result == 0
        mock_load.assert_called_once()

    @patch("sys.argv", ["query_package", "bash", "--data-dir", "/tmp", "--json"])
    @patch("src.commands.query.load_packages")
    def test_main_success_json_output(self, mock_load: MagicMock) -> None:
        """Test successful query with JSON output."""
        mock_load.return_value = {
            "bash": {
                "bash": {
                    "required_by": ["rpm"],
                    "included": True,
                    "required_by_rpm": ["filesystem"],
                }
            }
        }

        result = query_main()

        assert result == 0

    @patch("sys.argv", ["query_package", "bash"])
    @patch("src.commands.query.load_packages")
    def test_main_file_not_found(self, mock_load: MagicMock) -> None:
        """Test when packages.json is not found."""
        mock_load.side_effect = FileNotFoundError("packages.json not found")

        result = query_main()

        assert result == 1

    @patch("sys.argv", ["query_package", "bash"])
    @patch("src.commands.query.load_packages")
    def test_main_unexpected_error(self, mock_load: MagicMock) -> None:
        """Test handling of unexpected errors."""
        mock_load.side_effect = Exception("Unexpected error")

        result = query_main()

        assert result == 1

    @patch("sys.argv", ["query_package", "bash"])
    @patch("src.commands.query.load_packages")
    def test_main_logs_file_not_found_error(
        self, mock_load: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that FileNotFoundError is logged at ERROR level."""
        mock_load.side_effect = FileNotFoundError("packages.json not found in /tmp")

        with caplog.at_level(logging.ERROR):
            result = query_main()

        assert result == 1
        assert "packages.json not found in /tmp" in caplog.text

    @patch("sys.argv", ["query_package", "bash", "--data-dir", "/tmp"])
    def test_main_logs_json_decode_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that JSONDecodeError is logged at ERROR level."""
        # Create invalid JSON file
        invalid_json = tmp_path / "packages.json"
        invalid_json.write_text("{ invalid json ]")

        with (
            patch("sys.argv", ["query_package", "bash", "--data-dir", str(tmp_path)]),
            caplog.at_level(logging.ERROR),
        ):
            result = query_main()

        assert result == 1
        assert "Failed to parse packages.json" in caplog.text

    @patch("sys.argv", ["query_package", "bash"])
    @patch("src.commands.query.load_packages")
    def test_main_logs_unexpected_error(
        self, mock_load: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that unexpected errors are logged at ERROR level."""
        mock_load.side_effect = Exception("Something went wrong")

        with caplog.at_level(logging.ERROR):
            result = query_main()

        assert result == 1
        assert "Something went wrong" in caplog.text
