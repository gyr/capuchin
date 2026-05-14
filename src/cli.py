"""Capuchin CLI main entry point."""

import argparse
import sys
from pathlib import Path


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments with subcommands.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="capuchin",
        description="Analyze source packages and query binary dependencies",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze source packages")
    analyze_parser.add_argument(
        "source_packages_file",
        help="Path to JSON file containing list of source package names",
    )
    analyze_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to write packages.json file (default: current directory)",
    )
    analyze_parser.add_argument(
        "--monkey-path",
        type=str,
        help="Path to monkey executable directory (overrides PACKAGE_MONKEY_PATH env var)",
    )
    analyze_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG level) logging",
    )
    analyze_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress progress bar and console output (logging to file still works)",
    )
    analyze_parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Write logs to specified file",
    )

    # Query subcommand
    query_parser = subparsers.add_parser("query", help="Query package information")
    query_parser.add_argument("package_name", help="Package name to query")
    query_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing packages.json file (default: current directory)",
    )
    query_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )

    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parsed_args = parse_args(args)

    # Route to appropriate command with lazy imports
    if parsed_args.command == "analyze":
        from src.commands.analyze import analyze_main

        return analyze_main(parsed_args)
    elif parsed_args.command == "query":
        from src.commands.query import query_main

        return query_main(parsed_args)
    else:
        # Should never reach here (argparse enforces required subcommand)
        print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
