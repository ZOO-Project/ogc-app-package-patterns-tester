# API Reference

## Core Modules

### PatternsManager

Main class for managing pattern deployment and execution.

```python
from ogc_patterns_tester import PatternsManager, ServerConfig

config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",
    auth_token="your-token"
)

manager = PatternsManager(
    server_config=config,
    patterns_dir="data/patterns",
    download_dir="temp/cwl"
)
```

#### Methods

- `run_single_pattern(pattern_id: str) -> ExecutionResult`
- `run_multiple_patterns(pattern_ids: List[str]) -> TestSummary`
- `run_all_patterns() -> TestSummary`
- `deploy_pattern(pattern_id: str) -> ProcessInfo`
- `cleanup_pattern(pattern_id: str) -> bool`

### ServerConfig

Configuration for OGC API Processes server.

```python
from ogc_patterns_tester.models import ServerConfig

config = ServerConfig(
    base_url="https://your-server.com/ogc-api/",
    auth_token="your-jwt-token",
    username=None,
    password=None,
    api_key=None,
    timeout=300
)
```

#### Parameters

- `base_url` (str): Base URL of the OGC API Processes server
- `auth_token` (str, optional): Bearer token for authentication
- `username` (str, optional): Username for basic authentication
- `password` (str, optional): Password for basic authentication
- `api_key` (str, optional): API key for authentication
- `timeout` (int): Request timeout in seconds (default: 300)

### ExecutionResult

Result of pattern execution.

```python
class ExecutionResult:
    pattern_id: str
    success: bool
    message: str
    execution_time: float
    job_id: Optional[str]
    process_id: Optional[str]
```

### TestSummary

Summary of multiple pattern executions.

```python
class TestSummary:
    total_patterns: int
    successful_patterns: int
    failed_patterns: int
    total_execution_time: float
    results: List[ExecutionResult]
```

## CLI Module

### Command Line Interface

The CLI is built with Click and provides the following commands:

```bash
ogc-patterns-tester [OPTIONS] COMMAND [ARGS]
```

#### Global Options

- `-c, --config PATH`: Server JSON configuration file
- `-s, --server-url TEXT`: Base URL of the OGC API Processes server
- `-t, --auth-token TEXT`: Authentication token
- `-p, --patterns-dir PATH`: Directory containing pattern files
- `-d, --download-dir PATH`: Temporary directory for CWL files
- `-f, --force-download`: Force re-download of CWL files
- `-v, --verbose`: Verbose mode

#### Commands

- `run PATTERN_ID`: Execute a specific pattern
- `run-all`: Execute all available patterns
- `run-multiple PATTERN_IDS...`: Execute multiple patterns
- `list-patterns`: List all available patterns
- `deploy PATTERN_ID`: Deploy a pattern without executing
- `cleanup PATTERN_ID`: Clean up a deployed pattern
- `cleanup-all`: Clean up all deployed patterns
- `check-job JOB_ID`: Check job status
- `sync-params`: Synchronize pattern parameters from GitHub

## Utilities

### Logger

```python
from ogc_patterns_tester.utils import setup_logger

logger = setup_logger(verbose=True)
```

### Download CWL Workflows

```python
from ogc_patterns_tester.utils import download_cwl_workflow

cwl_path = download_cwl_workflow(
    pattern_id="pattern-1",
    output_dir="temp/cwl",
    force_download=False
)
```
