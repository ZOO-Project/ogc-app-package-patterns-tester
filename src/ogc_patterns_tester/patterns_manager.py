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

"""Main manager for orchestrating OGC API Processes pattern tests.

This module contains the PatternsManager class that coordinates the deployment,
execution and monitoring of CWL workflows on an OGC API Processes server.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import click

from .client import OGCApiClient
from .models import (
    ExecutionResult,
    JobStatus,
    PatternConfig,
    PatternType,
    ServerConfig,
    TestSummary,
)
from .utils import download_cwl_file, retry_with_backoff, setup_logger


class PatternsManager:
    """Main manager for orchestrating pattern tests."""

    def __init__(
        self,
        server_config: ServerConfig,
        patterns_dir: str = "data/patterns",
        download_dir: str = "temp/cwl",
        force_download: bool = False,
        cleanup_handler=None,
    ):
        """
        Initialize the patterns manager.

        Args:
            server_config: OGC API server configuration
            patterns_dir: Directory containing JSON parameter files
            download_dir: Temporary directory for CWL files
            force_download: Force re-download of CWL files even if they exist
            cleanup_handler: Optional cleanup handler for signal handling
        """
        self.server_config = server_config
        self.patterns_dir = Path(patterns_dir)
        self.download_dir = Path(download_dir)
        self.force_download = force_download
        self.cleanup_handler = cleanup_handler
        self.client = OGCApiClient(
            base_url=server_config.base_url,
            username=server_config.username,
            password=server_config.password,
            access_token=server_config.auth_token or server_config.api_key,
            timeout=server_config.timeout,
        )
        self.logger = setup_logger(__name__)

        # Internal state
        self.deployed_processes: Set[str] = set()
        self.running_jobs: Dict[str, str] = {}  # pattern_id -> job_id
        self.results: Dict[str, ExecutionResult] = {}

        # Create necessary directories
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def load_pattern_config(self, pattern_id: str) -> Optional[PatternConfig]:
        """
        Load pattern configuration from JSON file.

        Args:
            pattern_id: Pattern identifier (e.g., "pattern-1")

        Returns:
            Pattern configuration or None if not found
        """
        config_file = self.patterns_dir / f"{pattern_id}.json"

        if not config_file.exists():
            self.logger.error(f"Configuration file not found: {config_file}")
            return None

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            # Build CWL workflow URL
            cwl_url = (
                f"https://raw.githubusercontent.com/eoap/application-package-patterns/"
                f"main/cwl-workflow/{pattern_id}.cwl"
            )

            return PatternConfig(
                pattern_id=pattern_id,
                cwl_url=cwl_url,
                parameters=data,
                pattern_type=PatternType.from_pattern_id(pattern_id),
            )

        except Exception as e:
            self.logger.error(f"Error loading config for {pattern_id}: {e}")
            return None

    def download_pattern_cwl(self, pattern_id: str, force: bool = False) -> bool:
        """
        Download CWL workflow for a pattern.

        Args:
            pattern_id: Pattern identifier
            force: Force re-download even if file exists

        Returns:
            True if download succeeds or file already exists
        """
        config = self.load_pattern_config(pattern_id)
        if not config:
            return False

        cwl_file = self.download_dir / f"{pattern_id}.cwl"

        # Check if we need to download
        if not force and cwl_file.exists():
            self.logger.debug(f"CWL file already exists for {pattern_id}")
            return True

        # Download CWL file
        self.logger.info(
            f"Downloading CWL workflow for {pattern_id} from {config.cwl_url}"
        )
        success = download_cwl_file(config.cwl_url, str(cwl_file))

        if not success:
            self.logger.error(f"Failed to download CWL for {pattern_id}")
            return False

        self.logger.info(f"Successfully downloaded CWL for {pattern_id}")
        return True

    def prepare_pattern(self, pattern_id: str) -> bool:
        """
        Prepare a pattern for execution (download CWL if necessary).

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if preparation succeeds
        """
        # Use force_download setting from manager initialization
        return self.download_pattern_cwl(pattern_id, force=self.force_download)

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def deploy_pattern(self, pattern_id: str) -> bool:
        """
        Deploy a pattern to the OGC API Processes server.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if deployment succeeds
        """
        if not self.prepare_pattern(pattern_id):
            return False

        cwl_file = self.download_dir / f"{pattern_id}.cwl"

        try:
            self.logger.info(f"Deploying pattern {pattern_id}")
            process_info = self.client.deploy_process(pattern_id, str(cwl_file))

            if process_info:
                self.deployed_processes.add(pattern_id)
                self.logger.info(f"Pattern {pattern_id} deployed successfully")
                return True
            else:
                self.logger.error(f"Deployment failed for {pattern_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error deploying {pattern_id}: {e}")
            return False

    def execute_pattern(self, pattern_id: str) -> Optional[str]:
        """
        Execute a deployed pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Created job ID or None on error
        """
        if pattern_id not in self.deployed_processes:
            self.logger.error(f"Pattern {pattern_id} not deployed")
            return None

        config = self.load_pattern_config(pattern_id)
        if not config:
            return None

        try:
            self.logger.info(f"Executing pattern {pattern_id}")
            job_info = self.client.execute_process(pattern_id, config.parameters)

            if job_info:
                job_id = job_info.job_id
                self.running_jobs[pattern_id] = job_id
                return job_id
            else:
                self.logger.error(f"Execution failed for {pattern_id}")
                return None

        except Exception as e:
            self.logger.error(f"Error executing {pattern_id}: {e}")
            return None

    def monitor_job(self, pattern_id: str, timeout: int = 1800) -> ExecutionResult:
        """
        Monitor job execution until completion.

        Args:
            pattern_id: Pattern identifier
            timeout: Timeout in seconds (default: 30 minutes, use 0 for unlimited)

        Returns:
            Execution result
        """
        if pattern_id not in self.running_jobs:
            return ExecutionResult(
                pattern_id=pattern_id,
                success=False,
                message="No running job for this pattern",
            )

        job_id = self.running_jobs[pattern_id]

        try:
            start_time = time.time()
            final_job_info = self.client.wait_for_job_completion(job_id, timeout)
            execution_time = time.time() - start_time

            if final_job_info:
                success = final_job_info.status == JobStatus.SUCCESSFUL
                message = f"Job completed: {final_job_info.status.value}"

                result = ExecutionResult(
                    pattern_id=pattern_id,
                    job_id=job_id,
                    success=success,
                    execution_time=execution_time,
                    message=message,
                    outputs=final_job_info.outputs if success else None,
                )
            else:
                result = ExecutionResult(
                    pattern_id=pattern_id,
                    job_id=job_id,
                    success=False,
                    execution_time=execution_time,
                    message=f"Monitoring timeout after {timeout}s. Job may still be running on server. Check {self.client.base_url}/jobs/{job_id}",
                )

            # Clean up state
            if pattern_id in self.running_jobs:
                del self.running_jobs[pattern_id]

            self.results[pattern_id] = result
            return result

        except (KeyboardInterrupt, click.Abort):
            # Don't catch interruptions - let them propagate for cleanup
            self.logger.error(f"Error monitoring {pattern_id}: ")
            # Clean up state before re-raising
            if pattern_id in self.running_jobs:
                del self.running_jobs[pattern_id]
            raise

        except Exception as e:
            self.logger.error(f"Error monitoring {pattern_id}: {e}")
            return ExecutionResult(
                pattern_id=pattern_id,
                job_id=job_id,
                success=False,
                message=f"Error: {str(e)}",
            )

    def cleanup_pattern(self, pattern_id: str) -> bool:
        """
        Clean up a pattern (delete the deployed process).

        Args:
            pattern_id: Pattern identifier
            skip_jobs: If True, skip job cleanup (for interrupt scenarios)

        Returns:
            True if cleanup succeeds
        """
        if pattern_id not in self.deployed_processes:
            return True

        try:
            self.logger.info(f"Cleaning up pattern {pattern_id}")
            success = self.client.delete_process(pattern_id)

            if success:
                self.deployed_processes.discard(pattern_id)
                self.logger.info(f"Pattern {pattern_id} cleaned up")

            return success

        except Exception as e:
            self.logger.error(f"Error cleaning up {pattern_id}: {e}")
            return False

    def run_single_pattern(
        self, pattern_id: str, cleanup: bool = True, timeout: int = 1800
    ) -> ExecutionResult:
        """
        Run a complete pattern (deployment -> execution -> monitoring -> cleanup).

        Args:
            pattern_id: Pattern identifier
            cleanup: If True, clean up pattern after execution
            timeout: Timeout for execution (default: 30 minutes, use 0 for unlimited)

        Returns:
            Execution result
        """
        self.logger.info(f"Starting complete execution of pattern {pattern_id}")

        # Register pattern in cleanup handler at the start
        if self.cleanup_handler:
            self.cleanup_handler.current_pattern_id = pattern_id

        interrupted = False

        try:
            # Deployment
            if not self.deploy_pattern(pattern_id):
                # Clear cleanup handler on failure
                if self.cleanup_handler:
                    self.cleanup_handler.current_pattern_id = None
                return ExecutionResult(
                    pattern_id=pattern_id, success=False, message="Deployment failed"
                )

            # Execution
            job_id = self.execute_pattern(pattern_id)
            if not job_id:
                if cleanup:
                    self.cleanup_pattern(pattern_id)
                # Clear cleanup handler on failure
                if self.cleanup_handler:
                    self.cleanup_handler.current_pattern_id = None
                return ExecutionResult(
                    pattern_id=pattern_id, success=False, message="Execution failed"
                )

            # Register job_id in cleanup handler if available
            if self.cleanup_handler:
                self.cleanup_handler.current_job_id = job_id

            # Monitoring
            result = self.monitor_job(pattern_id, timeout)

            # Clear job_id from cleanup handler after monitoring
            if self.cleanup_handler:
                self.cleanup_handler.current_job_id = None

            # Optional cleanup - but skip if timeout (job may still be running)
            if cleanup:
                # Only cleanup if job actually finished, not on timeout
                if result.success or "Monitoring timeout" not in result.message:
                    cleanup_success = self.cleanup_pattern(pattern_id)
                    if not cleanup_success:
                        result.message += " (Warning: cleanup failed)"
                else:
                    self.logger.info(
                        f"Skipping cleanup for {pattern_id} - job may still be running"
                    )
                    result.message += " (Cleanup skipped - job may still be running)"

            return result

        finally:
            # Always clear pattern_id from cleanup handler
            if self.cleanup_handler:
                self.cleanup_handler.current_pattern_id = None

    def run_multiple_patterns(
        self,
        pattern_ids: List[str],
        cleanup: bool = True,
        timeout: int = 1800,
        parallel: bool = False,
    ) -> TestSummary:
        """
        Execute multiple patterns.

        Args:
            pattern_ids: List of pattern identifiers
            cleanup: If True, clean up each pattern after execution
            timeout: Timeout for each execution (default: 30 minutes, use 0 for unlimited)
            parallel: If True, execute in parallel (not implemented)

        Returns:
            Test summary
        """
        if parallel:
            # TODO: Implement parallel execution
            self.logger.warning("Parallel execution is not yet implemented")

        results = []
        start_time = time.time()

        for pattern_id in pattern_ids:
            self.logger.info(f"Processing pattern {pattern_id}")
            result = self.run_single_pattern(pattern_id, cleanup, timeout)
            results.append(result)

        total_time = time.time() - start_time

        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        summary = TestSummary(
            total_patterns=len(results),
            successful_patterns=successful,
            failed_patterns=failed,
            total_execution_time=total_time,
            results=results,
        )

        self.logger.info(f"Tests completed: {successful}/{len(results)} successful")
        return summary

    def run_all_patterns(
        self, cleanup: bool = True, timeout: int = 1800
    ) -> TestSummary:
        """
        Execute all available patterns.

        Args:
            cleanup: If True, clean up each pattern after execution
            timeout: Timeout for each execution (default: 30 minutes, use 0 for unlimited)

        Returns:
            Test summary
        """
        # Find all pattern files
        pattern_files = list(self.patterns_dir.glob("pattern-*.json"))
        pattern_ids = [f.stem for f in pattern_files]
        # Sort numerically by pattern number
        pattern_ids.sort(
            key=lambda x: (
                int(x.split("-")[1]) if "-" in x and x.split("-")[1].isdigit() else 0
            )
        )

        self.logger.info(f"Executing {len(pattern_ids)} patterns: {pattern_ids}")
        return self.run_multiple_patterns(pattern_ids, cleanup, timeout)

    def cleanup_all(self) -> bool:
        """
        Clean up all deployed patterns.

        Returns:
            True if all cleanups succeed
        """
        success = True
        deployed_copy = list(self.deployed_processes)

        for pattern_id in deployed_copy:
            if not self.cleanup_pattern(pattern_id):
                success = False

        return success

    def get_status(self) -> Dict:
        """
        Return the current state of the manager.

        Returns:
            Dictionary with current state
        """
        return {
            "deployed_processes": list(self.deployed_processes),
            "running_jobs": dict(self.running_jobs),
            "completed_results": len(self.results),
            "server_config": {
                "base_url": self.server_config.base_url,
                "auth_required": self.server_config.auth_token is not None,
            },
        }
