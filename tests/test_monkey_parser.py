"""Tests for monkey parser module."""

from pathlib import Path

import pytest

from src.monkey_parser import MonkeyParser, ParseError


class TestMonkeyParser:
    """Test suite for MonkeyParser."""

    @pytest.fixture
    def parser(self) -> MonkeyParser:
        """Create a MonkeyParser instance."""
        return MonkeyParser()

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    def test_parse_buildinfo_simple(self, parser: MonkeyParser, fixtures_dir: Path) -> None:
        """Test parsing buildinfo with simple package structure."""
        buildinfo_output = (fixtures_dir / "buildinfo_simple.txt").read_text()
        packages = parser.parse_buildinfo(buildinfo_output)

        assert len(packages) == 3

        # Check first package (no required_by)
        pkg1 = packages[0]
        assert pkg1.name == "gettext-runtime"
        assert pkg1.required_by == []

        # Check second package (no required_by)
        pkg2 = packages[1]
        assert pkg2.name == "gettext-runtime-32bit"
        assert pkg2.required_by == []

        # Check third package with dependencies
        pkg3 = packages[2]
        assert pkg3.name == "gettext-tools"
        assert len(pkg3.required_by) == 2
        assert pkg3.required_by == ["fontconfig-devel", "intltool"]

    def test_parse_buildinfo_with_dependencies(
        self, parser: MonkeyParser, fixtures_dir: Path
    ) -> None:
        """Test parsing buildinfo with dependencies."""
        buildinfo_output = (fixtures_dir / "buildinfo_with_dependencies.txt").read_text()
        packages = parser.parse_buildinfo(buildinfo_output)

        assert len(packages) == 2

        # Check package with dependencies
        fwts = packages[0]
        assert fwts.name == "fwts"
        assert len(fwts.required_by) == 2
        assert fwts.required_by == ["qa_test_fwts", "validation-tools"]

        # Check package without dependencies
        fwts_devel = packages[1]
        assert fwts_devel.name == "fwts-devel"
        assert fwts_devel.required_by == []

    def test_parse_buildinfo_empty(self, parser: MonkeyParser) -> None:
        """Test parsing empty buildinfo output."""
        packages = parser.parse_buildinfo("")
        assert packages == []

    def test_parse_buildinfo_malformed(self, parser: MonkeyParser) -> None:
        """Test parsing malformed buildinfo raises ParseError."""
        malformed = "This is not valid buildinfo output"
        with pytest.raises(ParseError, match="Invalid buildinfo format"):
            parser.parse_buildinfo(malformed)

    def test_parse_buildinfo_not_found(self, parser: MonkeyParser, fixtures_dir: Path) -> None:
        """Test parsing buildinfo for non-existent source package."""
        buildinfo_output = (fixtures_dir / "buildinfo_not_found.txt").read_text()
        packages = parser.parse_buildinfo(buildinfo_output)
        # Should return empty list for non-existent packages
        assert packages == []

    def test_parse_ex_simple(self, parser: MonkeyParser, fixtures_dir: Path) -> None:
        """Test parsing simple ex output with multiple media."""
        ex_output = (fixtures_dir / "ex_simple.txt").read_text()
        included, required_by_rpm = parser.parse_ex(ex_output)

        # Package is in media (sles_16.1 and sleha_16.1)
        assert included is True
        # Should collect required_by_rpm from sles_16.1 (fontconfig-devel)
        # sleha_16.1 has no required_by_rpm so only one value
        assert "fontconfig-devel" in required_by_rpm

    def test_parse_ex_multiple_paths(self, parser: MonkeyParser, fixtures_dir: Path) -> None:
        """Test parsing ex output with package that has required_by_rpm."""
        ex_output = (fixtures_dir / "ex_multiple_paths.txt").read_text()
        included, required_by_rpm = parser.parse_ex(ex_output)

        # Package is in media
        assert included is True
        # Should extract the required_by_rpm from the tree
        assert "qa_test_fwts" in required_by_rpm
        assert len(required_by_rpm) == 1

    def test_parse_ex_not_in_media(self, parser: MonkeyParser, fixtures_dir: Path) -> None:
        """Test parsing empty ex output (package not in media)."""
        ex_output = (fixtures_dir / "ex_not_in_media.txt").read_text()
        included, required_by_rpm = parser.parse_ex(ex_output)

        # Package is NOT in any media
        assert included is False
        assert required_by_rpm == []

    def test_parse_ex_empty_string(self, parser: MonkeyParser) -> None:
        """Test parsing empty string returns not included."""
        included, required_by_rpm = parser.parse_ex("")

        assert included is False
        assert required_by_rpm == []

    def test_parse_ex_whitespace_only(self, parser: MonkeyParser) -> None:
        """Test parsing whitespace-only string returns not included."""
        included, required_by_rpm = parser.parse_ex("   \n  \n  ")

        assert included is False
        assert required_by_rpm == []

    def test_parse_ex_spurious_decision(self, parser: MonkeyParser, fixtures_dir: Path) -> None:
        """Test parsing ex output with spurious decision (non-existent package)."""
        ex_output = (fixtures_dir / "ex_spurious.txt").read_text()
        included, required_by_rpm = parser.parse_ex(ex_output)

        # Spurious decision means not actually included
        assert included is False
        assert required_by_rpm == []

    def test_parse_buildinfo_multiple_packages(self, parser: MonkeyParser) -> None:
        """Test parsing multiple packages."""
        buildinfo = """Build test (2 rpms)
test-package-1 (TestEpic)
  version: 1.0.0
  architectures: x86_64
  summary: Test package 1
  required by:

test-package-2 (TestEpic)
  version: 1.0.0
  architectures: x86_64
  summary: Test package 2
  required by:
    - test-package-1 (TestEpic)
"""
        packages = parser.parse_buildinfo(buildinfo)
        assert len(packages) == 2
        assert packages[0].name == "test-package-1"
        assert packages[0].required_by == []
        assert packages[1].name == "test-package-2"
        assert packages[1].required_by == ["test-package-1"]

    def test_required_by_list_structure(self, parser: MonkeyParser) -> None:
        """Test that required_by is a simple list of package names."""
        buildinfo = """Build test (1 rpms)
test-package (TestEpic)
  version: 1.0.0
  architectures: x86_64
  summary: Test
  required by:
    - pkg1 (Epic1)
    - pkg2 (Epic2)
    - pkg3 (Epic3)
"""
        packages = parser.parse_buildinfo(buildinfo)
        req_by = packages[0].required_by

        assert len(req_by) == 3
        assert all(isinstance(item, str) for item in req_by)
        assert req_by == ["pkg1", "pkg2", "pkg3"]


class TestParseError:
    """Test suite for ParseError exception."""

    def test_inheritance(self) -> None:
        """Test that ParseError inherits from Exception."""
        assert issubclass(ParseError, Exception)

    def test_raise_and_catch(self) -> None:
        """Test raising and catching ParseError."""
        with pytest.raises(ParseError):
            raise ParseError("Test error")

    def test_error_message(self) -> None:
        """Test ParseError message."""
        error = ParseError("Custom parse error")
        assert str(error) == "Custom parse error"
