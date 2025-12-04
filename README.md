# OGC Application Package Patterns Tester

A Python tool for testing OGC API Processes application package patterns using the `ogc-api-client` library.

This project provides a Python implementation of pattern testing functionality, allowing automated deployment, execution, and cleanup of CWL workflows on OGC API Processes servers.

## Features

- ✅ **Automatic deployment** of CWL patterns on OGC API Processes servers
- ✅ **Automated execution** with pattern-specific parameters
- ✅ **Job monitoring** with configurable timeouts
- ✅ **Automatic cleanup** of deployed processes and jobs
- ✅ **Multiple authentication methods** (Bearer tokens, Basic auth, API keys)
- ✅ **Parameter synchronization** from GitHub notebooks to local JSON files
- ✅ **Comprehensive testing** with 41 unit tests and integration tests
- ✅ **Clean interrupt handling** with graceful shutdown messages

## Installation

### Prerequisites

- Python 3.8 or newer
- [Hatch](https://hatch.pypa.io/) for development (recommended)
- A running OGC API Processes server

### Quick Installation with Hatch (Recommended)

```bash
# Clone the project
git clone <repository-url>
cd ogc-app-package-patterns-tester

# Install Hatch if not already installed
pip install hatch

# Build the package
hatch build --clean

# Run the CLI (Hatch manages the environment automatically)
hatch run ogc-patterns-tester --help
```

### Alternative: pip Installation

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install the package
pip install -e .
```

### Verify Installation

```bash
# With Hatch
hatch run ogc-patterns-tester --help

# Or if installed in venv
ogc-patterns-tester --help
```

## Usage

### Quick Start

```bash
# Run a single pattern (with Hatch)
hatch run ogc-patterns-tester --server-url https://your-server.com/ogc-api/ run pattern-1

# Run with authentication (Bearer token)
hatch run ogc-patterns-tester \
  --server-url https://your-server.com/ogc-api/ \
  --auth-token "eyJhbGci..." \
  run pattern-1

# Run all patterns with unlimited timeout
hatch run ogc-patterns-tester \
  --server-url https://your-server.com/ogc-api/ \
  --auth-token "your-token" \
  run-all --timeout 0

# If installed in venv, omit 'hatch run'
ogc-patterns-tester --server-url https://your-server.com/ogc-api/ run pattern-1
```

### Command Line Interface

#### Basic Commands

```bash
# Execute a specific pattern
ogc-patterns-tester run pattern-1

# Execute multiple patterns
ogc-patterns-tester run-multiple pattern-1 pattern-2 pattern-3

# Execute all available patterns
ogc-patterns-tester run-all
ogc-patterns-tester list-patterns
```

**Note**: CWL workflows are automatically downloaded from the [eoap/application-package-patterns](https://github.com/eoap/application-package-patterns) repository on first use. Files are cached in `temp/cwl/` directory. Use `--force-download` to refresh cached files.

#### Server Configuration and Authentication

```bash
# Use a specific server
ogc-patterns-tester --server-url https://your-server.com/ogc-api/ run pattern-1

# Bearer token authentication (JWT - recommended)
ogc-patterns-tester \
  --server-url https://your-server.com/ogc-api/ \
  --auth-token "eyJhbGci..." \
  run pattern-1

# Basic authentication (if supported by server)
# Note: Configure via ServerConfig in Python code

# API key authentication (if supported by server)  
# Note: Configure via ServerConfig in Python code
```

**Authentication Methods:**
- **Bearer Token** (`--auth-token`): JWT tokens from OAuth2/OIDC providers (most common)
- **Basic Auth**: Username/password (configure programmatically)
- **API Key**: Custom API keys (configure programmatically)

**Note**: The `--auth-token` parameter maps to Bearer token authentication internally.

#### Advanced Options

```bash
# Verbose mode for detailed logging
ogc-patterns-tester --verbose run-all

# Custom timeout (in seconds, 0 = unlimited)
ogc-patterns-tester run pattern-1 --timeout 600

# Unlimited timeout (wait indefinitely for job completion)
ogc-patterns-tester run pattern-1 --timeout 0

# Continue even if errors occur
ogc-patterns-tester run-all --continue-on-error

# Force re-download of CWL files
ogc-patterns-tester --force-download run pattern-1

# Clean interrupt handling
# Press Ctrl+C to interrupt execution - cleanup occurs automatically
# A clean message is displayed instead of Python traceback
```

#### Parameter Synchronization

Automatically extract and update pattern parameters from GitHub notebooks:

```bash
# Sync parameters for a single pattern
ogc-patterns-tester sync-params pattern-1

# Sync parameters for multiple patterns
ogc-patterns-tester sync-params pattern-1 pattern-2 pattern-3

# Sync all patterns (1-12)
ogc-patterns-tester sync-params --all

# Custom output directory
ogc-patterns-tester sync-params pattern-1 --output-dir custom/params

# Continue even if some patterns fail
ogc-patterns-tester sync-params --all --continue-on-error

# Using the standalone script (alternative)
python sync_params_from_notebooks.py pattern-1
python sync_params_from_notebooks.py  # Syncs all patterns
```

**How it works:**
1. Downloads Jupyter notebooks from [eoap/application-package-patterns](https://github.com/eoap/application-package-patterns/tree/main/docs)
2. Extracts the `params` variable from code cells
3. Saves as formatted JSON in `data/patterns/`

**Use this when:**
- Setting up the project for the first time
- Upstream notebooks have been updated
- You want to refresh local parameter files

**Example output:**
```
Patterns to sync: pattern-1, pattern-2, pattern-3

✓ Downloaded notebook for pattern-1
✓ Found params in notebook
✓ Saved parameters to data/patterns/pattern-1.json

Summary: 3/3 patterns synced successfully
```

### Programmatic Usage

#### Simple Example

```python
from ogc_patterns_tester import PatternsManager, ServerConfig

# Server configuration with Bearer token
config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",
    auth_token="eyJhbGci...",  # JWT Bearer token
    timeout=300
)

# Create the manager
manager = PatternsManager(
    server_config=config,
    patterns_dir="data/patterns",
    download_dir="temp/cwl"
)

# Execute a pattern
result = manager.run_single_pattern("pattern-1")

if result.success:
    print(f"✓ Pattern executed successfully in {result.execution_time:.1f}s")
else:
    print(f"✗ Failed: {result.message}")
```

#### Advanced Example with Multiple Patterns

```python
from ogc_patterns_tester import PatternsManager, ServerConfig, CleanupHandler

# Configuration
config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",
    auth_token="your-bearer-token",
    timeout=600
)

# Create cleanup handler for tracking
cleanup_handler = CleanupHandler()

# Manager with custom settings
manager = PatternsManager(
    server_config=config,
    patterns_dir="data/patterns",
    download_dir="temp/cwl",
    force_download=False,  # Use cached CWL files
    cleanup_handler=cleanup_handler
)

# Execute multiple patterns
pattern_ids = ["pattern-1", "pattern-2", "pattern-3"]
summary = manager.run_multiple_patterns(
    pattern_ids,
    timeout=0,  # Unlimited timeout
    continue_on_error=True
)

# Display results
print(f"Results: {summary.successful_patterns}/{summary.total_patterns} successful")
print(f"Total time: {summary.total_execution_time:.1f}s")

for result in summary.results:
    status = "✓" if result.success else "✗"
    print(f"{status} {result.pattern_id}: {result.message}")
```

## Configuration

### Environment Variables

- `OGC_TEST_SERVER_URL`: Server URL for integration tests
- `OGC_TEST_ACCESS_TOKEN`: Bearer token for integration tests  
- `OGC_TEST_USERNAME`: Username for Basic auth (alternative to token)
- `OGC_TEST_PASSWORD`: Password for Basic auth (alternative to token)

### ServerConfig Options

When using the tool programmatically:

```python
from ogc_patterns_tester.models import ServerConfig

config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",  # Required
    auth_token="your-jwt-token",                   # Bearer token (recommended)
    username=None,                                 # Basic auth username
    password=None,                                 # Basic auth password
    api_key=None,                                  # API key (alternative)
    timeout=300                                    # Request timeout in seconds
)
```

**Note**: `auth_token` is automatically mapped to `access_token` for Bearer authentication internally.

## Supported Patterns

The tool tests CWL workflows from the [eoap/application-package-patterns](https://github.com/eoap/application-package-patterns) repository:

| Pattern | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| pattern-1 | One input/one output | 1 | 1 |
| pattern-2 | Two inputs/one output | 2 | 1 |
| pattern-3 | Scatter on inputs/one output | Multiple | 1 |
| pattern-4 | One input/two outputs | 1 | 2 |
| pattern-5 | One input/scatter on outputs | 1 | Multiple |
| pattern-6 | One input, no output | 1 | 0 |
| pattern-7 | Optional inputs, one output | 1-N | 1 |
| pattern-8 | One input, optional output | 1 | 0-1 |
| pattern-9 | One input, optional outputs | 1 | 0-N |
| pattern-10 | Multiple inputs, multiple outputs | N | N |
| pattern-11 | One input/one output (with DEM) | 1 | 1 |
| pattern-12 | One input/multiple outputs (complex) | 1 | N |

**CWL Workflows**: Automatically downloaded from GitHub on first use. Cached in `temp/cwl/` directory.

## Development

### Running Tests

```bash
# Run all unit tests (with Hatch)
hatch run test

# Run tests with coverage
hatch run test-cov

# Run only unit tests (skip integration tests)
hatch run test --no-cov

# Run integration tests (requires server and credentials)
export OGC_TEST_SERVER_URL="https://your-server.com/ogc-api/"
export OGC_TEST_ACCESS_TOKEN="your-bearer-token"
hatch run test -m integration

# Run specific test file
hatch run pytest tests/test_client.py -v

# Run with verbose output
hatch run test -v
```

### Integration Tests

Integration tests validate the tool against a real OGC API Processes server:

```bash
# Set environment variables
export OGC_TEST_SERVER_URL="https://d122.sandbox.ospd.geolabs.fr/ogc-api/"
export OGC_TEST_ACCESS_TOKEN="eyJhbGci..."  # Your JWT token

# Run integration tests
hatch run test -m integration -v

# Run specific integration test
hatch run test -m integration -k test_deploy_simple_process -v
```

**Integration Tests Include:**
- ✅ `test_list_processes` - List processes on server
- ✅ `test_get_capabilities` - Server connectivity check
- ✅ `test_deploy_simple_process` - Deploy and cleanup pattern-1

### Code Quality

```bash
# Format code with Black
hatch run fmt

# Run linter
hatch run lint

# Type checking with mypy
hatch run typing

# Run all quality checks
hatch run fmt && hatch run lint && hatch run typing
```

## Project Structure

### Key Components

- **`cli.py`**: Click-based CLI with clean KeyboardInterrupt handling
- **`client.py`**: Wraps `ogc-api-client` with Bearer token support and authentication
- **`patterns_manager.py`**: Orchestrates pattern deployment, execution, monitoring, cleanup
- **`models.py`**: Type-safe data models for processes, jobs, configurations
- **`utils.py`**: Helper functions for downloads, logging, file operations

## Test Coverage

**Current test coverage: 41 passing tests**

### Unit Tests
- ✅ `test_client.py` - OGC API client operations (10 tests)
- ✅ `test_patterns_manager.py` - Pattern orchestration (7 tests)
- ✅ `test_models.py` - Data model validation (12 tests)
- ✅ `test_patterns_tester.py` - End-to-end scenarios (12 tests)

### Integration Tests  
- ✅ `test_integration.py` - Real server validation (3 tests)
  - List processes with authentication
  - Server capabilities check
  - Deploy and cleanup pattern-1

Run tests with:
```bash
# Unit tests only
hatch run test --no-cov

# All tests including integration (requires server + credentials)
export OGC_TEST_SERVER_URL="https://your-server.com/ogc-api/"
export OGC_TEST_ACCESS_TOKEN="your-token"
hatch run test -m integration
```

## Troubleshooting

### Authentication Issues

**Problem**: `401 Unauthorized` errors

**Solutions**:
1. Verify your Bearer token is valid and not expired
2. Check token format: `--auth-token "eyJhbGci..."`
3. Ensure server accepts Bearer authentication
4. For integration tests, check `OGC_TEST_ACCESS_TOKEN` environment variable

### Timeout Issues

**Problem**: Jobs timeout before completion

**Solutions**:
1. Use `--timeout 0` for unlimited timeout
2. Increase timeout: `--timeout 3600` (1 hour)
3. Check server logs for job execution issues

### CWL Download Issues

**Problem**: Cannot download CWL workflows

**Solutions**:
1. Check internet connectivity
2. Verify GitHub is accessible
3. Use `--force-download` to refresh cached files
4. Check `temp/cwl/` directory permissions

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes
4. **Test** your changes: `hatch run test`
5. **Format** your code: `hatch run fmt`
6. **Commit** your changes: `git commit -am 'Add amazing feature'`
7. **Push** to the branch: `git push origin feature/amazing-feature`
8. **Open** a Pull Request

### Development Guidelines

- Write tests for new features
- Keep test coverage above 20%
- Follow PEP 8 style guidelines (enforced by Black)
- Add docstrings to public functions and classes
- Update documentation for user-facing changes

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Links and Resources

- **OGC API Client**: [github.com/EOEPCA/ogc-api-client](https://github.com/EOEPCA/ogc-api-client)
- **Application Package Patterns**: [github.com/eoap/application-package-patterns](https://github.com/eoap/application-package-patterns)
- **OGC API Processes**: [ogcapi.ogc.org/processes](https://ogcapi.ogc.org/processes/)
- **Hatch Documentation**: [hatch.pypa.io](https://hatch.pypa.io/)
- **CWL User Guide**: [commonwl.org](https://www.commonwl.org/)

## Acknowledgments

This tool implements pattern testing functionality for OGC API Processes servers, enabling automated validation of CWL application package patterns.

Built with:
- `ogc-api-client` - OGC API interaction library
- `Click` - Command line interface framework
- `Hatch` - Modern Python project management
- `pytest` - Testing framework

---

**Version**: 0.1.0  
**Python**: 3.8+  
**License**: Apache 2.0