# Prerequisites Documentation Reminder

## Required for Documentation

Before finalizing the project, ensure the README.md includes these prerequisites:

### 1. package_monkey Pre-configuration
- **What**: The `monkey` CLI tool from package_monkey must be pre-configured
- **Why**: The analyzer relies on `monkey buildinfo` and `monkey ex` commands
- **Where to document**: Requirements section in README.md
- **Details needed**:
  - How to obtain/install package_monkey
  - Configuration steps required
  - How to verify it's working (e.g., `monkey --help`)
  - Link to package_monkey documentation if available

### 2. jq Installation
- **What**: `jq` command-line JSON processor must be installed
- **Why**: Used by JsonValidator (via validate_json.sh) for JSON validation and sorting
- **Where to document**: Requirements section in README.md
- **Current mention**: Already listed in README.md requirements, but needs emphasis
- **Details needed**:
  - Installation instructions for common platforms
  - How to verify installation: `jq --version`

### 3. PACKAGE_MONKEY_PATH Environment Variable
- **What**: Environment variable pointing to package_monkey directory
- **Current status**: Already documented in README.md Configuration section
- **Default**: /home/user/work/repos/monkey/package_monkey
- **Note**: User must verify this path matches their actual package_monkey installation

## Action Items
- [ ] Update README.md Requirements section with package_monkey setup details
- [ ] Emphasize jq installation requirement
- [ ] Add "Verify Prerequisites" section with test commands
- [ ] Update CONTRIBUTING.md if developer setup differs from user setup
