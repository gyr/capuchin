"""Tests for data models."""

from src.models import BinaryPackageData, SourcePackageData


class TestBinaryPackageData:
    """Tests for BinaryPackageData model."""

    def test_creation_not_included(self) -> None:
        """Test creating BinaryPackageData for package not in media."""
        pkg = BinaryPackageData(
            required_by=["qa_test_fwts", "validation-tools"],
            included=False,
            required_by_rpm=[],
        )
        assert pkg.required_by == ["qa_test_fwts", "validation-tools"]
        assert pkg.included is False
        assert pkg.required_by_rpm == []

    def test_creation_included_single_rpm(self) -> None:
        """Test creating BinaryPackageData for package included in media with single rpm."""
        pkg = BinaryPackageData(
            required_by=["other-pkg"],
            included=True,
            required_by_rpm=["filesystem"],
        )
        assert pkg.required_by == ["other-pkg"]
        assert pkg.included is True
        assert pkg.required_by_rpm == ["filesystem"]

    def test_creation_included_multiple_rpm(self) -> None:
        """Test creating BinaryPackageData for package in multiple media."""
        pkg = BinaryPackageData(
            required_by=[],
            included=True,
            required_by_rpm=["filesystem", "systemd"],
        )
        assert pkg.required_by == []
        assert pkg.included is True
        assert len(pkg.required_by_rpm) == 2
        assert "filesystem" in pkg.required_by_rpm
        assert "systemd" in pkg.required_by_rpm

    def test_to_dict(self) -> None:
        """Test converting BinaryPackageData to dictionary."""
        pkg = BinaryPackageData(
            required_by=["pkg-a", "pkg-b"],
            included=True,
            required_by_rpm=["filesystem"],
        )
        result = pkg.to_dict()
        assert result["required_by"] == ["pkg-a", "pkg-b"]
        assert result["included"] is True
        assert result["required_by_rpm"] == ["filesystem"]


class TestSourcePackageData:
    """Tests for SourcePackageData model."""

    def test_creation_single_binary(self) -> None:
        """Test creating SourcePackageData with single binary package."""
        binary = BinaryPackageData(
            required_by=["other-pkg"],
            included=False,
            required_by_rpm=[],
        )
        source = SourcePackageData(
            source_name="bash",
            binaries={"bash": binary},
        )
        assert source.source_name == "bash"
        assert len(source.binaries) == 1
        assert "bash" in source.binaries
        assert source.binaries["bash"].required_by == ["other-pkg"]

    def test_creation_multiple_binaries(self) -> None:
        """Test creating SourcePackageData with multiple binary packages."""
        bash = BinaryPackageData(
            required_by=["bash-completion"],
            included=True,
            required_by_rpm=["filesystem"],
        )
        bash_doc = BinaryPackageData(
            required_by=[],
            included=False,
            required_by_rpm=[],
        )
        source = SourcePackageData(
            source_name="bash",
            binaries={"bash": bash, "bash-doc": bash_doc},
        )
        assert source.source_name == "bash"
        assert len(source.binaries) == 2
        assert "bash" in source.binaries
        assert "bash-doc" in source.binaries
        assert source.binaries["bash"].included is True
        assert source.binaries["bash-doc"].included is False

    def test_to_dict(self) -> None:
        """Test converting SourcePackageData to dictionary."""
        bash = BinaryPackageData(
            required_by=["rpm"],
            included=True,
            required_by_rpm=["filesystem"],
        )
        bash_doc = BinaryPackageData(
            required_by=[],
            included=False,
            required_by_rpm=[],
        )
        source = SourcePackageData(
            source_name="bash",
            binaries={"bash": bash, "bash-doc": bash_doc},
        )
        result = source.to_dict()
        assert "bash" in result
        assert "bash-doc" in result
        assert result["bash"]["required_by"] == ["rpm"]
        assert result["bash"]["included"] is True
        assert result["bash"]["required_by_rpm"] == ["filesystem"]
        assert result["bash-doc"]["required_by"] == []
        assert result["bash-doc"]["included"] is False
        assert result["bash-doc"]["required_by_rpm"] == []
