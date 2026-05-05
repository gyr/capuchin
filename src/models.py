"""Data models for Package Analyzer."""

from dataclasses import asdict, dataclass


@dataclass
class BinaryPackageData:
    """Represents a binary package with all its data."""

    required_by: list[str]  # Packages that depend on this binary
    included: bool  # Whether package appears in any media
    required_by_rpm: list[str]  # RPMs that require this in media (can be multiple)

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SourcePackageData:
    """Groups binary packages from the same source package."""

    source_name: str
    binaries: dict[str, BinaryPackageData]  # {binary_name: BinaryPackageData}

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization.

        Returns only the binaries dict (without source_name key),
        since source_name will be the key in the final JSON output.
        """
        return {
            name: binary.to_dict()
            for name, binary in self.binaries.items()
        }
