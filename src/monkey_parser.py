"""Parser for monkey command outputs."""

import re
from typing import Any, NamedTuple


class ParseError(Exception):
    """Raised when parsing fails."""

    pass


class BinaryPackage(NamedTuple):
    """Temporary structure for parse_buildinfo results."""

    name: str
    required_by: list[str]


class MonkeyParser:
    """Parser for monkey buildinfo and ex command outputs."""

    def parse_buildinfo(self, output: str) -> list[BinaryPackage]:
        """Parse monkey buildinfo output into BinaryPackage objects.

        Args:
            output: Raw output from 'monkey buildinfo' command.

        Returns:
            List of BinaryPackage objects. Returns empty list if package not found.

        Raises:
            ParseError: If the output format is invalid.
        """
        if not output.strip():
            return []

        lines = output.strip().split("\n")

        # Check for "not found" message (non-existent source package)
        if "not found" in lines[0]:
            return []

        # Validate header format
        if not lines[0].startswith("Build "):
            raise ParseError(
                f"Invalid buildinfo format: expected 'Build ...' header, got: {lines[0]}"
            )

        packages: list[BinaryPackage] = []
        current_package: dict[str, Any] | None = None
        in_required_by = False

        for line in lines[1:]:  # Skip header line
            # Package header: no indentation, format "package-name (Purpose)"
            if line and not line.startswith(" "):
                # Save previous package if exists
                if current_package:
                    packages.append(self._create_binary_package(current_package))

                # Parse new package header
                match = re.match(r"^(.+?)\s+\((.+?)\)$", line)
                if match:
                    current_package = {
                        "name": match.group(1),
                        "required_by": [],
                    }
                    in_required_by = False

            # Indented field lines
            elif line.startswith("  ") and current_package is not None:
                stripped = line.strip()

                if stripped == "required by:":
                    in_required_by = True

                elif stripped.startswith("-") and in_required_by:
                    # Parse "- package-name (Purpose)" - extract only package name
                    dep_match = re.match(r"^-\s+(.+?)\s+\((.+?)\)$", stripped)
                    if dep_match:
                        current_package["required_by"].append(dep_match.group(1))

        # Don't forget the last package
        if current_package:
            packages.append(self._create_binary_package(current_package))

        return packages

    def _create_binary_package(self, pkg_dict: dict[str, Any]) -> BinaryPackage:
        """Create BinaryPackage from parsed dictionary.

        Args:
            pkg_dict: Dictionary with package data.

        Returns:
            BinaryPackage object.

        Raises:
            ParseError: If required fields are missing.
        """
        if "name" not in pkg_dict:
            raise ParseError("Missing required field 'name' for package")

        return BinaryPackage(
            name=pkg_dict["name"],
            required_by=pkg_dict.get("required_by", []),
        )

    def parse_ex(self, output: str) -> tuple[bool, list[str]]:
        """Parse monkey ex output into simplified media inclusion data.

        Extracts:
        1. Whether package is included in any media (boolean)
        2. All RPMs that require this package across all media (list of strings)

        Args:
            output: Raw output from 'monkey ex' command.

        Returns:
            Tuple of (included: bool, required_by_rpm: list[str])
            - included: True if package appears in any media
            - required_by_rpm: List of all RPMs requiring this package (may be empty)
        """
        if not output.strip():
            return (False, [])

        lines = output.strip().split("\n")
        found_in_media = False
        required_by_rpm_set: set[str] = set()

        for line in lines:
            # Check for package inclusion (ignore spurious decisions)
            if "include" in line and "└─>" in line and "spurious decision" not in line:
                found_in_media = True

            # Extract required_by_rpm from "is required by rpm: package-name" line
            if "is required by rpm:" in line:
                match = re.search(r"is required by rpm:\s+(.+)", line)
                if match:
                    rpm_name = match.group(1).strip()
                    required_by_rpm_set.add(rpm_name)

        return (found_in_media, sorted(required_by_rpm_set))

    def _has_tree_chars(self, line: str) -> bool:
        """Check if line contains tree drawing characters."""
        return any(char in line for char in ["└─>", "├─>", "│"])

    def _strip_tree_chars(self, line: str) -> str:
        """Remove tree drawing characters from a line."""
        cleaned = line
        for char_seq in ["└─>", "├─>", "│"]:
            cleaned = cleaned.replace(char_seq, "")
        return cleaned
