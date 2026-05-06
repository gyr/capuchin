"""CLI tool to query package information from analysis results."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Module-level logger
logger = logging.getLogger(__name__)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Query package information from packages.json."
    )

    parser.add_argument(
        "package_name",
        help="Package name to query (source or binary package)",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing packages.json (default: current directory)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text",
    )

    return parser.parse_args(args)


def load_packages(data_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Load packages data from packages.json.

    Args:
        data_dir: Directory containing packages.json.

    Returns:
        Dictionary mapping source packages to their binaries.

    Raises:
        FileNotFoundError: If packages.json is missing.
    """
    packages_file = data_dir / "packages.json"

    if not packages_file.exists():
        raise FileNotFoundError(f"packages.json not found in {data_dir}")

    with open(packages_file) as f:
        return json.load(f)


def query_package(
    package_name: str, packages_data: dict[str, dict[str, dict[str, Any]]]
) -> dict[str, Any]:  # Result varies by query type
    """Query for a package by name.

    Searches first as a source package, then as a binary package across all sources.

    Args:
        package_name: Name of package to find.
        packages_data: Loaded packages data.

    Returns:
        Dictionary with query result:
        - type: "source" | "binary" | "not_found"
        - Additional fields depending on type
    """
    # Try to find as source package first
    if package_name in packages_data:
        return {
            "type": "source",
            "source_package": package_name,
            "binaries": packages_data[package_name],
        }

    # Search across all sources for binary package
    for source_name, binaries in packages_data.items():
        if package_name in binaries:
            return {
                "type": "binary",
                "binary_package": package_name,
                "source_package": source_name,
                "data": binaries[package_name],
            }

    # Not found
    return {
        "type": "not_found",
        "package_name": package_name,
    }


def format_human_readable(query_result: dict[str, Any]) -> str:
    """Format query result as human-readable text.

    Args:
        query_result: Result from query_package().

    Returns:
        Formatted string.
    """
    result_type = query_result["type"]

    if result_type == "source":
        lines = [f"Source package: {query_result['source_package']}"]
        lines.append("Binary packages:")
        binaries = query_result["binaries"]
        for binary_name, binary_data in binaries.items():  # type: ignore
            lines.append(f"  - {binary_name}")
            lines.append(f"      required_by: {binary_data['required_by']}")  # type: ignore
            lines.append(f"      included: {binary_data['included']}")  # type: ignore
            lines.append(f"      required_by_rpm: {binary_data['required_by_rpm']}")  # type: ignore
        return "\n".join(lines)

    elif result_type == "binary":
        lines = [f"Binary package: {query_result['binary_package']}"]
        lines.append(f"Source package: {query_result['source_package']}")
        data = query_result["data"]
        lines.append(f"  required_by: {data['required_by']}")  # type: ignore
        lines.append(f"  included: {data['included']}")  # type: ignore
        lines.append(f"  required_by_rpm: {data['required_by_rpm']}")  # type: ignore
        return "\n".join(lines)

    else:  # not_found
        return f"Package not found: {query_result['package_name']}"


def main() -> int:
    """Main entry point for the query_package CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Setup basic logging (INFO level, no file handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    args = parse_args()

    try:
        # Load packages data
        packages_data = load_packages(args.data_dir)

        # Query for the package
        result = query_package(args.package_name, packages_data)

        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_human_readable(result))

        # Exit with success unless package not found
        return 0 if result["type"] != "not_found" else 1

    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except json.JSONDecodeError as e:
        logger.error("Failed to parse packages.json: %s", e)
        return 1
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
