"""CLI tool to query package information from analysis results."""

import argparse
import json
import sys
from pathlib import Path

from src.models import BinaryPackage, BinaryPackageInfo, InclusionReason, QueryResult


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Query package information from analysis results."
    )

    parser.add_argument(
        "source_package",
        help="Source package name to query",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.cwd(),
        help=(
            "Directory containing binary_packages.json and media_inclusion.json "
            "(default: current directory)"
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text",
    )

    return parser.parse_args(args)


def load_data(
    data_dir: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, list[dict[str, object]]]]]:
    """Load binary packages and media inclusion data from JSON files.

    Args:
        data_dir: Directory containing the JSON files.

    Returns:
        Tuple of (binary_packages_dict, media_inclusion_dict).

    Raises:
        FileNotFoundError: If required JSON files are missing.
        json.JSONDecodeError: If JSON files are invalid.
    """
    binary_file = data_dir / "binary_packages.json"
    media_file = data_dir / "media_inclusion.json"

    if not binary_file.exists():
        raise FileNotFoundError(f"binary_packages.json not found in {data_dir}")

    if not media_file.exists():
        raise FileNotFoundError(f"media_inclusion.json not found in {data_dir}")

    with open(binary_file) as f:
        binary_packages = json.load(f)

    with open(media_file) as f:
        media_inclusion = json.load(f)

    return binary_packages, media_inclusion


def query_source_package(
    source_package: str,
    binary_packages: dict[str, dict[str, object]],
    media_inclusion: dict[str, dict[str, list[dict[str, object]]]],
) -> QueryResult:
    """Query information about a source package.

    Args:
        source_package: Name of the source package to query.
        binary_packages: Dictionary of binary packages.
        media_inclusion: Dictionary of media inclusion information.

    Returns:
        QueryResult with package information.
    """
    # Find all binary packages that match the source package name prefix
    matching_binaries = []

    for pkg_name, pkg_data in binary_packages.items():
        # Match if package name starts with source package name
        # This handles cases like "bash" matching "bash", "bash-completion", etc.
        if pkg_name.startswith(source_package):
            # Type assertions for JSON data
            pkg_name_str = str(pkg_data["name"])
            required_by_list = pkg_data.get("required_by", [])
            assert isinstance(required_by_list, list)
            required_by_typed = [str(pkg) for pkg in required_by_list]

            binary_pkg = BinaryPackage(
                name=pkg_name_str,
                required_by=required_by_typed,
            )

            # Get media inclusion for this binary package
            media_inclusions: dict[str, list[InclusionReason]] = {}
            if pkg_name in media_inclusion:
                for media_name, reasons_data in media_inclusion[pkg_name].items():
                    reasons = []
                    for r in reasons_data:
                        # Type assertions for JSON data
                        reason_chain_data = r["reason_chain"]
                        assert isinstance(reason_chain_data, list)
                        reason_chain = [str(item) for item in reason_chain_data]

                        required_by_rpm_data = r.get("required_by_rpm")
                        required_by_rpm = (
                            str(required_by_rpm_data) if required_by_rpm_data else None
                        )

                        reasons.append(
                            InclusionReason(
                                reason_chain=reason_chain,
                                required_by_rpm=required_by_rpm,
                            )
                        )
                    media_inclusions[media_name] = reasons

            pkg_info = BinaryPackageInfo(
                binary_package=binary_pkg,
                required_by_packages=binary_pkg.required_by,
                media_inclusions=media_inclusions,
            )
            matching_binaries.append(pkg_info)

    return QueryResult(
        source_package=source_package,
        found=len(matching_binaries) > 0,
        binary_packages=matching_binaries,
    )


def format_text_output(result: QueryResult) -> str:
    """Format query result as human-readable text.

    Args:
        result: Query result to format.

    Returns:
        Formatted text output.
    """
    lines = []
    lines.append(f"Source package: {result.source_package}")

    if not result.found:
        lines.append("No binary packages found for this source package.")
        return "\n".join(lines)

    lines.append(f"Binary packages: {len(result.binary_packages)}")
    lines.append("")

    for idx, pkg_info in enumerate(result.binary_packages, 1):
        lines.append(f"{idx}. {pkg_info.binary_package.name}")

        # Required by
        if pkg_info.required_by_packages:
            lines.append(f"   Required by: {', '.join(pkg_info.required_by_packages)}")
        else:
            lines.append("   Required by: (none)")

        # Media inclusion
        if pkg_info.media_inclusions:
            lines.append("   Media inclusion:")
            for media_name, reasons in pkg_info.media_inclusions.items():
                lines.append(f"     {media_name}:")
                for reason in reasons:
                    if reason.required_by_rpm:
                        lines.append(f"       - Required by RPM: {reason.required_by_rpm}")
                    else:
                        lines.append("       - Included (no RPM dependency)")
        else:
            lines.append("   Media inclusion: Not in media")

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    """Main entry point for the query_package CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args()

    try:
        # Load data
        binary_packages, media_inclusion = load_data(args.data_dir)

        # Query source package
        result = query_source_package(
            args.source_package, binary_packages, media_inclusion
        )

        # Output results
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(format_text_output(result))

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
