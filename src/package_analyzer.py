"""Package analyzer orchestration."""

import json
import subprocess
from pathlib import Path

from src.models import BinaryPackageData, SourcePackageData
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

    def analyze_source_package(self, source_package: str) -> SourcePackageData:
        """Analyze a single source package.

        Args:
            source_package: Name of the source package to analyze.

        Returns:
            SourcePackageData containing binaries with merged buildinfo and ex data.
        """
        binaries: dict[str, BinaryPackageData] = {}

        # Get binary packages from buildinfo
        buildinfo_output = self._run_buildinfo(source_package)
        binary_packages = self.parser.parse_buildinfo(buildinfo_output)

        # For each binary package, merge buildinfo and ex data
        for binary_pkg in binary_packages:
            # Get media inclusion info
            ex_output = self._run_ex(binary_pkg.name)
            included, required_by_rpm = self.parser.parse_ex(ex_output)

            # Create merged BinaryPackageData
            binaries[binary_pkg.name] = BinaryPackageData(
                required_by=binary_pkg.required_by,
                included=included,
                required_by_rpm=required_by_rpm,
            )

        return SourcePackageData(
            source_name=source_package,
            binaries=binaries,
        )

    def analyze_packages(
        self, source_packages: list[str]
    ) -> dict[str, SourcePackageData]:
        """Analyze multiple source packages.

        Args:
            source_packages: List of source package names to analyze.

        Returns:
            Dictionary mapping source package names to SourcePackageData.
        """
        packages_data: dict[str, SourcePackageData] = {}

        for source_pkg in source_packages:
            source_data = self.analyze_source_package(source_pkg)
            packages_data[source_pkg] = source_data

        return packages_data

    def _write_results(
        self,
        packages_data: dict[str, SourcePackageData],
    ) -> None:
        """Write analysis results to single packages.json file.

        Args:
            packages_data: Dictionary of source package data.
        """
        output_path = self.output_dir / "packages.json"

        # Build JSON structure: {source_name: {binary_name: binary_data}}
        output_dict = {
            source_name: source_data.to_dict()
            for source_name, source_data in packages_data.items()
        }

        with open(output_path, "w") as f:
            json.dump(output_dict, f, indent=2)

    def analyze_and_write(self, source_packages: list[str]) -> None:
        """Analyze source packages and write results to JSON file.

        Args:
            source_packages: List of source package names to analyze.
        """
        packages_data = self.analyze_packages(source_packages)
        self._write_results(packages_data)
