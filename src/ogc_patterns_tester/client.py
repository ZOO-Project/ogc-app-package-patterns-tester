# Copyright 2025 EOEPCA Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""OGC API Processes client wrapper for simplifying pattern operations.

This module provides a simplified interface for deploying, executing,
and managing OGC processes using the ogc-api-client module.
"""

import base64
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import click

# Import ogc-api-client components
import yaml
from ogc_api_client.api.capabilities_api import CapabilitiesApi
from ogc_api_client.api.execute_api import ExecuteApi
from ogc_api_client.api.process_description_api import ProcessDescriptionApi
from ogc_api_client.api.process_list_api import ProcessListApi
from ogc_api_client.api.result_api import ResultApi
from ogc_api_client.api.status_api import StatusApi
from ogc_api_client.api_client import ApiClient
from ogc_api_client.configuration import Configuration
from ogc_api_client.rest import ApiException

from .models import JobInfo, JobStatus, ProcessInfo
from .utils import setup_logger


class OGCApiClient:
    """
    A client for interacting with OGC API Processes endpoints using ogc-api-client.
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: int = 600,
    ):
        """
        Initialize the OGC API client.

        Args:
            base_url: Base URL of the OGC API Processes endpoint
            username: Optional username for Basic authentication
            password: Optional password for Basic authentication
            api_key: Optional API key
            access_token: Optional Bearer token
            timeout: Request timeout in seconds (default: 600)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = setup_logger(__name__)

        # Configure the API client
        self.configuration = Configuration(host=self.base_url)

        # Set up authentication
        if username and password:
            self.configuration.username = username
            self.configuration.password = password
        elif access_token:
            self.configuration.access_token = access_token
        elif api_key:
            self.configuration.api_key = {"bearerAuth": api_key}
            self.configuration.api_key_prefix = {"bearerAuth": "Bearer"}

        self.api_client = ApiClient(self.configuration)

        # Initialize API instances
        self.capabilities_api = CapabilitiesApi(self.api_client)
        self.process_list_api = ProcessListApi(self.api_client)
        self.process_description_api = ProcessDescriptionApi(self.api_client)
        self.execute_api = ExecuteApi(self.api_client)
        self.status_api = StatusApi(self.api_client)
        self.result_api = ResultApi(self.api_client)

    def _get_client_with_timeout(self, timeout_seconds: int = 5) -> ApiClient:
        """
        Create a temporary API client with a short timeout for cleanup operations.

        Args:
            timeout_seconds: Timeout in seconds

        Returns:
            ApiClient with specified timeout
        """
        temp_config = Configuration(host=self.base_url)

        # Copy authentication settings
        if self.configuration.username and self.configuration.password:
            temp_config.username = self.configuration.username
            temp_config.password = self.configuration.password
        elif self.configuration.access_token:
            temp_config.access_token = self.configuration.access_token
        elif self.configuration.api_key:
            temp_config.api_key = self.configuration.api_key.copy()
            temp_config.api_key_prefix = self.configuration.api_key_prefix.copy()

        # Set timeout
        temp_config.timeout = timeout_seconds

        return ApiClient(temp_config)

    def _add_auth_header(self, headers: Dict[str, str]) -> None:
        """
        Add authentication header to the provided headers dictionary.

        Args:
            headers: Dictionary of headers to modify in-place
        """
        if self.configuration.username and self.configuration.password:
            credentials = base64.b64encode(
                f"{self.configuration.username}:{self.configuration.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif self.configuration.access_token:
            headers["Authorization"] = f"Bearer {self.configuration.access_token}"
        elif self.configuration.api_key and "bearerAuth" in self.configuration.api_key:
            prefix = self.configuration.api_key_prefix.get("bearerAuth", "Bearer")
            headers["Authorization"] = (
                f'{prefix} {self.configuration.api_key["bearerAuth"]}'
            )

    def deploy_process(
        self, process_id: str, cwl_file_path: str
    ) -> Optional[ProcessInfo]:
        """
        Deploy a CWL process to the OGC API Processes endpoint.

        Args:
            process_id: Unique identifier for the process
            cwl_file_path: Path to the CWL workflow file

        Returns:
            ProcessInfo if deployment successful, None otherwise
        """
        try:
            # Read CWL content
            cwl_path = Path(cwl_file_path)
            if not cwl_path.exists():
                self.logger.error(f"CWL file not found: {cwl_file_path}")
                return None

            with open(cwl_path, encoding="utf-8") as f:
                if cwl_path.suffix.lower() in [".yml", ".yaml", ".cwl"]:
                    # CWL files are typically in YAML format
                    cwl_content = yaml.safe_load(f)
                else:
                    # Try JSON first, fallback to YAML
                    try:
                        f.seek(0)
                        cwl_content = json.load(f)
                    except json.JSONDecodeError:
                        f.seek(0)
                        cwl_content = yaml.safe_load(f)

            self.logger.info(f"Deploying process '{process_id}' to {self.base_url}")

            # Prepare headers for deployment
            headers = {
                "Content-Type": "application/cwl+yaml",
                "Accept": "application/json",
            }

            # Add authentication
            self._add_auth_header(headers)

            # Convert CWL to YAML format
            cwl_yaml = yaml.dump(cwl_content, default_flow_style=False)

            # Use api_client.param_serialize() + call_api() for consistency with ogc-api-client architecture
            _param = self.api_client.param_serialize(
                method="POST",
                resource_path="/processes",
                path_params={},
                query_params=[],
                header_params=headers,
                body=cwl_yaml,
                post_params=[],
                files={},
                auth_settings=[],
                collection_formats={},
            )

            # Call the API
            response_data = self.api_client.call_api(
                *_param, _request_timeout=self.timeout
            )

            response_data.read()

            # Check response status
            if response_data.status in [200, 201]:
                self.logger.info(f"✓ Process '{process_id}' deployed successfully")
                return ProcessInfo(
                    process_id=process_id,
                    title=cwl_content.get("label", process_id),
                    deployed=True,
                )
            elif response_data.status == 409:
                # Process already exists - treat as success
                self.logger.info(f"✓ Process '{process_id}' already exists on server")
                return ProcessInfo(
                    process_id=process_id,
                    title=cwl_content.get("label", process_id),
                    deployed=True,
                )
            else:
                error_body = (
                    response_data.data.decode("utf-8")
                    if response_data.data
                    else "No error details"
                )
                self.logger.error(
                    f"HTTP error deploying process '{process_id}': {response_data.status}"
                )
                self.logger.error(f"Error details: {error_body}")
                return None
        except ApiException as e:
            self.logger.error(
                f"API error deploying process '{process_id}': {e.status} - {e.reason}"
            )
            if e.body:
                self.logger.error(f"Error details: {e.body}")
            return None
        except Exception as e:
            self.logger.error(f"Error deploying process '{process_id}': {e}")
            return None

    def execute_process(
        self, process_id: str, parameters: Dict[str, Any]
    ) -> Optional[JobInfo]:
        """
        Execute a deployed process.

        Args:
            process_id: The ID of the process to execute
            parameters: Process input parameters

        Returns:
            JobInfo if successful, None otherwise

        Note:
            Uses api_client.param_serialize() + call_api() instead of ExecuteApi directly.
            This is necessary because Pydantic's strict oneOf validation in ExecuteInputsValue
            is incompatible with OGC's flexible input structures like {"mediaType": "...", "value": "..."}.
            This approach still uses ogc-api-client infrastructure while bypassing strict validation.
        """
        try:
            self.logger.info(f"Executing process '{process_id}'...")

            # Prepare the execute request body as raw JSON
            execute_body = {"inputs": parameters, "response": "document"}

            # Prepare headers for async execution and authentication
            headers = {
                "Prefer": "respond-async",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Add authentication
            self._add_auth_header(headers)

            # Use api_client.param_serialize to prepare the request
            self.logger.info(f"Calling API for process '{process_id}'...")

            _param = self.api_client.param_serialize(
                method="POST",
                resource_path=f"/processes/{process_id}/execution",
                path_params={"processID": process_id},
                query_params=[],
                header_params=headers,
                body=execute_body,
                post_params=[],
                files={},
                auth_settings=[],
                collection_formats={},
            )

            # Call the API
            response_data = self.api_client.call_api(*_param, _request_timeout=None)

            response_data.read()

            # Deserialize using ExecuteApi's response types
            response = self.api_client.response_deserialize(
                response_data=response_data,
                response_types_map={
                    "200": "Execute200Response",
                    "201": "StatusInfo",
                    "404": "Exception",
                    "500": "Exception",
                },
            )

            # Log response details
            self.logger.info(f"Response status: {response_data.status}")

            # Extract job information from response
            job_id = None

            # Try to get job ID from Location header
            location_header = response_data.getheader("Location")
            if location_header:
                job_id = location_header.split("/")[-1]
                self.logger.debug(f"Job ID from Location header: {job_id}")

            # Try to get job ID from response data
            if not job_id and response.data:
                if hasattr(response.data, "job_id"):
                    job_id = response.data.job_id
                elif hasattr(response.data, "jobID"):
                    job_id = response.data.jobID
                if job_id:
                    self.logger.debug(f"Job ID from response body: {job_id}")

            if job_id:
                self.logger.info(f"✓ Job {job_id} started for process '{process_id}'")
                return JobInfo(
                    job_id=job_id, process_id=process_id, status=JobStatus.RUNNING
                )
            else:
                self.logger.warning(
                    f"No job ID found in response for process '{process_id}'"
                )
                return None

        except ApiException as e:
            self.logger.error(
                f"API error executing process '{process_id}': {e.status} - {e.reason}"
            )
            if e.body:
                self.logger.error(f"Error details: {e.body}")
            return None
        except Exception as e:
            self.logger.error(f"Error executing process '{process_id}': {e}")
            self.logger.error(f"Exception type: {type(e)}")
            if hasattr(e, "__dict__"):
                self.logger.error(f"Exception details: {e.__dict__}")
            return None

    def wait_for_job_completion(
        self, job_id: str, timeout: int = 1800
    ) -> Optional[JobInfo]:
        """
        Wait for a job to complete by polling its status.

        Args:
            job_id: Job identifier
            timeout: Maximum wait time in seconds (default: 30 minutes, use 0 for unlimited)

        Returns:
            Final JobInfo or None if timeout/error
        """
        start_time = time.time()
        poll_interval = 10
        last_status_log_time = start_time
        last_status = None
        status_log_interval = 60  # Log status every 60 seconds if unchanged

        timeout_msg = "no timeout" if timeout == 0 else f"{timeout}s timeout"
        self.logger.info(f"Monitoring job '{job_id}' ({timeout_msg})...")

        # Prepare headers
        headers = {}
        self._add_auth_header(headers)

        while timeout == 0 or time.time() - start_time < timeout:
            try:
                # Get job status
                # self.status_api._request_auth = headers
                self.logger.debug(f"Checking status for job '{job_id}'...")
                status_response = self.status_api.get_status(
                    job_id=job_id, _headers=headers
                )

                # Extract status information
                status_str = getattr(status_response, "status", "unknown")

                try:
                    status = JobStatus(status_str.lower())
                except ValueError:
                    status = JobStatus.UNKNOWN

                job_info = JobInfo(
                    job_id=job_id,
                    process_id=getattr(status_response, "process_id", ""),
                    status=status,
                    progress=getattr(status_response, "progress", None),
                    message=getattr(status_response, "message", None),
                    outputs=getattr(status_response, "outputs", None),
                )

                # Check if job is complete
                if status in [JobStatus.SUCCESSFUL, JobStatus.FAILED]:
                    elapsed_time = time.time() - start_time
                    self.logger.info(
                        f"Job '{job_id}' completed with status: {status.value} after {elapsed_time:.1f}s"
                    )
                    return job_info

                # Log status only if it changed or every 60 seconds
                current_time = time.time()
                elapsed_time = current_time - start_time
                should_log = (
                    status != last_status
                    or (current_time - last_status_log_time) >= status_log_interval
                )

                if should_log:
                    self.logger.info(
                        f"Job '{job_id}' status: {status.value} (elapsed: {elapsed_time:.1f}s)"
                    )
                    last_status = status
                    last_status_log_time = current_time

                time.sleep(poll_interval)

            except (KeyboardInterrupt, click.Abort):
                # Re-raise interruption signals to be handled by the CLI for cleanup
                raise
            except ApiException as e:
                self.logger.error(
                    f"API error checking job status: {e.status} - {e.reason}"
                )
                return None
            except Exception as e:
                self.logger.error(f"Error checking job status: {e}")
                return None

        # Timeout reached (only when timeout > 0)
        self.logger.warning(
            f"Timeout reached for job '{job_id}'. The job may still be running on the server."
        )
        self.logger.info(
            f"You can check the job status later at: {self.base_url}/jobs/{job_id}"
        )
        self.logger.info(
            "Consider increasing the timeout or checking the job status manually."
        )
        return None

    def list_jobs(
        self, process_id: Optional[str] = None, use_timeout: bool = False
    ) -> list:
        """
        List jobs, optionally filtered by process ID.

        Args:
            process_id: Optional process identifier to filter jobs
            use_timeout: If True, use a client with short timeout (for cleanup)

        Returns:
            List of job IDs
        """
        try:
            # Use client with timeout for cleanup operations
            client = (
                self._get_client_with_timeout(5) if use_timeout else self.api_client
            )

            # Prepare headers
            headers = {"Accept": "application/json", "Connection": "close"}
            self._add_auth_header(headers)

            # Construct URL with query params
            if process_id:
                url = f"{self.base_url}/jobs?processID={process_id}"
            else:
                url = f"{self.base_url}/jobs"

            kwargs = {"header_params": headers}
            if use_timeout:
                kwargs["_request_timeout"] = 5

            response = client.call_api("GET", url, **kwargs)

            # Read response to populate response.data
            response.read()

            if response.status == 200:
                import json

                raw = response.data
                if raw is None:
                    self.logger.warning("Response data is None")
                    return []
                if isinstance(raw, (bytes, bytearray)):
                    try:
                        text = raw.decode("utf-8")
                    except Exception as e:
                        self.logger.error(f"Failed to decode response: {e}")
                        return []
                elif isinstance(raw, str):
                    text = raw
                else:
                    self.logger.warning(f"Unexpected response type: {type(raw)}")
                    return []

                try:
                    data = json.loads(text)
                except Exception as e:
                    self.logger.error(f"Failed to parse JSON: {e}")
                    return []

                # Extract job IDs from the response
                jobs = []
                if (
                    isinstance(data, dict)
                    and "jobs" in data
                    and isinstance(data["jobs"], list)
                ):
                    jobs = [
                        job.get("jobID")
                        for job in data["jobs"]
                        if isinstance(job, dict) and "jobID" in job
                    ]
                    self.logger.info(
                        f"Found {len(jobs)} jobs for process '{process_id}'"
                    )
                else:
                    self.logger.warning(f"Unexpected data structure: {data}")
                return jobs
            else:
                self.logger.warning(f"List jobs returned status {response.status}")
                return []
        except (KeyboardInterrupt, click.Abort):
            # During cleanup, don't re-raise - just return empty list
            self.logger.warning("Job listing interrupted - returning empty list")
            return []
        except Exception as e:
            self.logger.error(f"Error listing jobs: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return []

    def delete_job(self, job_id: str, use_timeout: bool = False) -> bool:
        """
        Delete a specific job.

        Args:
            job_id: Job identifier
            use_timeout: If True, use a client with short timeout (for cleanup)

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting job '{job_id}'...")

        # Use client with timeout for cleanup operations
        client = self._get_client_with_timeout(5) if use_timeout else self.api_client

        # Prepare headers
        headers = {"Accept": "application/json", "Connection": "close"}
        self._add_auth_header(headers)

        kwargs = {"header_params": headers}
        if use_timeout:
            kwargs["_request_timeout"] = 5

        response = client.call_api("DELETE", f"{self.base_url}/jobs/{job_id}", **kwargs)

        # Read response to populate response.data
        response.read()

        success = response.status in [200, 204]
        if success:
            self.logger.info(f"Job '{job_id}' deleted successfully")
        else:
            self.logger.warning(
                f"Failed to delete job '{job_id}': HTTP {response.status}"
            )
        return True  # Always return True to continue cleanup

    def delete_process(self, process_id: str) -> bool:
        """
        Delete a process from the server.
        Also attempts to delete all associated jobs before removing the process.

        Args:
            process_id: Process identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting process '{process_id}'...")

            # List and delete jobs
            self.logger.info(
                f"Checking for jobs associated with process '{process_id}'..."
            )
            jobs = []
            try:
                jobs = self.list_jobs(process_id, use_timeout=True)
            except Exception as e:
                self.logger.warning(f"Error listing jobs during cleanup: {e}")
            if jobs:
                self.logger.info(f"Found {len(jobs)} job(s) to delete")
                deleted_count = 0
                for job_id in jobs:
                    try:
                        # Use timeout for cleanup operations
                        if self.delete_job(job_id, use_timeout=True):
                            deleted_count += 1
                    except Exception as e:
                        self.logger.warning(f"Error deleting job '{job_id}': {e}")
                self.logger.info(f"Deleted {deleted_count}/{len(jobs)} job(s)")
            else:
                self.logger.info(f"No jobs found for process '{process_id}'")

            # Now delete the process itself
            self.logger.info(f"Attempting to delete process '{process_id}'...")

            # Prepare headers
            headers = {}
            self._add_auth_header(headers)

            # Use call_api which returns a RESTResponse object
            response = self.api_client.call_api(
                "DELETE",
                f"{self.base_url}/processes/{process_id}",
                header_params=headers,
            )

            # RESTResponse has .status, .reason, and .data attributes
            if response.status in [200, 204]:
                self.logger.info(f"✓ Process '{process_id}' deleted successfully")
                return True
            else:
                self.logger.error(
                    f"Failed to delete process '{process_id}': HTTP {response.status}"
                )
                if response.data:
                    self.logger.error(f"Response: {response.data}")
                return False

        except (KeyboardInterrupt, click.Abort):
            # Interrupted at any point during cleanup
            self.logger.warning(
                f"Cleanup interrupted. Process '{process_id}' may still exist on server."
            )
            self.logger.warning(
                f"To clean up manually: ogc-patterns-tester cleanup {process_id}"
            )
            return False
        except ApiException as e:
            self.logger.error(
                f"API error deleting process '{process_id}': {e.status} - {e.reason}"
            )
            if e.body:
                self.logger.error(f"Error details: {e.body}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting process '{process_id}': {e}")
            return False

    def list_processes(self) -> Dict[str, Any]:
        """
        List all available processes on the server.

        Returns:
            Dictionary containing process list information
        """
        try:
            self.logger.info("Retrieving process list...")

            # Prepare headers with authentication
            headers = {"Accept": "application/json"}
            self._add_auth_header(headers)

            # Get process list with explicit headers
            response = self.process_list_api.get_processes(_headers=headers)

            processes = {}
            if hasattr(response, "processes"):
                for process in response.processes:
                    processes[process.id] = {
                        "title": getattr(process, "title", ""),
                        "description": getattr(process, "description", ""),
                        "version": getattr(process, "version", ""),
                    }

            self.logger.info(f"Found {len(processes)} processes")
            return processes

        except ApiException as e:
            self.logger.error(f"API error listing processes: {e.status} - {e.reason}")
            return {}
        except Exception as e:
            self.logger.error(f"Error listing processes: {e}")
            return {}

    def get_process_description(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed description of a specific process.

        Args:
            process_id: Process identifier

        Returns:
            Process description dictionary or None
        """
        try:
            self.logger.info(f"Getting description for process '{process_id}'...")

            # Prepare headers with authentication
            headers = {"Accept": "application/json"}
            self._add_auth_header(headers)

            # Get process description with explicit headers
            response = self.process_description_api.get_process_description(
                process_id=process_id, _headers=headers
            )

            description = {
                "id": getattr(response, "id", process_id),
                "title": getattr(response, "title", ""),
                "description": getattr(response, "description", ""),
                "version": getattr(response, "version", ""),
                "inputs": getattr(response, "inputs", {}),
                "outputs": getattr(response, "outputs", {}),
            }

            return description

        except ApiException as e:
            self.logger.error(
                f"API error getting process description: {e.status} - {e.reason}"
            )
            return None
        except Exception as e:
            self.logger.error(f"Error getting process description: {e}")
            return None
