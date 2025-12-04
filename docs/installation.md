# Installation

## Prerequisites

- Python 3.8 or newer
- [Hatch](https://hatch.pypa.io/) for development (recommended)
- A running OGC API Processes server

## Quick Installation with Hatch (Recommended)

```bash
# Clone the project
git clone https://github.com/ZOO-Project/ogc-app-package-patterns-tester.git
cd ogc-app-package-patterns-tester

# Install Hatch if not already installed
pip install hatch

# Build the package
hatch build --clean

# Run the CLI (Hatch manages the environment automatically)
hatch run ogc-patterns-tester --help
```

## Alternative: pip Installation

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install the package
pip install -e .
```

## Verify Installation

```bash
# With Hatch
hatch run ogc-patterns-tester --help

# Or if installed in venv
ogc-patterns-tester --help
```

You should see the CLI help message with available commands.
