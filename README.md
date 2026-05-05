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
- `monkey` CLI tool (package_monkey)
- `jq` (for JSON validation)

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
- Generates two JSON files in the output directory:
  - `binary_packages.json`: Binary packages with reverse dependencies
  - `media_inclusion.json`: Media inclusion information

**Example source_packages.json:**
```json
["aaa_base", "bash", "coreutils"]
```

### 2. Query Package Information

Query information about a specific source package:

```bash
query-package <source_package_name>
```

**Example:**
```bash
query-package gettext-runtime
```

**Output:**
```
Source Package: gettext-runtime
Binary Packages: 2

1. gettext-runtime
   Required by: (none)
   Media inclusion: Not in media

2. gettext-tools
   Required by:
     - fontconfig-devel
     - intltool
   Media inclusion:
     SLE-15-SP7-Full-x86_64-GM-Media1:
       - Required by RPM: fontconfig-devel
```

**JSON output:**
```bash
query-package fwts --json | jq .
```

## Output Format

The tool generates two JSON files with simplified data focused on essential package information.

### binary_packages.json

Maps binary package names to their reverse dependencies:

```json
{
  "aaa_base": {
    "name": "aaa_base",
    "required_by": ["aaa_base-extras"]
  },
  "aaa_base-extras": {
    "name": "aaa_base-extras",
    "required_by": []
  },
  "bash": {
    "name": "bash",
    "required_by": ["bash-completion", "bash-doc"]
  }
}
```

**Fields:**
- `name`: Binary package name
- `required_by`: List of package names that require this package (reverse dependencies)

### media_inclusion.json

Maps binary package names to their media inclusion information:

```json
{
  "aaa_base": {
    "SLE-15-SP7-Full-x86_64-GM-Media1": [
      {
        "reason_chain": ["aaa_base include"],
        "required_by_rpm": "filesystem"
      }
    ]
  },
  "bash": {
    "SLE-15-SP7-Full-x86_64-GM-Media1": [
      {
        "reason_chain": ["bash include"],
        "required_by_rpm": null
      }
    ],
    "SLE-15-SP7-Full-aarch64-GM-Media1": [
      {
        "reason_chain": ["bash include"],
        "required_by_rpm": null
      }
    ]
  }
}
```

**Fields:**
- Top-level key: Binary package name
- Second-level key: Media name (e.g., `SLE-15-SP7-Full-x86_64-GM-Media1`)
- `reason_chain`: List with the inclusion reason (typically `["<package-name> include"]`)
- `required_by_rpm`: Package that requires this binary package (if applicable), or `null`

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
