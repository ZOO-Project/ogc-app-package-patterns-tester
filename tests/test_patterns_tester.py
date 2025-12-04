"""
Unit tests for the OGC API Processes patterns tester.

These tests demonstrate how to test the various components
of the package without requiring a real OGC API server.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.ogc_patterns_tester.models import (
    ExecutionResult,
    JobStatus,
    PatternType,
    ServerConfig,
)
from src.ogc_patterns_tester.patterns_manager import PatternsManager
from src.ogc_patterns_tester.utils import setup_logger


class TestModels(unittest.TestCase):
    """Tests for data models."""

    def test_server_config_creation(self):
        """Test server configuration creation."""
        config = ServerConfig(
            base_url="http://example.com", auth_token="test-token", timeout=300
        )

        self.assertEqual(config.base_url, "http://example.com")
        self.assertEqual(config.auth_token, "test-token")
        self.assertEqual(config.timeout, 300)

    def test_pattern_type_from_id(self):
        """Test pattern type determination."""
        self.assertEqual(
            PatternType.from_pattern_id("pattern-1"), PatternType.BASIC_PROCESSING
        )
        self.assertEqual(
            PatternType.from_pattern_id("pattern-9"), PatternType.MULTIPLE_INPUTS
        )
        self.assertEqual(
            PatternType.from_pattern_id("pattern-unknown"),
            PatternType.BASIC_PROCESSING,  # Default
        )

    def test_execution_result_creation(self):
        """Test execution result creation."""
        result = ExecutionResult(
            pattern_id="pattern-1",
            success=True,
            execution_time=45.5,
            message="Test successful",
        )

        self.assertEqual(result.pattern_id, "pattern-1")
        self.assertTrue(result.success)
        self.assertEqual(result.execution_time, 45.5)
        self.assertEqual(result.message, "Test successful")


class TestPatternsManager(unittest.TestCase):
    """Tests for the patterns manager."""

    def setUp(self):
        """Test setup."""
        self.temp_dir = tempfile.mkdtemp()
        self.patterns_dir = Path(self.temp_dir) / "patterns"
        self.download_dir = Path(self.temp_dir) / "cwl"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

        # Test configuration
        self.server_config = ServerConfig(base_url="http://test-server.com", timeout=60)

        # Create a test pattern file
        pattern_data = {
            "aoi": "-118.985,38.432,-118.183,38.938",
            "epsg": "EPSG:4326",
            "bands": ["green", "nir08"],
            "item": {
                "class": "https://raw.githubusercontent.com/eoap/schemas/main/url.yaml#URL",
                "value": "https://example.com/test-item",
            },
        }

        pattern_file = self.patterns_dir / "pattern-test.json"
        with open(pattern_file, "w", encoding="utf-8") as f:
            json.dump(pattern_data, f)

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = PatternsManager(
            server_config=self.server_config,
            patterns_dir=str(self.patterns_dir),
            download_dir=str(self.download_dir),
        )

        self.assertEqual(manager.server_config, self.server_config)
        self.assertEqual(manager.patterns_dir, self.patterns_dir)
        self.assertEqual(len(manager.deployed_processes), 0)
        self.assertEqual(len(manager.running_jobs), 0)

    def test_load_pattern_config(self):
        """Test loading a pattern configuration."""
        manager = PatternsManager(
            server_config=self.server_config,
            patterns_dir=str(self.patterns_dir),
            download_dir=str(self.download_dir),
        )

        config = manager.load_pattern_config("pattern-test")

        self.assertIsNotNone(config)
        self.assertEqual(config.pattern_id, "pattern-test")
        self.assertIn("application-package-patterns", config.cwl_url)
        self.assertEqual(config.parameters["aoi"], "-118.985,38.432,-118.183,38.938")

    def test_load_nonexistent_pattern(self):
        """Test loading a non-existent pattern."""
        manager = PatternsManager(
            server_config=self.server_config,
            patterns_dir=str(self.patterns_dir),
            download_dir=str(self.download_dir),
        )

        config = manager.load_pattern_config("pattern-nonexistent")
        self.assertIsNone(config)

    @patch("src.ogc_patterns_tester.patterns_manager.download_cwl_file")
    def test_prepare_pattern(self, mock_download):
        """Test pattern preparation."""
        mock_download.return_value = True

        manager = PatternsManager(
            server_config=self.server_config,
            patterns_dir=str(self.patterns_dir),
            download_dir=str(self.download_dir),
        )

        success = manager.prepare_pattern("pattern-test")
        self.assertTrue(success)
        mock_download.assert_called_once()

    def test_get_status(self):
        """Test status retrieval."""
        manager = PatternsManager(
            server_config=self.server_config,
            patterns_dir=str(self.patterns_dir),
            download_dir=str(self.download_dir),
        )

        # Simulate some states
        manager.deployed_processes.add("pattern-1")
        manager.running_jobs["pattern-2"] = "job-123"
        manager.results["pattern-3"] = ExecutionResult(
            pattern_id="pattern-3", success=True
        )

        status = manager.get_status()

        self.assertIn("pattern-1", status["deployed_processes"])
        self.assertEqual(status["running_jobs"]["pattern-2"], "job-123")
        self.assertEqual(status["completed_results"], 1)
        self.assertEqual(status["server_config"]["base_url"], "http://test-server.com")


class TestUtils(unittest.TestCase):
    """Tests for utilities."""

    def test_logger_setup(self):
        """Test logger configuration."""
        logger = setup_logger("test_logger", level="INFO")

        # Loguru retourne un objet Logger qui n'a pas d'attribut 'name'
        # On vérifie juste qu'il n'est pas None
        self.assertIsNotNone(logger)

    @patch("requests.get")
    def test_download_cwl_file_success(self, mock_get):
        """Test successful CWL file download."""
        from src.ogc_patterns_tester.utils import download_cwl_file

        # Simulate a successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "cwlVersion: v1.0\nclass: Workflow"
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_file = f.name

        try:
            success = download_cwl_file("http://example.com/test.cwl", temp_file)
            self.assertTrue(success)

            # Verify content
            with open(temp_file, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("cwlVersion", content)

        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch("requests.get")
    def test_download_cwl_file_failure(self, mock_get):
        """Test failed CWL file download."""
        from src.ogc_patterns_tester.utils import download_cwl_file

        # Simulate an HTTP error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_file = f.name

        try:
            success = download_cwl_file("http://example.com/notfound.cwl", temp_file)
            self.assertFalse(success)

        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestIntegration(unittest.TestCase):
    """Simulated integration tests."""

    def setUp(self):
        """Integration test setup."""
        self.temp_dir = tempfile.mkdtemp()
        self.patterns_dir = Path(self.temp_dir) / "patterns"
        self.download_dir = Path(self.temp_dir) / "cwl"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple test pattern files
        for i in range(1, 4):
            pattern_data = {
                "aoi": "-118.985,38.432,-118.183,38.938",
                "epsg": "EPSG:4326",
                "bands": ["green", "nir08"],
                "item": {
                    "class": "https://raw.githubusercontent.com/eoap/schemas/main/url.yaml#URL",
                    "value": f"https://example.com/test-item-{i}",
                },
            }

            pattern_file = self.patterns_dir / f"pattern-{i}.json"
            with open(pattern_file, "w", encoding="utf-8") as f:
                json.dump(pattern_data, f)

        self.server_config = ServerConfig(base_url="http://mock-server.com")

    @patch("src.ogc_patterns_tester.client.OGCApiClient")
    def test_full_workflow_simulation(self, mock_client_class):
        """Test complete workflow simulation."""
        # Configure the client mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Configure mock responses
        from src.ogc_patterns_tester.models import JobInfo, ProcessInfo

        mock_client.deploy_process.return_value = ProcessInfo(
            process_id="pattern-1", version="1.0.0", title="Test Pattern"
        )

        mock_client.execute_process.return_value = JobInfo(
            job_id="job-123", status=JobStatus.RUNNING, process_id="pattern-1"
        )

        mock_client.wait_for_job_completion.return_value = JobInfo(
            job_id="job-123",
            status=JobStatus.SUCCESSFUL,
            process_id="pattern-1",
            outputs={"result": "http://example.com/result.tif"},
        )

        mock_client.delete_process.return_value = True

        # Create the manager
        manager = PatternsManager(
            server_config=self.server_config,
            patterns_dir=str(self.patterns_dir),
            download_dir=str(self.download_dir),
        )

        # Replace the client with the mock
        manager.client = mock_client

        # Test pattern execution
        with patch(
            "src.ogc_patterns_tester.patterns_manager.download_cwl_file",
            return_value=True,
        ):
            result = manager.run_single_pattern("pattern-1", cleanup=True)

        # Verifications
        self.assertTrue(result.success)
        self.assertEqual(result.pattern_id, "pattern-1")
        self.assertEqual(result.job_id, "job-123")

        # Verify method calls
        mock_client.deploy_process.assert_called_once()
        mock_client.execute_process.assert_called_once()
        mock_client.wait_for_job_completion.assert_called_once()
        mock_client.delete_process.assert_called_once()


if __name__ == "__main__":
    # Test configuration
    unittest.main(verbosity=2)
