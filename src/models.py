"""Data models for Package Analyzer."""

from dataclasses import asdict, dataclass


@dataclass
class BinaryPackage:
    """Represents a binary package."""

    name: str
    required_by: list[str]  # List of package names that require this package

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SourcePackage:
    """Groups binary packages from the same source."""

    name: str
    binary_packages: list[BinaryPackage]

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return {"binary_packages": [pkg.to_dict() for pkg in self.binary_packages]}


@dataclass
class InclusionReason:
    """Represents one inclusion path in media."""

    reason_chain: list[str]  # Chain of reasons (tree path)
    required_by_rpm: str | None  # If included due to rpm dependency

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class MediaInclusion:
    """Maps media to inclusion reasons for a binary package."""

    binary_package: str
    included_in: dict[str, list[InclusionReason]]  # {media_name: [reasons...]}

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return {
            media: [reason.to_dict() for reason in reasons]
            for media, reasons in self.included_in.items()
        }


@dataclass
class BinaryPackageInfo:
    """Extended info for query results."""

    binary_package: BinaryPackage
    required_by_packages: list[str]
    media_inclusions: dict[str, list[InclusionReason]]

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return {
            "binary_package": self.binary_package.to_dict(),
            "required_by_packages": self.required_by_packages,
            "media_inclusions": {
                media: [reason.to_dict() for reason in reasons]
                for media, reasons in self.media_inclusions.items()
            },
        }


@dataclass
class QueryResult:
    """Result of querying a source package."""

    source_package: str
    found: bool
    binary_packages: list[BinaryPackageInfo]

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_package": self.source_package,
            "found": self.found,
            "binary_packages": [pkg.to_dict() for pkg in self.binary_packages],
        }
