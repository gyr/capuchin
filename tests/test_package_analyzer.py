"""Tests for PackageAnalyzer."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.package_analyzer import PackageAnalyzer


@pytest.fixture
def sample_buildinfo_output() -> str:
    """Sample buildinfo output for testing."""
    return """Build aaa_base (SLE15-SP7)

aaa_base (Standard)
  required by:
    - aaa_base-extras (Standard)

aaa_base-extras (Standard)
"""


@pytest.fixture
def sample_ex_output() -> str:
    """Sample ex output for aaa_base."""
    return """SLE-15-SP7-Full-x86_64-GM-Media1:
 └─> aaa_base include
     is required by rpm: filesystem"""


@pytest.fixture
def sample_ex_output_no_required() -> str:
    """Sample ex output without required_by_rpm."""
    return """SLE-15-SP7-Full-x86_64-GM-Media1:
 └─> aaa_base-extras include"""


@pytest.fixture
def analyzer(tmp_path: Path) -> PackageAnalyzer:
    """Create PackageAnalyzer instance for testing."""
    monkey_path = "/opt/monkey"
    return PackageAnalyzer(monkey_path=monkey_path, output_dir=tmp_path)


class TestPackageAnalyzerInit:
    """Test PackageAnalyzer initialization."""

    def test_init_with_defaults(self, tmp_path: Path) -> None:
        """Test initialization with default output directory."""
        analyzer = PackageAnalyzer(monkey_path="/opt/monkey")
        assert analyzer.monkey_path == "/opt/monkey"
        assert analyzer.output_dir == Path.cwd()

    def test_init_with_custom_output_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom output directory."""
        analyzer = PackageAnalyzer(
            monkey_path="/opt/monkey", output_dir=tmp_path
        )
        assert analyzer.monkey_path == "/opt/monkey"
        assert analyzer.output_dir == tmp_path


class TestCommandExecution:
    """Test command execution methods."""

    @patch("subprocess.run")
    def test_run_buildinfo_success(
        self, mock_run: MagicMock, analyzer: PackageAnalyzer, sample_buildinfo_output: str
    ) -> None:
        """Test successful buildinfo command execution."""
        mock_run.return_value = MagicMock(
            stdout=sample_buildinfo_output, returncode=0
        )

        result = analyzer._run_buildinfo("aaa_base")

        assert result == sample_buildinfo_output
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd == ["monkey", "buildinfo", "aaa_base"]
        assert kwargs["cwd"] == analyzer.monkey_path

    @patch("subprocess.run")
    def test_run_buildinfo_command_failure(
        self, mock_run: MagicMock, analyzer: PackageAnalyzer
    ) -> None:
        """Test buildinfo command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "monkey")

        with pytest.raises(RuntimeError, match="Failed to run monkey buildinfo"):
            analyzer._run_buildinfo("nonexistent")

    @patch("subprocess.run")
    def test_run_ex_success(
        self, mock_run: MagicMock, analyzer: PackageAnalyzer, sample_ex_output: str
    ) -> None:
        """Test successful ex command execution."""
        mock_run.return_value = MagicMock(stdout=sample_ex_output, returncode=0)

        result = analyzer._run_ex("aaa_base")

        assert result == sample_ex_output
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd == ["monkey", "ex", "aaa_base"]
        assert kwargs["cwd"] == analyzer.monkey_path

    @patch("subprocess.run")
    def test_run_ex_command_failure(
        self, mock_run: MagicMock, analyzer: PackageAnalyzer
    ) -> None:
        """Test ex command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "monkey")

        with pytest.raises(RuntimeError, match="Failed to run monkey ex"):
            analyzer._run_ex("nonexistent")


class TestAnalyzeSinglePackage:
    """Test analyzing a single source package."""

    @patch("src.package_analyzer.PackageAnalyzer._run_ex")
    @patch("src.package_analyzer.PackageAnalyzer._run_buildinfo")
    def test_analyze_single_package_success(
        self,
        mock_buildinfo: MagicMock,
        mock_ex: MagicMock,
        analyzer: PackageAnalyzer,
        sample_buildinfo_output: str,
        sample_ex_output: str,
        sample_ex_output_no_required: str,
    ) -> None:
        """Test successful analysis of a single source package."""
        mock_buildinfo.return_value = sample_buildinfo_output
        mock_ex.side_effect = [sample_ex_output, sample_ex_output_no_required]

        binary_pkgs, media_inclusions = analyzer.analyze_source_package("aaa_base")

        # Verify binary packages
        assert len(binary_pkgs) == 2
        assert "aaa_base" in binary_pkgs
        assert "aaa_base-extras" in binary_pkgs
        assert binary_pkgs["aaa_base"].name == "aaa_base"
        assert binary_pkgs["aaa_base"].required_by == ["aaa_base-extras"]
        assert binary_pkgs["aaa_base-extras"].name == "aaa_base-extras"
        assert binary_pkgs["aaa_base-extras"].required_by == []

        # Verify media inclusions
        assert len(media_inclusions) == 2
        assert "aaa_base" in media_inclusions
        assert "aaa_base-extras" in media_inclusions

        # Check aaa_base media inclusion
        aaa_base_media = media_inclusions["aaa_base"]
        assert "SLE-15-SP7-Full-x86_64-GM-Media1" in aaa_base_media.included_in
        reasons = aaa_base_media.included_in["SLE-15-SP7-Full-x86_64-GM-Media1"]
        assert len(reasons) == 1
        assert reasons[0].reason_chain == ["aaa_base include"]
        assert reasons[0].required_by_rpm == "filesystem"

        # Check aaa_base-extras media inclusion
        extras_media = media_inclusions["aaa_base-extras"]
        assert "SLE-15-SP7-Full-x86_64-GM-Media1" in extras_media.included_in
        reasons = extras_media.included_in["SLE-15-SP7-Full-x86_64-GM-Media1"]
        assert len(reasons) == 1
        assert reasons[0].reason_chain == ["aaa_base-extras include"]
        assert reasons[0].required_by_rpm is None

    @patch("src.package_analyzer.PackageAnalyzer._run_buildinfo")
    def test_analyze_nonexistent_source_package(
        self, mock_buildinfo: MagicMock, analyzer: PackageAnalyzer
    ) -> None:
        """Test analyzing a non-existent source package."""
        mock_buildinfo.return_value = "foobar: not found\n"

        binary_pkgs, media_inclusions = analyzer.analyze_source_package("foobar")

        assert len(binary_pkgs) == 0
        assert len(media_inclusions) == 0

    @patch("src.package_analyzer.PackageAnalyzer._run_ex")
    @patch("src.package_analyzer.PackageAnalyzer._run_buildinfo")
    def test_analyze_package_with_nonexistent_binary(
        self,
        mock_buildinfo: MagicMock,
        mock_ex: MagicMock,
        analyzer: PackageAnalyzer,
    ) -> None:
        """Test analyzing when a binary package doesn't exist in media."""
        buildinfo_output = """Build test (SLE15-SP7)

test-bin (Standard)
"""
        ex_output = """SLE-15-SP7-Full-x86_64-GM-Media1:
 └─> spurious decision"""

        mock_buildinfo.return_value = buildinfo_output
        mock_ex.return_value = ex_output

        binary_pkgs, media_inclusions = analyzer.analyze_source_package("test")

        # Binary package should exist
        assert len(binary_pkgs) == 1
        assert "test-bin" in binary_pkgs

        # But no media inclusion (spurious decision)
        assert len(media_inclusions) == 0


class TestAnalyzeMultiplePackages:
    """Test analyzing multiple source packages."""

    @patch("src.package_analyzer.PackageAnalyzer._run_ex")
    @patch("src.package_analyzer.PackageAnalyzer._run_buildinfo")
    def test_analyze_packages_multiple(
        self,
        mock_buildinfo: MagicMock,
        mock_ex: MagicMock,
        analyzer: PackageAnalyzer,
    ) -> None:
        """Test analyzing multiple source packages."""

        def buildinfo_side_effect(pkg: str) -> str:
            if pkg == "pkg1":
                return """Build pkg1 (SLE15-SP7)

pkg1-bin (Standard)
"""
            elif pkg == "pkg2":
                return """Build pkg2 (SLE15-SP7)

pkg2-bin (Standard)
"""
            return ""

        def ex_side_effect(pkg: str) -> str:
            return f"""SLE-15-SP7-Full-x86_64-GM-Media1:
 └─> {pkg} include"""

        mock_buildinfo.side_effect = buildinfo_side_effect
        mock_ex.side_effect = ex_side_effect

        binary_pkgs, media_inclusions = analyzer.analyze_packages(["pkg1", "pkg2"])

        assert len(binary_pkgs) == 2
        assert "pkg1-bin" in binary_pkgs
        assert "pkg2-bin" in binary_pkgs

        assert len(media_inclusions) == 2
        assert "pkg1-bin" in media_inclusions
        assert "pkg2-bin" in media_inclusions


class TestJSONOutput:
    """Test JSON output generation."""

    @patch("src.package_analyzer.PackageAnalyzer._run_ex")
    @patch("src.package_analyzer.PackageAnalyzer._run_buildinfo")
    def test_write_json_files(
        self,
        mock_buildinfo: MagicMock,
        mock_ex: MagicMock,
        analyzer: PackageAnalyzer,
        sample_buildinfo_output: str,
        sample_ex_output: str,
        sample_ex_output_no_required: str,
    ) -> None:
        """Test writing binary_packages.json and media_inclusion.json."""
        mock_buildinfo.return_value = sample_buildinfo_output
        mock_ex.side_effect = [sample_ex_output, sample_ex_output_no_required]

        # Analyze and write
        analyzer.analyze_and_write(["aaa_base"])

        # Verify binary_packages.json
        binary_json = analyzer.output_dir / "binary_packages.json"
        assert binary_json.exists()

        with open(binary_json) as f:
            binary_data = json.load(f)

        assert "aaa_base" in binary_data
        assert "aaa_base-extras" in binary_data
        assert binary_data["aaa_base"]["name"] == "aaa_base"
        assert binary_data["aaa_base"]["required_by"] == ["aaa_base-extras"]

        # Verify media_inclusion.json
        media_json = analyzer.output_dir / "media_inclusion.json"
        assert media_json.exists()

        with open(media_json) as f:
            media_data = json.load(f)

        assert "aaa_base" in media_data
        assert "SLE-15-SP7-Full-x86_64-GM-Media1" in media_data["aaa_base"]
        reasons = media_data["aaa_base"]["SLE-15-SP7-Full-x86_64-GM-Media1"]
        assert len(reasons) == 1
        assert reasons[0]["reason_chain"] == ["aaa_base include"]
        assert reasons[0]["required_by_rpm"] == "filesystem"

    def test_write_empty_analysis(self, analyzer: PackageAnalyzer) -> None:
        """Test writing empty results."""
        # Manually write empty results
        analyzer._write_results({}, {})

        binary_json = analyzer.output_dir / "binary_packages.json"
        media_json = analyzer.output_dir / "media_inclusion.json"

        assert binary_json.exists()
        assert media_json.exists()

        with open(binary_json) as f:
            assert json.load(f) == {}

        with open(media_json) as f:
            assert json.load(f) == {}
