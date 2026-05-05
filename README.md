# Package Analyzer

A Python tool to analyze source packages and their binary dependencies using the `monkey` CLI tool. This tool extracts information about binary packages, their reverse dependencies, and media inclusion details.

## Features

- **Binary Package Analysis**: Extract all binary packages produced by source packages and their reverse dependencies
- **Media Inclusion Tracking**: Determine which binary packages are included in media (products like sles_16.1, sleha_16.1) and why
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
Binary Packages: 8

1. gettext-runtime-32bit (CoreLocalization-32bit) v0.22.5
   Architectures: x86_64
   Required by: (none)
   Media inclusion: Not in media

2. gettext-tools (CoreLocalization-api) v0.22.5
   Architectures: x86_64, s390x, ppc64le, aarch64
   Required by:
     - fontconfig-devel (CoreX11-api)
     - intltool (Internationalization-api)
   Media inclusion:
     sles_16.1:
       - Required by: fontconfig-devel
         Reason: propagated from epic: CoreX11 → set by policy: epic:CoreX11
```

**JSON output:**
```bash
query-package fwts --json | jq .
```

## Output Format

### binary_packages.json

```json
{
  "source_package_name": {
    "binary_packages": [
      {
        "name": "binary-package-name",
        "purpose": "Epic-classification",
        "version": "1.2.3",
        "architectures": ["x86_64", "aarch64"],
        "summary": "Package description",
        "required_by": [
          {"package": "other-package", "purpose": "OtherEpic-classification"}
        ]
      }
    ]
  }
}
```

### media_inclusion.json

```json
{
  "binary_package_name": {
    "media_name": [
      {
        "reason_chain": [
          "include",
          "propagated from epic: EpicName",
          "set by policy: policy:name"
        ],
        "required_by_rpm": "package-that-requires-this"
      }
    ]
  }
}
```

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
