# CI/CD Pipeline Documentation

## Overview

This repository uses GitHub Actions for continuous integration and deployment. The pipeline consists of two main workflows:

1. **Build and Test** - Runs on every push and pull request
2. **Publish** - Runs on version tags and manual triggers

## Workflows

### 1. Build and Test Workflow (`build.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Jobs:**

#### Version Check
- Verifies that if Python or TOML files have changed, the version number in `pyproject.toml` has been updated
- Fails early if a release with the current version already exists
- Prevents accidental overwrites of published versions

#### Test Matrix
- **Platforms:** Ubuntu, Windows, macOS
- **Python versions:** 3.8, 3.9, 3.10, 3.11, 3.12
- **Steps:**
  1. Install dependencies including dev tools
  2. Check code formatting with Black
  3. Auto-format if needed (with warning)
  4. Run unit tests with pytest
  5. Upload coverage reports (Ubuntu + Python 3.11 only)

#### Integration Tests
- Tests actual CLI functionality on all platforms
- Verifies installation and basic commands work
- Tests wildcard patterns and file operations

### 2. Publish Workflow (`publish.yml`)

**Triggers:**
- Push of tags matching `v*` pattern
- Manual workflow dispatch

**Jobs:**

#### Version Check
- Extracts version from `pyproject.toml`
- Ensures version hasn't been previously released
- Outputs version for subsequent jobs

#### Test Suite
- Runs reduced test matrix (Python 3.8 and 3.11 on all platforms)
- Ensures all tests pass before publishing
- Verifies code formatting compliance

#### Build
- Creates source distribution and wheel
- Validates package with `twine check`
- Uploads build artifacts for publishing

#### Publish to PyPI
- Uses PyPI trusted publisher (OIDC)
- Requires `pypi` environment approval
- Publishes to https://pypi.org/project/dropblock/

#### Create GitHub Release
- Generates release notes from commit history
- Attaches built packages (wheel and tarball)
- Creates GitHub release with version tag

## Testing Strategy

### Test Structure
The repository contains two types of tests in the `test/` directory:

#### 1. Mock Tests (`test_obvious.py`)
- Unit tests that mock system calls for rapid feedback
- Cross-platform compatible (run on all platforms)
- Test code logic without requiring actual system tools
- Use `@unittest.skipUnless` to only run on appropriate platforms when needed

#### 2. Integration Tests (`test_actual.py`)  
- **Real filesystem operations** - Creates actual files and directories
- **Platform-specific functionality** - Tests actual PowerShell, xattr, and attr commands
- **Conflict detection** - Uses real conflicted file scenarios
- **CLI integration** - Tests the actual command-line interface
- **Debug mode testing** - Verifies traceback output in debug scenarios

### Platform-Specific Testing
Each platform runs real tests:
- **Windows:** PowerShell `Set-Content -Stream` commands with verification
- **macOS:** `xattr` commands with File Provider detection
- **Linux:** `attr` and `xattr` commands with fallback logic

### Test Dependencies
- **Mock tests:** Only Python standard library
- **Integration tests:** Platform-specific tools (PowerShell, xattr, attr)
- **Dropbox SDK:** Available via `pip install -e ".[test]"` for future Dropbox API integration

## Version Management

### Automatic Version Checking
The pipeline enforces version updates when:
1. Python or TOML files change
2. A release with the current version exists

### Version Update Process
1. Update version in `pyproject.toml`
2. Commit changes
3. Push to branch (triggers build workflow)
4. Create tag `v<version>` (triggers publish workflow)
5. Push tag to trigger release

### Manual Release
```bash
# Update version in pyproject.toml
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## Black Formatter Configuration

### Settings (from `pyproject.toml`)
- Line length: 88 characters
- Target Python versions: 3.6+
- Excludes: build directories, virtual environments

### Enforcement
- Build workflow checks formatting
- Auto-formats if needed (with warning)
- Developers should run `black .` locally before committing

## PyPI Publishing

### Setup Requirements
1. Repository must have PyPI trusted publisher configured
2. Create `pypi` environment in GitHub repository settings
3. No API tokens needed (uses OIDC authentication)

### Published Artifacts
- Source distribution (`.tar.gz`)
- Wheel distribution (`.whl`)
- Both attached to GitHub releases

## Local Development

### Running Tests Locally
```bash
# Install dev and test dependencies
pip install -e ".[dev,test]"

# Run formatter
black .

# Run all tests
pytest test/ -v

# Run only mock tests (fast)
pytest test/test_obvious.py -v

# Run only integration tests (slower, requires platform tools)
pytest test/test_actual.py -v

# Run with coverage
pytest test/ --cov=dropblock --cov-report=term-missing

# Run with debug output
DEBUG=true pytest test/test_actual.py -v -s
```

### Pre-commit Checklist
1. ✅ Update version if needed
2. ✅ Run `black .` for formatting
3. ✅ Run tests on your platform
4. ✅ Update documentation if needed
5. ✅ Commit and push changes

## Troubleshooting

### Common Issues

1. **Version already exists error**
   - Update version in `pyproject.toml`
   - Ensure version follows semantic versioning

2. **Black formatting failures**
   - Run `black .` locally
   - Commit formatted changes

3. **Platform-specific test failures**
   - Check test skip conditions
   - Verify platform detection logic
   - Review mock configurations

4. **Publishing failures**
   - Verify PyPI environment configuration
   - Check GitHub Actions permissions
   - Ensure tag matches `v*` pattern

## Security Considerations

- Uses PyPI trusted publishing (no stored tokens)
- Runs tests in isolated environments
- Version checks prevent accidental overwrites
- Platform-specific code properly isolated

## Future Improvements

- [ ] Add type checking with mypy
- [ ] Implement changelog generation
- [ ] Add security scanning (e.g., bandit)
- [ ] Setup dependabot for dependency updates
- [ ] Add performance benchmarks
- [ ] Implement signed releases