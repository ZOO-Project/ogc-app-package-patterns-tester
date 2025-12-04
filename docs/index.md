# OGC Application Package Patterns Tester

A Python tool for testing OGC API Processes application package patterns using the `ogc-api-client` library.

## Overview

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

## Quick Start

```bash
# Install with Hatch
pip install hatch
hatch build --clean

# Run a pattern
hatch run ogc-patterns-tester --server-url https://your-server.com/ogc-api/ run pattern-1
```

## Documentation

- [Installation](installation.md) - Setup and installation guide
- [Usage](usage.md) - How to use the tool
- [API Reference](api.md) - Python API documentation
- [Contributing](contributing.md) - Contributing guidelines

## Links

- **GitHub**: [ZOO-Project/ogc-app-package-patterns-tester](https://github.com/ZOO-Project/ogc-app-package-patterns-tester)
- **OGC API Client**: [github.com/EOEPCA/ogc-api-client](https://github.com/EOEPCA/ogc-api-client)
- **Application Package Patterns**: [github.com/eoap/application-package-patterns](https://github.com/eoap/application-package-patterns)
