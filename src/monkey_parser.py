"""Parser for monkey command outputs."""

import re
from typing import Any

from src.models import BinaryPackage, InclusionReason


class ParseError(Exception):
    """Raised when parsing fails."""

    pass


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

    def parse_ex(self, output: str) -> dict[str, list[InclusionReason]]:
        """Parse monkey ex output into media inclusion dictionary.

        Extracts two key pieces of information:
        1. Which media the package is included in
        2. If included, which package requires it (from "is required by rpm:" line)

        Args:
            output: Raw output from 'monkey ex' command.

        Returns:
            Dictionary mapping media names to lists of InclusionReason objects.
            Each media has one InclusionReason with the package name and
            optional required_by_rpm.
        """
        if not output.strip():
            return {}

        media_dict: dict[str, list[InclusionReason]] = {}
        lines = output.strip().split("\n")

        current_media: str | None = None
        package_name: str | None = None
        required_by_rpm: str | None = None

        for line in lines:
            # Media header (ends with colon, no tree chars)
            if line.endswith(":") and not self._has_tree_chars(line):
                # Save previous media if exists
                if current_media and package_name:
                    media_dict[current_media] = [
                        InclusionReason(
                            reason_chain=[package_name],
                            required_by_rpm=required_by_rpm,
                        )
                    ]

                # Start new media
                current_media = line.rstrip(":")
                package_name = None
                required_by_rpm = None
                continue

            # Extract package name from "└─> package-name include" line
            # Ignore "spurious decision" (non-existent binary package)
            if "include" in line and "└─>" in line and "spurious decision" not in line:
                content = self._strip_tree_chars(line).strip()
                if content:
                    package_name = content

            # Extract required_by_rpm from "is required by rpm: package-name" line
            if "is required by rpm:" in line:
                match = re.search(r"is required by rpm:\s+(.+)", line)
                if match:
                    required_by_rpm = match.group(1).strip()

        # Don't forget the last media
        if current_media and package_name:
            media_dict[current_media] = [
                InclusionReason(
                    reason_chain=[package_name],
                    required_by_rpm=required_by_rpm,
                )
            ]

        return media_dict

    def _has_tree_chars(self, line: str) -> bool:
        """Check if line contains tree drawing characters."""
        return any(char in line for char in ["└─>", "├─>", "│"])

    def _strip_tree_chars(self, line: str) -> str:
        """Remove tree drawing characters from a line."""
        cleaned = line
        for char_seq in ["└─>", "├─>", "│"]:
            cleaned = cleaned.replace(char_seq, "")
        return cleaned
