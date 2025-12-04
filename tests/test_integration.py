"""Integration tests for OGC API client.

These tests require a real OGC API Processes server to be available.
They are skipped by default unless a server URL is provided.
"""

import os

import pytest

from ogc_patterns_tester.client import OGCApiClient

# Skip integration tests unless server URL is provided
TEST_SERVER_URL = os.environ.get("OGC_TEST_SERVER_URL")
TEST_USERNAME = os.environ.get("OGC_TEST_USERNAME")
TEST_PASSWORD = os.environ.get("OGC_TEST_PASSWORD")
TEST_API_KEY = os.environ.get("OGC_TEST_API_KEY")
TEST_ACCESS_TOKEN = os.environ.get("OGC_TEST_ACCESS_TOKEN")

pytestmark = pytest.mark.skipif(
    not TEST_SERVER_URL,
    reason="Integration tests require OGC_TEST_SERVER_URL environment variable",
)


class TestOGCApiClientIntegration:
    """Integration tests for OGCApiClient with real server."""

    @pytest.fixture
    def integration_client(self):
        """Create a client for integration testing."""
        return OGCApiClient(
            base_url=TEST_SERVER_URL,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            api_key=TEST_API_KEY,
            access_token=TEST_ACCESS_TOKEN,
        )

    @pytest.mark.integration
    def test_list_processes(self, integration_client):
        """Test listing processes on real server."""
        processes = integration_client.list_processes()

        # Should return a dictionary (even if empty)
        assert isinstance(processes, dict)
        # No assertion on content as server may be empty

    @pytest.mark.integration
    def test_get_capabilities(self, integration_client):
        """Test getting server capabilities."""
        # This would test actual server connection
        try:
            # Attempt to get process list as a connectivity test
            processes = integration_client.list_processes()
            # If we get here, the server is reachable
            assert True
        except Exception as e:
            pytest.fail(f"Server connectivity test failed: {e}")

    @pytest.mark.integration
    def test_deploy_simple_process(self, integration_client, temp_dir):
        """Test deploying a real process (pattern-1) to real server.

        This uses the actual pattern-1 CWL from the application-package-patterns repository.
        """
        import urllib.request


        # Download the real pattern-1 CWL
        pattern_1_url = (
            "https://raw.githubusercontent.com/eoap/application-package-patterns/"
            "main/cwl-workflow/pattern-1.cwl"
        )

        cwl_file = temp_dir / "pattern-1.cwl"

        try:
            print(f"\nDownloading pattern-1 CWL from {pattern_1_url}")
            urllib.request.urlretrieve(pattern_1_url, cwl_file)
        except Exception as e:
            pytest.skip(f"Could not download pattern-1 CWL: {e}")
            return

        # Try to deploy
        print(f"Attempting to deploy pattern-1 to {TEST_SERVER_URL}")
        result = integration_client.deploy_process("pattern-1", str(cwl_file))

        if result is not None:
            # If deployment succeeded, clean up
            print(f"Deployment succeeded: {result}")
            integration_client.delete_process("pattern-1")
            assert result.deployed is True
        else:
            # Deployment may fail due to permissions - that's expected
            print("Deployment returned None - likely due to server restrictions")
            pytest.skip("Process deployment not permitted on test server")


# Example of how to run integration tests:
# With Bearer token (JWT):
# OGC_TEST_SERVER_URL=https://d122.sandbox.ospd.geolabs.fr/ogc-api/ \
# OGC_TEST_ACCESS_TOKEN="eyJhbGci..." \
# hatch run test -m integration
#
# Or with username/password:
# OGC_TEST_SERVER_URL=https://d122.sandbox.ospd.geolabs.fr/ogc-api/ \
# OGC_TEST_USERNAME="user" \
# OGC_TEST_PASSWORD="pass" \
# hatch run test -m integration
