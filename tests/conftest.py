"""Test configuration and fixtures for pytest."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from ogc_patterns_tester.client import OGCApiClient
from ogc_patterns_tester.models import ServerConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def server_config():
    """Create a test server configuration.

    Can be overridden with environment variables:
    - OGC_SERVER_URL: Server base URL
    - OGC_AUTH_TOKEN: Bearer token for authentication
    """
    return ServerConfig(
        base_url=os.getenv("OGC_SERVER_URL", "https://test.example.com/ogc-api"),
        auth_token=os.getenv("OGC_AUTH_TOKEN"),
        username=(
            os.getenv("OGC_USERNAME", "test_user")
            if not os.getenv("OGC_AUTH_TOKEN")
            else None
        ),
        password=(
            os.getenv("OGC_PASSWORD", "test_pass")
            if not os.getenv("OGC_AUTH_TOKEN")
            else None
        ),
        timeout=int(os.getenv("OGC_TIMEOUT", "30")),
    )


@pytest.fixture
def mock_ogc_client():
    """Create a mock OGC API client."""
    return Mock(spec=OGCApiClient)


@pytest.fixture
def sample_cwl_content():
    """Sample CWL content for testing."""
    return {
        "cwlVersion": "v1.0",
        "class": "CommandLineTool",
        "label": "Test Process",
        "doc": "A test process for validation",
        "baseCommand": ["echo"],
        "inputs": {"message": {"type": "string", "inputBinding": {"position": 1}}},
        "outputs": {"output": {"type": "stdout"}},
        "stdout": "output.txt",
    }


@pytest.fixture
def sample_pattern_config():
    """Sample pattern configuration."""
    return {
        "pattern_id": "test-pattern-1",
        "cwl_url": "https://github.com/eoap/application-package-patterns/raw/main/cwl-workflow/test.cwl",
        "parameters": {"message": "Hello World"},
        "pattern_type": "basic_processing",
    }
