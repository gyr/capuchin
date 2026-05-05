"""Tests for data models."""

import pytest

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
            purpose="KernelPlus-default",
            version="25.03.00",
            architectures=["x86_64", "aarch64"],
            summary="Firmware Test Suite",
            required_by=[],
        )
        assert pkg.name == "fwts"
        assert pkg.purpose == "KernelPlus-default"
        assert pkg.version == "25.03.00"
        assert pkg.architectures == ["x86_64", "aarch64"]
        assert pkg.summary == "Firmware Test Suite"
        assert pkg.required_by == []

    def test_to_dict(self) -> None:
        """Test converting BinaryPackage to dictionary."""
        pkg = BinaryPackage(
            name="test-pkg",
            purpose="Test-default",
            version="1.0.0",
            architectures=["x86_64"],
            summary="Test package",
            required_by=[{"package": "other-pkg", "purpose": "Other-default"}],
        )
        result = pkg.to_dict()
        assert result["name"] == "test-pkg"
        assert result["purpose"] == "Test-default"
        assert result["version"] == "1.0.0"
        assert result["architectures"] == ["x86_64"]
        assert result["summary"] == "Test package"
        assert len(result["required_by"]) == 1
        assert result["required_by"][0]["package"] == "other-pkg"


class TestSourcePackage:
    """Tests for SourcePackage model."""

    def test_creation(self) -> None:
        """Test creating a SourcePackage."""
        binary = BinaryPackage(
            name="test",
            purpose="Test-default",
            version="1.0",
            architectures=["x86_64"],
            summary="Test",
            required_by=[],
        )
        source = SourcePackage(name="test-source", binary_packages=[binary])
        assert source.name == "test-source"
        assert len(source.binary_packages) == 1
        assert source.binary_packages[0].name == "test"

    def test_to_dict(self) -> None:
        """Test converting SourcePackage to dictionary."""
        binary = BinaryPackage(
            name="test",
            purpose="Test-default",
            version="1.0",
            architectures=["x86_64"],
            summary="Test",
            required_by=[],
        )
        source = SourcePackage(name="test-source", binary_packages=[binary])
        result = source.to_dict()
        assert "binary_packages" in result
        assert len(result["binary_packages"]) == 1
        assert result["binary_packages"][0]["name"] == "test"


class TestInclusionReason:
    """Tests for InclusionReason model."""

    def test_creation_without_rpm(self) -> None:
        """Test creating InclusionReason without rpm dependency."""
        reason = InclusionReason(
            reason_chain=["include", "propagated from epic: KernelPlus"],
            required_by_rpm=None,
        )
        assert len(reason.reason_chain) == 2
        assert reason.required_by_rpm is None

    def test_creation_with_rpm(self) -> None:
        """Test creating InclusionReason with rpm dependency."""
        reason = InclusionReason(
            reason_chain=["include", "is required by rpm: libMagickWand"],
            required_by_rpm="libMagickWand",
        )
        assert len(reason.reason_chain) == 2
        assert reason.required_by_rpm == "libMagickWand"

    def test_to_dict(self) -> None:
        """Test converting InclusionReason to dictionary."""
        reason = InclusionReason(
            reason_chain=["include", "propagated from epic: Test"],
            required_by_rpm="test-rpm",
        )
        result = reason.to_dict()
        assert result["reason_chain"] == ["include", "propagated from epic: Test"]
        assert result["required_by_rpm"] == "test-rpm"


class TestMediaInclusion:
    """Tests for MediaInclusion model."""

    def test_creation(self) -> None:
        """Test creating MediaInclusion."""
        reason = InclusionReason(reason_chain=["include"], required_by_rpm=None)
        inclusion = MediaInclusion(
            binary_package="fwts", included_in={"sles_16.1": [reason]}
        )
        assert inclusion.binary_package == "fwts"
        assert "sles_16.1" in inclusion.included_in
        assert len(inclusion.included_in["sles_16.1"]) == 1

    def test_to_dict(self) -> None:
        """Test converting MediaInclusion to dictionary."""
        reason1 = InclusionReason(reason_chain=["include"], required_by_rpm=None)
        reason2 = InclusionReason(
            reason_chain=["include", "is required by rpm: other"],
            required_by_rpm="other",
        )
        inclusion = MediaInclusion(
            binary_package="test-pkg",
            included_in={"sles_16.1": [reason1], "sleha_16.1": [reason2]},
        )
        result = inclusion.to_dict()
        assert "sles_16.1" in result
        assert "sleha_16.1" in result
        assert len(result["sles_16.1"]) == 1
        assert len(result["sleha_16.1"]) == 1
        assert result["sleha_16.1"][0]["required_by_rpm"] == "other"


class TestBinaryPackageInfo:
    """Tests for BinaryPackageInfo model."""

    def test_creation(self) -> None:
        """Test creating BinaryPackageInfo."""
        binary = BinaryPackage(
            name="test",
            purpose="Test-default",
            version="1.0",
            architectures=["x86_64"],
            summary="Test",
            required_by=[],
        )
        reason = InclusionReason(reason_chain=["include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=binary,
            required_by_packages=["pkg1", "pkg2"],
            media_inclusions={"sles_16.1": [reason]},
        )
        assert info.binary_package.name == "test"
        assert len(info.required_by_packages) == 2
        assert "sles_16.1" in info.media_inclusions

    def test_to_dict(self) -> None:
        """Test converting BinaryPackageInfo to dictionary."""
        binary = BinaryPackage(
            name="test",
            purpose="Test-default",
            version="1.0",
            architectures=["x86_64"],
            summary="Test",
            required_by=[],
        )
        reason = InclusionReason(reason_chain=["include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=binary,
            required_by_packages=["pkg1"],
            media_inclusions={"sles_16.1": [reason]},
        )
        result = info.to_dict()
        assert "binary_package" in result
        assert "required_by_packages" in result
        assert "media_inclusions" in result
        assert result["binary_package"]["name"] == "test"
        assert result["required_by_packages"] == ["pkg1"]


class TestQueryResult:
    """Tests for QueryResult model."""

    def test_creation_found(self) -> None:
        """Test creating QueryResult for found package."""
        binary = BinaryPackage(
            name="test",
            purpose="Test-default",
            version="1.0",
            architectures=["x86_64"],
            summary="Test",
            required_by=[],
        )
        reason = InclusionReason(reason_chain=["include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=binary,
            required_by_packages=[],
            media_inclusions={"sles_16.1": [reason]},
        )
        result = QueryResult(
            source_package="test-source", found=True, binary_packages=[info]
        )
        assert result.source_package == "test-source"
        assert result.found is True
        assert len(result.binary_packages) == 1

    def test_creation_not_found(self) -> None:
        """Test creating QueryResult for not found package."""
        result = QueryResult(
            source_package="nonexistent", found=False, binary_packages=[]
        )
        assert result.source_package == "nonexistent"
        assert result.found is False
        assert result.binary_packages == []

    def test_to_dict(self) -> None:
        """Test converting QueryResult to dictionary."""
        binary = BinaryPackage(
            name="test",
            purpose="Test-default",
            version="1.0",
            architectures=["x86_64"],
            summary="Test",
            required_by=[],
        )
        reason = InclusionReason(reason_chain=["include"], required_by_rpm=None)
        info = BinaryPackageInfo(
            binary_package=binary,
            required_by_packages=[],
            media_inclusions={"sles_16.1": [reason]},
        )
        query_result = QueryResult(
            source_package="test-source", found=True, binary_packages=[info]
        )
        result = query_result.to_dict()
        assert result["source_package"] == "test-source"
        assert result["found"] is True
        assert len(result["binary_packages"]) == 1
