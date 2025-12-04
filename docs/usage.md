# Usage

## Quick Start

```bash
# Run a single pattern (with Hatch)
hatch run ogc-patterns-tester --server-url https://your-server.com/ogc-api/ run pattern-1

# Run with authentication (Bearer token)
hatch run ogc-patterns-tester \
  --server-url https://your-server.com/ogc-api/ \
  --auth-token "eyJhbGci..." \
  run pattern-1

# Run all patterns
hatch run ogc-patterns-tester \
  --server-url https://your-server.com/ogc-api/ \
  --auth-token "your-token" \
  run-all --timeout 0
```

## Command Line Interface

### Basic Commands

```bash
# List available patterns
ogc-patterns-tester list-patterns

# Execute a specific pattern
ogc-patterns-tester run pattern-1

# Execute multiple patterns
ogc-patterns-tester run-multiple pattern-1 pattern-2 pattern-3

# Execute all available patterns
ogc-patterns-tester run-all
```

### Authentication

The tool supports multiple authentication methods:

```bash
# Bearer token (JWT - recommended)
ogc-patterns-tester \
  --server-url https://your-server.com/ogc-api/ \
  --auth-token "eyJhbGci..." \
  run pattern-1
```

**Authentication Methods:**

- **Bearer Token** (`--auth-token`): JWT tokens from OAuth2/OIDC providers
- **Basic Auth**: Username/password (configure programmatically)
- **API Key**: Custom API keys (configure programmatically)

### Advanced Options

```bash
# Verbose mode
ogc-patterns-tester --verbose run-all

# Custom timeout (seconds, 0 = unlimited)
ogc-patterns-tester run pattern-1 --timeout 600

# Continue on error
ogc-patterns-tester run-all --continue-on-error

# Force re-download CWL files
ogc-patterns-tester --force-download run pattern-1
```

## Programmatic Usage

### Simple Example

```python
from ogc_patterns_tester import PatternsManager, ServerConfig

# Server configuration
config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",
    auth_token="eyJhbGci...",
    timeout=300
)

# Create manager
manager = PatternsManager(
    server_config=config,
    patterns_dir="data/patterns",
    download_dir="temp/cwl"
)

# Execute pattern
result = manager.run_single_pattern("pattern-1")

if result.success:
    print(f"✓ Success in {result.execution_time:.1f}s")
else:
    print(f"✗ Failed: {result.message}")
```

### Advanced Example

```python
from ogc_patterns_tester import PatternsManager, ServerConfig

config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",
    auth_token="your-bearer-token",
    timeout=600
)

manager = PatternsManager(
    server_config=config,
    patterns_dir="data/patterns",
    download_dir="temp/cwl",
    force_download=False
)

# Execute multiple patterns
pattern_ids = ["pattern-1", "pattern-2", "pattern-3"]
summary = manager.run_multiple_patterns(
    pattern_ids,
    timeout=0,
    continue_on_error=True
)

print(f"Results: {summary.successful_patterns}/{summary.total_patterns} successful")
```

## Supported Patterns

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
