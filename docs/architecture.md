# Architecture Documentation

## Overview

Capuchin is designed to extract and analyze package dependency information from the `monkey` CLI tool. It follows a modular architecture with clear separation of concerns.

## High-Level Design

```
┌─────────────────┐
│source_packages  │
│     .json       │
└────────┬────────┘
         │
         v
┌────────────────────────────────────────┐
│      Capuchin                  │
│  ┌──────────────────────────────────┐  │
│  │  For each source package:        │  │
│  │  1. Run monkey buildinfo         │  │
│  │  2. Parse binary packages        │  │
│  │  3. For each binary package:     │  │
│  │     - Run monkey ex              │  │
│  │     - Parse media inclusion      │  │
│  └──────────────────────────────────┘  │
└────────┬───────────────────────────────┘
         │
         v
┌────────────────────────────────────────┐
│         JSON Output                    │
│  ┌─────────────────┬─────────────────┐ │
│  │ binary_packages │ media_inclusion │ │
│  │      .json      │      .json      │ │
│  └─────────────────┴─────────────────┘ │
└────────┬───────────────────────────────┘
         │
         v
┌────────────────────────────────────────┐
│         Query Tool                     │
│  - Load JSON files                     │
│  - Query by source package             │
│  - Format output (text/JSON)           │
└────────────────────────────────────────┘
```

## Module Responsibilities

### src/config.py

**Purpose**: Centralized configuration management

**Responsibilities**:
- Load environment variables from `.env` file
- Provide default values
- Validate configuration (e.g., path exists)

**Key Functions**:
- `Config.get_package_monkey_path()`: Returns path to monkey CLI tool

### src/models.py

**Purpose**: Data models for type safety and serialization

**Models**:
- `BinaryPackage`: Represents a binary package with name and reverse dependencies
- `SourcePackage`: Groups binary packages from same source
- `InclusionReason`: Represents one inclusion path in media (reason chain + optional required_by_rpm)
- `MediaInclusion`: Maps media to inclusion reasons
- `BinaryPackageInfo`: Extended info for query results
- `QueryResult`: Result of querying a source package

**Design Decision**: Use dataclasses for simplicity and built-in features (type hints, repr, equality)

**Simplified Data Model**: Focus on essential information only:
- Binary package names and reverse dependencies (no version, architecture, summary, epic)
- Media inclusion and required_by_rpm (no propagation chains or policy details)

### src/monkey_parser.py

**Purpose**: Parse monkey command outputs into structured data

**Responsibilities**:
- Parse `monkey buildinfo` output → `List[BinaryPackage]`
- Parse `monkey ex` output → `Dict[str, List[InclusionReason]]`

**Parsing Strategy**:

#### buildinfo Parser
```
Build source_package (SLE15-SP7)
binary_package_1 (Purpose)
  required by:
    - package1 (Purpose1)
    - package2 (Purpose2)
binary_package_2 (Purpose)
  ...
```

**Extracts (simplified)**:
- Binary package names
- List of "required by" package names (just names, ignores purpose/epic)
- **Ignores**: version, architectures, summary, epic classifications

**Strategy**:
- Split by package blocks (identified by indentation)
- Extract package name from header line
- Parse "required by" list, extracting only package names

#### ex Parser
```
media_name:
  └─> binary_package include
      is required by rpm: other_package
```

**Extracts (simplified)**:
- Which media the package is included in
- Optional "required_by_rpm" value if present
- **Ignores**: propagation chains, policy details, complex reason trees

**Strategy**:
- Identify media sections (lines ending with colon)
- Extract package name from "└─> package-name include" line
- Extract required_by_rpm from "is required by rpm:" line if present
- Ignore "spurious decision" (non-existent packages)

### src/package_analyzer.py

**Purpose**: Orchestrate the analysis workflow

**Responsibilities**:
- Execute monkey commands via subprocess
- Coordinate parsing
- Generate JSON output
- Validate JSON files

**Workflow**:
1. Load source packages from JSON
2. For each source package:
   - Run `monkey buildinfo <source>`
   - Parse binary packages
   - For each binary package:
     - Run `monkey ex <binary>`
     - Parse media inclusion
3. Aggregate results
4. Write JSON files
5. Validate JSON files

**Design Decision**: Change directory to `PACKAGE_MONKEY_PATH` before running commands to ensure monkey tool can access its database.

### src/json_validator.py

**Purpose**: Validate and sort JSON output

**Responsibilities**:
- Validate JSON syntax
- Sort JSON (arrays/object keys)
- Call existing `validate_json.sh` script

**Design Decision**: Reuse existing bash script instead of reimplementing to maintain consistency.

### src/query_package.py

**Purpose**: Query and display package information

**Responsibilities**:
- Load JSON files into memory
- Query by source package name
- Format output (human-readable or JSON)
- Display binary packages, dependencies, and media inclusion

**Output Format**:
- Text: Structured, indented, easy to read
- JSON: Machine-readable for further processing

## Data Flow

```
source_packages.json
        ↓
    [Capuchin]
        ↓
    subprocess: monkey buildinfo
        ↓
    [MonkeyParser.parse_buildinfo]
        ↓
    List[BinaryPackage]
        ↓
    For each binary:
        subprocess: monkey ex
            ↓
        [MonkeyParser.parse_ex]
            ↓
        Dict[media, List[InclusionReason]]
        ↓
    Aggregate results
        ↓
    binary_packages.json + media_inclusion.json
        ↓
    [JSONValidator]
        ↓
    Validated, sorted JSON
        ↓
    [QueryTool]
        ↓
    Display results
```

## Design Decisions

### Simplified Data Model

**Decision**: Extract only essential information, ignore metadata

**Rationale**:
- Focus on what's needed: binary names, dependencies, media inclusion
- Simpler JSON structure, easier to process
- Faster parsing (skip unnecessary fields)
- Reduced storage requirements

**What we extract**:
- Binary package names
- Reverse dependencies (just package names)
- Media inclusion (which media, required_by_rpm)

**What we ignore**:
- Version numbers, architectures, summaries
- Epic classifications and purpose fields
- Complex propagation chains and policy details
- Reason tree hierarchies

### Why Two JSON Files?

**Decision**: Separate `binary_packages.json` and `media_inclusion.json`

**Rationale**:
- Clear separation of concerns
- Easier to consume independently
- Simpler schema for each file

**Alternative Considered**: Single nested JSON
- Pro: All data in one place
- Con: More complex structure, harder to query

### Why Dataclasses?

**Decision**: Use Python dataclasses for models

**Rationale**:
- Built-in type hints support
- Auto-generated `__init__`, `__repr__`, `__eq__`
- Easy serialization with `asdict()`
- Lightweight (no external dependencies)

**Alternative Considered**: Pydantic
- Pro: Advanced validation, better error messages
- Con: External dependency, overkill for this use case

### Why Subprocess for Monkey Commands?

**Decision**: Execute monkey commands via subprocess

**Rationale**:
- Monkey tool is external CLI, not Python library
- Direct execution ensures compatibility
- No need to reverse-engineer monkey's database format

### Why Environment Variables?

**Decision**: Use `PACKAGE_MONKEY_PATH` environment variable

**Rationale**:
- Flexible: users can override default path
- Secure: actual paths in `.env` (gitignored)
- Standard practice in modern applications

## Error Handling Strategy

1. **Command Failures**: Log stderr, continue with remaining packages
2. **Parse Failures**: Log warning, skip malformed entries (don't fail entire analysis)
3. **JSON Validation**: Fail fast if output JSON is invalid (data integrity)
4. **File I/O**: Check permissions, handle missing files gracefully
5. **Configuration Errors**: Fail fast if PACKAGE_MONKEY_PATH doesn't exist

## Testing Strategy

### Unit Tests
- Each module tested independently
- Mock subprocess calls
- Use fixture files for parser tests
- Target >90% code coverage

### Integration Tests
- Test full workflow with sample data
- Verify JSON structure and validity
- Test error scenarios

### Test Fixtures
- Real monkey command outputs captured as text files
- Cover edge cases: no dependencies, multiple architectures, not in media

## Performance Considerations

- **Sequential Processing**: Process packages one at a time (monkey commands are I/O bound)
- **Caching**: Consider caching monkey command outputs for testing
- **Memory**: Load all results in memory (reasonable for typical package counts)

## Future Enhancements

- Parallel processing of packages (if monkey supports it)
- SQLite backend for querying large datasets
- Web UI for interactive exploration
- Diff tool to compare results between runs
- Export to other formats (CSV, Excel)
