# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- CLI tools: `analyze-packages` and `query-package`

## [0.1.0] - TBD

Initial release.
