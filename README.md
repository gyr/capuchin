# Capuchin

A Python tool to analyze source packages and query binary dependencies using the `monkey` CLI tool. This tool extracts information about binary packages, their reverse dependencies, and media inclusion details.

## Features

- **Binary Package Analysis**: Extract binary packages from source packages with reverse dependency tracking
- **Media Inclusion Tracking**: Determine which media includes each binary package and whether it's required by another package
- **Simplified Data Model**: Focus on essential information (package names, dependencies, media inclusion) - no metadata like versions, architectures, or epic classifications
- **Progress Tracking**: Real-time progress bar showing completion percentage and ETA
- **Comprehensive Logging**: Industry-standard logging with verbose/quiet modes and file output
- **Unified CLI**: Single entry point with `analyze` and `query` subcommands
- **JSON Output**: Structured JSON output for downstream processing

## Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- `monkey` CLI tool (package_monkey) - **must be pre-configured**
- `jq` (for JSON processing)

### Prerequisites Setup

#### 1. package_monkey (monkey CLI tool)

The `monkey` CLI tool must be installed and configured before using Capuchin.

**Installation**: Refer to the package_monkey documentation for installation instructions.

**Configuration**:  
Once installed, set the `PACKAGE_MONKEY_PATH` environment variable to point to your package_monkey directory (see Configuration section below).

**Verification**:
```bash
# Navigate to your package_monkey directory
cd /path/to/package_monkey

# Verify monkey command works
./monkey --help
```

#### 2. jq (JSON processor)

Required for JSON validation and processing.

**Installation**:
```bash
# On openSUSE/SUSE
zypper install jq

# On Ubuntu/Debian
apt-get install jq

# On macOS
brew install jq
```

**Verification**:
```bash
jq --version
```

## Installation

### For Development

1. Clone the repository:
```bash
git clone <repository-url>
cd capuchin
```

2. Install dependencies using uv:
```bash
uv sync
```

### For CLI Usage

To install the package and enable the `capuchin` CLI command:

```bash
uv pip install -e .
```

This creates an executable entry point in your environment. After installation, you can run:
- `capuchin analyze` instead of `python -m src.commands.analyze`
- `capuchin query` instead of `python -m src.commands.query`

## Configuration

### Environment Variables

**PACKAGE_MONKEY_PATH** (optional)
- Path to the package_monkey directory where the `monkey` CLI tool is located
- Default: `/home/user/work/repos/monkey/package_monkey`
- Override by:
  1. Creating a `.env` file: `PACKAGE_MONKEY_PATH=/your/custom/path`
  2. Exporting in shell: `export PACKAGE_MONKEY_PATH=/your/custom/path`
  3. Using `--monkey-path` flag: `capuchin analyze source.json --monkey-path /path`

**Example `.env` file:**
```bash
PACKAGE_MONKEY_PATH=/home/user/work/repos/monkey/package_monkey
```

**Note:** The `.env` file is gitignored for security. Use `.env.example` as a template.

## Usage

There are two ways to run the tools:

1. **Without installation** (for development/testing):
   ```bash
   python -m src.commands.analyze source_packages.json
   python -m src.commands.query <package_name>
   ```

2. **After installation** (`uv pip install -e .`):
   ```bash
   capuchin analyze source_packages.json
   capuchin query <package_name>
   ```

The following examples use the installed CLI command. If you haven't installed the package, use the `python -m` form shown above.

### 1. Analyze Source Packages

Run the analysis tool to process source packages from a JSON file:

```bash
capuchin analyze source_packages.json
```

**With options:**
```bash
# Specify custom output directory
capuchin analyze source_packages.json --output-dir ./output

# Override PACKAGE_MONKEY_PATH
capuchin analyze source_packages.json --monkey-path /custom/path/to/monkey

# Verbose logging (shows DEBUG level logs including exact commands)
capuchin analyze source_packages.json --verbose

# Quiet mode (no progress bar or console output)
capuchin analyze source_packages.json --quiet

# Write logs to file
capuchin analyze source_packages.json --log-file analysis.log

# Combined: verbose logs to file, quiet console, no progress bar
capuchin analyze source_packages.json --verbose --log-file debug.log --quiet
```

**What it does:**
- Reads source package names from the JSON file (must be a JSON array of strings)
- Executes `monkey buildinfo` and `monkey ex` commands for each package
- Shows progress bar with completion percentage (unless --quiet is used)
- Generates a single `packages.json` file in the output directory with all package data

**Example source_packages.json:**
```json
["aaa_base", "bash", "coreutils"]
```

### 2. Query Package Information

Query information about a package (source or binary):

```bash
capuchin query <package_name>
```

The query tool searches first as a source package, then as a binary package across all sources.

**Example - querying a source package:**
```bash
capuchin query bash
```

**Output:**
```
Source package: bash
Binary packages:
  - bash
      required_by: ['bash-completion', 'rpm']
      included: True
      required_by_rpm: ['filesystem']
  - bash-doc
      required_by: []
      included: False
      required_by_rpm: []
```

**Example - querying a binary package:**
```bash
capuchin query envsubst
```

**Output:**
```
Binary package: envsubst
Source package: gettext-runtime
  required_by: ['gettext-runtime']
  included: False
  required_by_rpm: []
```

**JSON output:**
```bash
capuchin query fwts --json | jq .
```

**With custom data directory:**
```bash
capuchin query bash --data-dir /path/to/output
```

### 3. Logging and Progress

The analyzer provides comprehensive logging and progress tracking:

#### Progress Bar

By default, a progress bar displays during analysis showing:
- Current package being analyzed
- Completion percentage
- Estimated time remaining

To disable the progress bar, use the `--quiet` flag.

#### Logging Levels

**Default (INFO):**
- Shows package analysis progress
- Binary package counts
- Timing information
- Formatted with colors for readability

**Verbose (DEBUG):**
```bash
capuchin analyze source_packages.json --verbose
```
- All INFO level logs
- Exact `monkey` commands before execution
- Detailed debugging information

**Quiet:**
```bash
capuchin analyze source_packages.json --quiet
```
- No console output (progress bar and logs suppressed)
- File logging still works if `--log-file` is specified
- Ideal for CI/CD pipelines or scripted usage

#### File Logging

Write logs to a file for later analysis:
```bash
capuchin analyze source_packages.json --log-file analysis.log
```

**File log features:**
- Always DEBUG level (regardless of console verbosity)
- Machine-readable format without colors
- Includes all commands executed and timing information

**Common patterns:**
```bash
# Quiet console, detailed file logs
capuchin analyze source_packages.json --quiet --log-file analysis.log

# Verbose console and file logs
capuchin analyze source_packages.json --verbose --log-file debug.log

# Debug to file only, no console clutter
capuchin analyze source_packages.json --verbose --quiet --log-file debug.log
```

## Output Format

The tool generates a single `packages.json` file with all package data organized by source package.

### packages.json

Hierarchical structure: source package → binary packages → package data

```json
{
  "bash": {
    "bash": {
      "required_by": ["bash-completion", "rpm"],
      "included": true,
      "required_by_rpm": ["filesystem"]
    },
    "bash-doc": {
      "required_by": [],
      "included": false,
      "required_by_rpm": []
    }
  },
  "gettext-runtime": {
    "gettext-runtime": {
      "required_by": ["gettext-tools", "grub2-common"],
      "included": true,
      "required_by_rpm": ["glibc", "systemd"]
    },
    "envsubst": {
      "required_by": ["gettext-runtime"],
      "included": false,
      "required_by_rpm": []
    }
  }
}
```

**Structure:**
- **Top level**: Source package names (keys match input source_packages.json)
- **Second level**: Binary package names produced by each source
- **Binary package fields:**
  - `required_by`: List of package names that depend on this binary (reverse dependencies)
  - `included`: Boolean indicating if package appears in any media
  - `required_by_rpm`: List of RPM packages requiring this binary in media (empty if not included or no requirements)

**Note:** Top-level keys match input source_packages.json exactly.

## Troubleshooting

### Command not found: capuchin

After installation, ensure your environment's bin directory is in PATH:
```bash
which capuchin
```

If not found, try:
```bash
uv pip install --force-reinstall -e .
```

### Command not found: monkey

Ensure that `PACKAGE_MONKEY_PATH` points to the correct directory containing the `monkey` CLI tool.

```bash
export PACKAGE_MONKEY_PATH=/path/to/package_monkey
```

### Permission denied

Ensure the `monkey` tool is executable:

```bash
chmod +x /path/to/package_monkey/monkey
```

### JSON validation errors

If you encounter JSON validation errors, ensure `jq` is installed:

```bash
# On openSUSE/SUSE
zypper install jq

# On Ubuntu/Debian
apt-get install jq
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[Add your license here]

## Authors

[Add author information here]
