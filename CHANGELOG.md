# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - BREAKING

**Major refactoring: Simplified output to single source-keyed JSON file**

- **Output format**: Two files (`binary_packages.json`, `media_inclusion.json`) merged into single `packages.json`
- **Structure**: Now keyed by source package (matches input), preserving source→binary relationship
- **Binary package data**: Simplified to three fields:
  - `required_by`: list of package dependencies (from buildinfo)
  - `included`: boolean for media inclusion (from ex)
  - `required_by_rpm`: list of RPMs requiring this package (from ex, deduplicated across media)
- **Query tool**: Now searches both source and binary packages intelligently
  - First tries as source package → shows all its binaries
  - Then searches all sources for binary package → shows that binary + its source
- **Data models**: Removed complex models (`InclusionReason`, `MediaInclusion`, etc.), replaced with two simple models (`BinaryPackageData`, `SourcePackageData`)
- **Parser**: `parse_ex()` now returns `(bool, list[str])` instead of complex dict structure

### Fixed
- Use system-installed `monkey` command instead of path-based executable
- Simplified media inclusion parsing (40 lines removed)
- Read `monkey ex` output from stderr instead of stdout

### Added
- **Progress bar**: Real-time progress tracking with completion percentage and ETA during analysis
- **Industry-standard logging**: Comprehensive logging using Python's logging module with rich formatting
  - `--verbose/-v`: Enable DEBUG level logging showing exact commands
  - `--quiet/-q`: Suppress progress bar and console output (for CI/CD)
  - `--log-file PATH`: Write detailed logs to file (always DEBUG level)
  - Colored console output with RichHandler for better readability
  - Module-level loggers throughout codebase
  - Timing information for analysis operations
- Initial project setup with Python 3.12 and uv
- Configuration module with environment variable support (PACKAGE_MONKEY_PATH)
- Monkey output parser for buildinfo and ex commands
- Package analyzer for extracting binary packages and dependencies
- Media inclusion tracker to determine package inclusion in products
- Query tool for interactive package exploration
- JSON output format for binary packages and media inclusion
- Comprehensive test suite with >90% coverage
- GitHub Actions CI pipeline
- Complete documentation (README, CONTRIBUTING, architecture docs)

### Features
- Parse `monkey buildinfo` output to extract binary packages and reverse dependencies
- Parse `monkey ex` output to extract media inclusion chains
- Support for multiple inclusion paths (direct and rpm-based)
- JSON validation and sorting
- Unified CLI tool: `capuchin analyze` and `capuchin query`

## [0.1.0] - TBD

Initial release.
