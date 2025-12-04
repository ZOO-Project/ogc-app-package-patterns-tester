# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Parameter Synchronization from GitHub Notebooks**
  - New `NotebookParser` module to extract `params` from Jupyter notebooks
  - CLI command `sync-params` to download and sync parameters from upstream
  - Standalone script `sync_params_from_notebooks.py` for easy usage
  - Automatic extraction handles nested dictionaries, lists, and multi-line strings
  - Supports syncing single, multiple, or all patterns (1-12)
  - 20 comprehensive unit tests for notebook parsing functionality
  - Example script in `examples/notebook_parser_example.py`
  
- **Features:**
  - Downloads notebooks from [eoap/application-package-patterns](https://github.com/eoap/application-package-patterns/tree/main/docs)
  - Parses Python code cells to extract `params = {...}` definitions
  - Uses `ast.literal_eval` for robust parsing of Python syntax
  - Fallback to JSON parsing with syntax conversion
  - Saves formatted JSON files to `data/patterns/`
  - Continue-on-error option for batch processing
  - Detailed logging with success/failure indicators

- **CLI Usage:**
  ```bash
  # Sync single pattern
  ogc-patterns-tester sync-params pattern-1
  
  # Sync multiple patterns
  ogc-patterns-tester sync-params pattern-1 pattern-2 pattern-3
  
  # Sync all patterns
  ogc-patterns-tester sync-params --all
  
  # Custom output directory
  ogc-patterns-tester sync-params --all --output-dir custom/params
  ```

### Fixed
- Authentication parameter mapping: Changed `api_key` to `access_token` in `patterns_manager.py`
- Added explicit authentication headers to `list_processes()` and `get_process_description()`
- Fixed 401 Unauthorized errors in integration tests
- Improved error detail logging in `deploy_process()`

### Changed
- Integration tests now use real pattern-1 CWL from GitHub instead of simple echo command
- Updated README.md with complete documentation for current project state
- Test count increased from 41 to 61 unit tests (with notebook parser tests)

## [0.1.0] - 2024-11-30

### Added
- Initial release
- OGC API Processes client wrapper
- Pattern deployment and execution functionality
- Authentication support (Bearer tokens, Basic auth, API keys)
- Automatic cleanup handlers
- CLI interface with multiple commands
- 41 unit tests
- 3 integration tests
- Comprehensive README documentation
