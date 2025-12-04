"""Tests for the OGC API client."""

from unittest.mock import MagicMock, Mock, patch

import yaml

from ogc_patterns_tester.client import OGCApiClient
from ogc_patterns_tester.models import ProcessInfo


class TestOGCApiClient:
    """Test cases for OGCApiClient class."""

    def test_client_initialization(self, server_config):
        """Test client initialization with configuration."""
        # Mock the ogc-api-client components
        with patch(
            "ogc_patterns_tester.client.Configuration"
        ) as mock_config_class, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class:

            mock_config = Mock()
            mock_config.username = server_config.username
            mock_config.password = server_config.password
            mock_config_class.return_value = mock_config

            client = OGCApiClient(
                base_url=server_config.base_url,
                username=server_config.username,
                password=server_config.password,
                timeout=server_config.timeout,
            )

            assert client.base_url == server_config.base_url.rstrip("/")
            assert client.timeout == server_config.timeout
            assert client.configuration.username == server_config.username
            assert client.configuration.password == server_config.password

    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key."""
        api_key = "test_api_key_123"

        # Mock the ogc-api-client components
        with patch(
            "ogc_patterns_tester.client.Configuration"
        ) as mock_config_class, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class:

            mock_config = Mock()
            mock_config.api_key = {"bearerAuth": api_key}
            mock_config.api_key_prefix = {"bearerAuth": "Bearer"}
            mock_config_class.return_value = mock_config

            client = OGCApiClient(
                base_url="https://test.example.com/ogc-api", api_key=api_key
            )

            assert client.configuration.api_key["bearerAuth"] == api_key
            assert client.configuration.api_key_prefix["bearerAuth"] == "Bearer"

    def test_deploy_process_success(self, sample_cwl_content, temp_dir):
        """Test successful process deployment."""
        # Setup
        cwl_file = temp_dir / "test.cwl"
        cwl_file.write_text(yaml.dump(sample_cwl_content))

        # Mock the ogc-api-client components to avoid real network calls
        with patch("ogc_patterns_tester.client.Configuration") as mock_config, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class:

            # Setup mock for call_api
            mock_api_client = MagicMock()
            mock_response = Mock()
            mock_response.status = 201
            mock_response.read = Mock()
            mock_api_client.call_api.return_value = mock_response
            mock_api_client.param_serialize.return_value = (
                "POST",
                "/processes",
                {},
                [],
                {},
                "",
                [],
                {},
                [],
                {},
            )
            mock_api_client_class.return_value = mock_api_client

            client = OGCApiClient(base_url="https://test.example.com/ogc-api")

            # Execute
            result = client.deploy_process("test-process", str(cwl_file))

            # Verify
            assert result is not None
            assert isinstance(result, ProcessInfo)
            assert result.process_id == "test-process"
            assert result.deployed is True
            mock_api_client.param_serialize.assert_called_once()
            mock_api_client.call_api.assert_called_once()

    def test_deploy_process_http_error(self, temp_dir, sample_cwl_content):
        """Test process deployment with HTTP error."""
        # Setup
        cwl_file = temp_dir / "test.cwl"
        cwl_file.write_text(yaml.dump(sample_cwl_content))

        # Mock the ogc-api-client components
        with patch("ogc_patterns_tester.client.Configuration") as mock_config, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class:

            # Setup mock for call_api returning error status
            mock_api_client = MagicMock()
            mock_response = Mock()
            mock_response.status = 403
            mock_response.read = Mock()
            mock_api_client.call_api.return_value = mock_response
            mock_api_client.param_serialize.return_value = (
                "POST",
                "/processes",
                {},
                [],
                {},
                "",
                [],
                {},
                [],
                {},
            )
            mock_api_client_class.return_value = mock_api_client

            client = OGCApiClient(base_url="https://test.example.com/ogc-api")

            # Execute
            result = client.deploy_process("test-process", str(cwl_file))

            # Verify
            assert result is None

    def test_deploy_process_file_not_found(self):
        """Test process deployment with missing CWL file."""
        # Mock the ogc-api-client components
        with patch("ogc_patterns_tester.client.Configuration") as mock_config, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client:

            client = OGCApiClient(base_url="https://test.example.com/ogc-api")

            result = client.deploy_process("test-process", "/nonexistent/file.cwl")

            assert result is None

    def test_execute_process_success(self):
        """Test successful process execution."""
        # Mock the ogc-api-client components
        with patch("ogc_patterns_tester.client.Configuration") as mock_config, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class:

            # Setup mock for call_api
            mock_api_client = MagicMock()
            mock_response = Mock()
            mock_response.status = 201
            mock_response.data = b'{"jobID": "test-job-123", "status": "accepted"}'
            mock_response.read = Mock()
            # Mock getheader to return Location header
            mock_response.getheader = Mock(
                return_value="https://test.example.com/jobs/test-job-123"
            )
            mock_response.getheaders = Mock(
                return_value=[
                    ("Location", "https://test.example.com/jobs/test-job-123")
                ]
            )

            mock_api_client.call_api.return_value = mock_response
            mock_api_client.param_serialize.return_value = (
                "POST",
                "/processes/test-process/execution",
                {},
                [],
                {},
                {},
                [],
                {},
                [],
                {},
            )

            # Mock response_deserialize to return job info
            mock_job_response = Mock()
            mock_job_response.job_id = "test-job-123"
            mock_api_client.response_deserialize.return_value = mock_job_response

            mock_api_client_class.return_value = mock_api_client

            client = OGCApiClient(base_url="https://test.example.com/ogc-api")

            # Execute
            result = client.execute_process("test-process", {"input": "test"})

            # Verify
            assert result is not None
            assert result.job_id == "test-job-123"
            assert result.process_id == "test-process"

    def test_wait_for_job_completion_success(self):
        """Test waiting for job completion."""
        # Mock the ogc-api-client components
        with patch("ogc_patterns_tester.client.Configuration") as mock_config, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class, patch(
            "ogc_patterns_tester.client.StatusApi"
        ) as mock_status_api_class:

            # Setup mock StatusApi
            mock_status_response = Mock()
            mock_status_response.status = "successful"
            mock_status_response.process_id = "test-process"
            mock_status_response.progress = 100
            mock_status_response.message = "Job completed"

            mock_status_api = Mock()
            mock_status_api.get_status.return_value = mock_status_response
            mock_status_api_class.return_value = mock_status_api

            client = OGCApiClient(base_url="https://test.example.com/ogc-api")

            # Execute
            result = client.wait_for_job_completion("test-job-123", timeout=1)

            # Verify
            assert result is not None
            assert result.job_id == "test-job-123"
            assert result.status.value == "successful"

    def test_delete_process_success(self):
        """Test successful process deletion."""
        # Mock the ogc-api-client components
        with patch("ogc_patterns_tester.client.Configuration") as mock_config, patch(
            "ogc_patterns_tester.client.ApiClient"
        ) as mock_api_client_class:

            # Setup mock for call_api
            mock_api_client = MagicMock()

            # Mock response for list_jobs (returns empty list - no jobs)
            mock_jobs_response = Mock()
            mock_jobs_response.status = 200
            mock_jobs_response.data = '{"jobs": []}'

            # Mock response for delete_process
            mock_delete_response = Mock()
            mock_delete_response.status = 204

            # Set up call_api to return different responses based on the call
            mock_api_client.call_api.side_effect = [
                mock_jobs_response,
                mock_delete_response,
            ]
            mock_api_client_class.return_value = mock_api_client

            client = OGCApiClient(base_url="https://test.example.com/ogc-api")

            # Execute
            result = client.delete_process("test-process")

            # Verify
            assert result is True
            assert (
                mock_api_client.call_api.call_count == 2
            )  # list_jobs + delete_process

    def test_authentication_headers_basic_auth(self):
        """Test basic authentication header generation."""
        client = OGCApiClient(
            base_url="https://test.example.com/ogc-api",
            username="testuser",
            password="testpass",
        )

        # Basic auth should be configured in the configuration
        assert client.configuration.username == "testuser"
        assert client.configuration.password == "testpass"

    def test_authentication_headers_api_key(self):
        """Test API key authentication header generation."""
        client = OGCApiClient(
            base_url="https://test.example.com/ogc-api", api_key="test-api-key-123"
        )

        assert client.configuration.api_key["bearerAuth"] == "test-api-key-123"
        assert client.configuration.api_key_prefix["bearerAuth"] == "Bearer"
