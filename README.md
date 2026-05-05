# Package Analyzer

A Python tool to analyze source packages and their binary dependencies using the `monkey` CLI tool. This tool extracts information about binary packages, their reverse dependencies, and media inclusion details.

## Features

- **Binary Package Analysis**: Extract binary packages from source packages with reverse dependency tracking
- **Media Inclusion Tracking**: Determine which media includes each binary package and whether it's required by another package
- **Simplified Data Model**: Focus on essential information (package names, dependencies, media inclusion) - no metadata like versions, architectures, or epic classifications
- **Query Tool**: Interactive query interface to explore package information
- **JSON Output**: Structured JSON output for downstream processing

## Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- `monkey` CLI tool (package_monkey) - **must be pre-configured**
- `jq` (for JSON validation)

### Prerequisites Setup

#### 1. package_monkey (monkey CLI tool)

The `monkey` CLI tool must be installed and configured before using this analyzer.

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

Required for JSON validation and sorting.

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
cd package-analyzer
```

2. Install dependencies using uv:
```bash
uv sync
```

### For CLI Usage

To install the package and enable CLI commands (`analyze-packages`, `query-package`):

```bash
uv pip install -e .
```

This creates executable entry points in your environment. After installation, you can run:
- `analyze-packages` instead of `python -m src.analyze_packages`
- `query-package` instead of `python -m src.query_package`

## Configuration

### Environment Variables

**PACKAGE_MONKEY_PATH** (optional)
- Path to the package_monkey directory where the `monkey` CLI tool is located
- Default: `/home/user/work/repos/monkey/package_monkey`
- Override by:
  1. Creating a `.env` file: `PACKAGE_MONKEY_PATH=/your/custom/path`
  2. Exporting in shell: `export PACKAGE_MONKEY_PATH=/your/custom/path`

**Example `.env` file:**
```bash
PACKAGE_MONKEY_PATH=/home/user/work/repos/monkey/package_monkey
```

**Note:** The `.env` file is gitignored for security. Use `.env.example` as a template.

## Usage

There are two ways to run the tools:

1. **Without installation** (for development/testing):
   ```bash
   python -m src.analyze_packages source_packages.json
   python -m src.query_package <package_name>
   ```

2. **After installation** (`uv pip install -e .`):
   ```bash
   analyze-packages source_packages.json
   query-package <package_name>
   ```

The following examples use the installed CLI commands. If you haven't installed the package, replace `analyze-packages` with `python -m src.analyze_packages` and `query-package` with `python -m src.query_package`.

### 1. Analyze Source Packages

Run the analysis tool to process source packages from a JSON file:

```bash
analyze-packages source_packages.json
```

**With options:**
```bash
# Specify custom output directory
analyze-packages source_packages.json --output-dir ./output

# Override PACKAGE_MONKEY_PATH
analyze-packages source_packages.json --monkey-path /custom/path/to/monkey
```

**What it does:**
- Reads source package names from the JSON file (must be a JSON array of strings)
- Executes `monkey buildinfo` and `monkey ex` commands for each package
- Generates a single `packages.json` file in the output directory with all package data

**Example source_packages.json:**
```json
["aaa_base", "bash", "coreutils"]
```

### 2. Query Package Information

Query information about a package (source or binary):

```bash
query-package <package_name>
```

The query tool searches first as a source package, then as a binary package across all sources.

**Example - querying a source package:**
```bash
query-package bash
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
query-package envsubst
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
query-package fwts --json | jq .
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

## Troubleshooting

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
