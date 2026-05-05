"""Tests for data models."""

from src.models import (
    BinaryPackage,
    BinaryPackageInfo,
    InclusionReason,
    MediaInclusion,
    QueryResult,
    SourcePackage,
)


class TestBinaryPackage:
    """Tests for BinaryPackage model."""

    def test_creation(self) -> None:
        """Test creating a BinaryPackage."""
        pkg = BinaryPackage(
            name="fwts",
            required_by=["qa_test_fwts", "validation-tools"],
        )
        assert pkg.name == "fwts"
        assert len(pkg.required_by) == 2
        assert pkg.required_by == ["qa_test_fwts", "validation-tools"]

    def test_to_dict(self) -> None:
        """Test converting BinaryPackage to dictionary."""
        pkg = BinaryPackage(
            name="test-pkg",
            required_by=["other-pkg"],
        )
        result = pkg.to_dict()
        assert result["name"] == "test-pkg"
        assert len(result["required_by"]) == 1
        assert result["required_by"][0] == "other-pkg"


class TestSourcePackage:
    """Tests for SourcePackage model."""

    def test_creation(self) -> None:
        """Test creating a SourcePackage."""
        binary = BinaryPackage(name="test", required_by=[])
        source = SourcePackage(name="test-source", binary_packages=[binary])
        assert source.name == "test-source"
        assert len(source.binary_packages) == 1
        assert source.binary_packages[0].name == "test"

    def test_to_dict(self) -> None:
        """Test converting SourcePackage to dictionary."""
        binary = BinaryPackage(name="test", required_by=["other-pkg"])
        source = SourcePackage(name="test-source", binary_packages=[binary])
        result = source.to_dict()
        assert "binary_packages" in result
        assert len(result["binary_packages"]) == 1
        assert result["binary_packages"][0]["name"] == "test"
        assert result["binary_packages"][0]["required_by"] == ["other-pkg"]


class TestInclusionReason:
    """Tests for InclusionReason model."""

    def test_creation_without_rpm(self) -> None:
        """Test creating InclusionReason without required_by_rpm."""
        reason = InclusionReason(
            reason_chain=["fwts include"],
            required_by_rpm=None,
        )
        assert reason.reason_chain == ["fwts include"]
        assert reason.required_by_rpm is None

    def test_creation_with_rpm(self) -> None:
        """Test creating InclusionReason with required_by_rpm."""
        reason = InclusionReason(
            reason_chain=["libopenjph0_25 include"],
            required_by_rpm="libMagickWand-7_Q16HDRI10",
        )
        assert reason.required_by_rpm == "libMagickWand-7_Q16HDRI10"

    def test_to_dict(self) -> None:
        """Test converting InclusionReason to dictionary."""
        reason = InclusionReason(
            reason_chain=["fwts include"],
            required_by_rpm="qa_test_fwts",
        )
        result = reason.to_dict()
        assert result["reason_chain"] == ["fwts include"]
        assert result["required_by_rpm"] == "qa_test_fwts"


class TestMediaInclusion:
    """Tests for MediaInclusion model."""

    def test_creation(self) -> None:
        """Test creating MediaInclusion."""
        reason = InclusionReason(reason_chain=["fwts include"], required_by_rpm=None)
        inclusion = MediaInclusion(binary_package="fwts", included_in={"sles_16.1": [reason]})
        assert inclusion.binary_package == "fwts"
        assert "sles_16.1" in inclusion.included_in
        assert len(inclusion.included_in["sles_16.1"]) == 1

    def test_to_dict(self) -> None:
        """Test converting MediaInclusion to dictionary."""
        reason = InclusionReason(reason_chain=["fwts include"], required_by_rpm=None)
        inclusion = MediaInclusion(binary_package="fwts", included_in={"sles_16.1": [reason]})
        result = inclusion.to_dict()
        assert "sles_16.1" in result
        assert len(result["sles_16.1"]) == 1
        assert result["sles_16.1"][0]["reason_chain"] == ["fwts include"]


class TestBinaryPackageInfo:
    """Tests for BinaryPackageInfo model."""

    def test_creation(self) -> None:
        """Test creating BinaryPackageInfo."""
        pkg = BinaryPackage(name="fwts", required_by=["qa_test_fwts"])
        reason = InclusionReason(reason_chain=["fwts include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=pkg,
            required_by_packages=["qa_test_fwts"],
            media_inclusions={"sles_16.1": [reason]},
        )
        assert info.binary_package.name == "fwts"
        assert len(info.required_by_packages) == 1
        assert "sles_16.1" in info.media_inclusions

    def test_to_dict(self) -> None:
        """Test converting BinaryPackageInfo to dictionary."""
        pkg = BinaryPackage(name="fwts", required_by=["qa_test_fwts"])
        reason = InclusionReason(reason_chain=["fwts include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=pkg,
            required_by_packages=["qa_test_fwts"],
            media_inclusions={"sles_16.1": [reason]},
        )
        result = info.to_dict()
        assert result["binary_package"]["name"] == "fwts"
        assert result["binary_package"]["required_by"] == ["qa_test_fwts"]
        assert result["required_by_packages"] == ["qa_test_fwts"]
        assert len(result["media_inclusions"]) == 1
        assert "sles_16.1" in result["media_inclusions"]


class TestQueryResult:
    """Tests for QueryResult model."""

    def test_creation_found(self) -> None:
        """Test creating QueryResult for found package."""
        pkg = BinaryPackage(name="fwts", required_by=["qa_test_fwts"])
        reason = InclusionReason(reason_chain=["fwts include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=pkg,
            required_by_packages=["qa_test_fwts"],
            media_inclusions={"sles_16.1": [reason]},
        )
        result = QueryResult(source_package="test-source", found=True, binary_packages=[info])
        assert result.source_package == "test-source"
        assert result.found is True
        assert len(result.binary_packages) == 1

    def test_creation_not_found(self) -> None:
        """Test creating QueryResult for not found package."""
        result = QueryResult(source_package="nonexistent", found=False, binary_packages=[])
        assert result.source_package == "nonexistent"
        assert result.found is False
        assert result.binary_packages == []

    def test_to_dict(self) -> None:
        """Test converting QueryResult to dictionary."""
        pkg = BinaryPackage(name="fwts", required_by=["qa_test_fwts"])
        reason = InclusionReason(reason_chain=["fwts include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=pkg,
            required_by_packages=["qa_test_fwts"],
            media_inclusions={"sles_16.1": [reason]},
        )
        query_result = QueryResult(source_package="test-source", found=True, binary_packages=[info])
        result = query_result.to_dict()
        assert result["source_package"] == "test-source"
        assert result["found"] is True
        assert len(result["binary_packages"]) == 1
