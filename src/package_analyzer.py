"""Package analyzer orchestration."""

import json
import subprocess
from pathlib import Path

from src.models import BinaryPackage, MediaInclusion
from src.monkey_parser import MonkeyParser


class PackageAnalyzer:
    """Orchestrates package analysis workflow."""

    def __init__(
        self, monkey_path: str, output_dir: Path | None = None
    ) -> None:
        """Initialize PackageAnalyzer.

        Args:
            monkey_path: Path to the monkey executable directory.
            output_dir: Directory for output JSON files. Defaults to current directory.
        """
        self.monkey_path = monkey_path
        self.output_dir = output_dir if output_dir is not None else Path.cwd()
        self.parser = MonkeyParser()

    def _run_buildinfo(self, source_package: str) -> str:
        """Execute monkey buildinfo command.

        Args:
            source_package: Name of the source package.

        Returns:
            Raw command output.

        Raises:
            RuntimeError: If command execution fails.
        """
        cmd = ["monkey", "buildinfo", source_package]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.monkey_path,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to run monkey buildinfo for {source_package}: {e}"
            ) from e

    def _run_ex(self, binary_package: str) -> str:
        """Execute monkey ex command.

        Args:
            binary_package: Name of the binary package.

        Returns:
            Raw command output.

        Raises:
            RuntimeError: If command execution fails.
        """
        cmd = ["monkey", "ex", binary_package]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.monkey_path,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to run monkey ex for {binary_package}: {e}"
            ) from e

    def analyze_source_package(
        self, source_package: str
    ) -> tuple[dict[str, BinaryPackage], dict[str, MediaInclusion]]:
        """Analyze a single source package.

        Args:
            source_package: Name of the source package to analyze.

        Returns:
            Tuple of (binary_packages_dict, media_inclusions_dict).
        """
        binary_pkgs: dict[str, BinaryPackage] = {}
        media_inclusions: dict[str, MediaInclusion] = {}

        # Get binary packages from buildinfo
        buildinfo_output = self._run_buildinfo(source_package)
        binary_packages = self.parser.parse_buildinfo(buildinfo_output)

        # For each binary package, get media inclusion info
        for binary_pkg in binary_packages:
            binary_pkgs[binary_pkg.name] = binary_pkg

            # Get media inclusion
            ex_output = self._run_ex(binary_pkg.name)
            inclusion_dict = self.parser.parse_ex(ex_output)

            # Only add media inclusion if package is actually included
            if inclusion_dict:
                media_inclusions[binary_pkg.name] = MediaInclusion(
                    binary_package=binary_pkg.name,
                    included_in=inclusion_dict,
                )

        return binary_pkgs, media_inclusions

    def analyze_packages(
        self, source_packages: list[str]
    ) -> tuple[dict[str, BinaryPackage], dict[str, MediaInclusion]]:
        """Analyze multiple source packages.

        Args:
            source_packages: List of source package names to analyze.

        Returns:
            Tuple of (binary_packages_dict, media_inclusions_dict).
        """
        all_binary_pkgs: dict[str, BinaryPackage] = {}
        all_media_inclusions: dict[str, MediaInclusion] = {}

        for source_pkg in source_packages:
            binary_pkgs, media_inclusions = self.analyze_source_package(
                source_pkg
            )
            all_binary_pkgs.update(binary_pkgs)
            all_media_inclusions.update(media_inclusions)

        return all_binary_pkgs, all_media_inclusions

    def _write_results(
        self,
        binary_pkgs: dict[str, BinaryPackage],
        media_inclusions: dict[str, MediaInclusion],
    ) -> None:
        """Write analysis results to JSON files.

        Args:
            binary_pkgs: Dictionary of binary packages.
            media_inclusions: Dictionary of media inclusions.
        """
        # Write binary_packages.json
        binary_json_path = self.output_dir / "binary_packages.json"
        with open(binary_json_path, "w") as f:
            binary_data = {name: pkg.to_dict() for name, pkg in binary_pkgs.items()}
            json.dump(binary_data, f, indent=2)

        # Write media_inclusion.json
        media_json_path = self.output_dir / "media_inclusion.json"
        with open(media_json_path, "w") as f:
            media_data = {
                name: inclusion.to_dict()
                for name, inclusion in media_inclusions.items()
            }
            json.dump(media_data, f, indent=2)

    def analyze_and_write(self, source_packages: list[str]) -> None:
        """Analyze source packages and write results to JSON files.

        Args:
            source_packages: List of source package names to analyze.
        """
        binary_pkgs, media_inclusions = self.analyze_packages(source_packages)
        self._write_results(binary_pkgs, media_inclusions)
