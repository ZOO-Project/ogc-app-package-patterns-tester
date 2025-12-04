# Makefile for the OGC API Processes patterns tester

.PHONY: help install install-dev test lint format clean build docs run-example

# Variables
PYTHON = python3
PIP = pip3
PACKAGE_NAME = ogc_patterns_tester

help:  ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	$(PIP) install -e .

install-dev:  ## Install the package with development dependencies
	$(PIP) install -e ".[dev,test]"

test:  ## Run tests
	$(PYTHON) -m pytest tests/ -v

test-coverage:  ## Run tests with coverage
	$(PYTHON) -m pytest tests/ --cov=src/$(PACKAGE_NAME) --cov-report=html --cov-report=term

lint:  ## Check code with flake8 and mypy
	$(PYTHON) -m flake8 src/$(PACKAGE_NAME)/
	$(PYTHON) -m mypy src/$(PACKAGE_NAME)/

format:  ## Format code with black
	$(PYTHON) -m black src/$(PACKAGE_NAME)/ tests/ examples/

format-check:  ## Check formatting without modifying
	$(PYTHON) -m black --check src/$(PACKAGE_NAME)/ tests/ examples/

clean:  ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf temp/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf site/

build:  ## Build the package
	$(PYTHON) -m build

docs:  ## Generate documentation (placeholder)
	@echo "Documentation generation not implemented yet"

# Pattern commands

run-example:  ## Run the usage example
	$(PYTHON) examples/example_usage.py

run-pattern:  ## Run a specific pattern (usage: make run-pattern PATTERN=pattern-1)
	$(PYTHON) -m $(PACKAGE_NAME) run $(PATTERN)

run-all-patterns:  ## Run all patterns
	$(PYTHON) -m $(PACKAGE_NAME) run-all

list-patterns:  ## List available patterns
	$(PYTHON) -m $(PACKAGE_NAME) list-patterns

status:  ## Display manager status
	$(PYTHON) -m $(PACKAGE_NAME) status

cleanup:  ## Clean up all deployed patterns
	$(PYTHON) -m $(PACKAGE_NAME) cleanup-all

# Development commands

setup-dev:  ## Initial setup for development
	$(PIP) install --upgrade pip setuptools wheel
	$(MAKE) install-dev
	@echo "Development environment configured"

check-all:  ## Complete checks (tests, lint, format)
	$(MAKE) format-check
	$(MAKE) lint  
	$(MAKE) test

# Test server configuration

setup-local-server:  ## Instructions to configure a local server
	@echo "To configure a local OGC API Processes server:"
	@echo "1. Clone the eoap/oapip-application-server repository"
	@echo "2. Follow the installation instructions"
	@echo "3. Start the server on http://localhost:5000"
	@echo "4. Configure config/server_config.json if necessary"

# Development utilities

create-pattern:  ## Create a new pattern file (usage: make create-pattern PATTERN=pattern-13)
	@if [ -z "$(PATTERN)" ]; then \
		echo "Error: Specify the pattern with PATTERN=pattern-X"; \
		exit 1; \
	fi
	@echo "Creating file data/patterns/$(PATTERN).json"
	@mkdir -p data/patterns
	@echo '{\n  "aoi": "-118.985,38.432,-118.183,38.938",\n  "epsg": "EPSG:4326",\n  "item": {\n    "class": "https://raw.githubusercontent.com/eoap/schemas/main/url.yaml#URL",\n    "value": "https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC08_L2SP_042033_20231007_02_T1"\n  },\n  "bands": ["green", "nir08"]\n}' > data/patterns/$(PATTERN).json
	@echo "File created: data/patterns/$(PATTERN).json"

validate-patterns:  ## Validate all JSON pattern files
	@echo "Validating pattern files..."
	@for file in data/patterns/*.json; do \
		if [ -f "$$file" ]; then \
			echo "Validating $$file"; \
			$(PYTHON) -m json.tool "$$file" > /dev/null || echo "Error in $$file"; \
		fi \
	done
	@echo "Validation completed"

# Version and release

version:  ## Display current version
	@$(PYTHON) -c "from src.$(PACKAGE_NAME) import __version__; print(__version__)"

bump-version:  ## Update version (usage: make bump-version VERSION=0.2.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: Specify version with VERSION=x.y.z"; \
		exit 1; \
	fi
	@sed -i.bak 's/__version__ = "[^"]*"/__version__ = "$(VERSION)"/' src/$(PACKAGE_NAME)/__init__.py
	@sed -i.bak 's/version = "[^"]*"/version = "$(VERSION)"/' pyproject.toml
	@rm -f src/$(PACKAGE_NAME)/__init__.py.bak pyproject.toml.bak
	@echo "Version updated to $(VERSION)"

# Default configuration
.DEFAULT_GOAL := help