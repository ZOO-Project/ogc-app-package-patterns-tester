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

"""Data models for the OGC patterns tester.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(Enum):
    """Possible statuses for an OGC API Processes job."""

    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    DISMISSED = "dismissed"
    ACCEPTED = "accepted"
    UNKNOWN = "unknown"


class PatternType(Enum):
    """Supported pattern types."""

    BASIC_PROCESSING = "basic_processing"
    SCATTER_GATHER = "scatter_gather"
    CONDITIONAL_WORKFLOW = "conditional_workflow"
    NESTED_WORKFLOW = "nested_workflow"
    MULTIPLE_INPUTS = "multiple_inputs"
    MULTIPLE_OUTPUTS = "multiple_outputs"
    OPTIONAL_OUTPUTS = "optional_outputs"
    COMPLEX_PARAMETERS = "complex_parameters"

    @classmethod
    def from_pattern_id(cls, pattern_id: str) -> "PatternType":
        """
        Determine the pattern type from its identifier.

        Args:
            pattern_id: Pattern identifier (e.g., "pattern-1")

        Returns:
            Corresponding pattern type
        """
        # Mapping based on patterns observed in the repository
        pattern_mapping = {
            "pattern-1": cls.BASIC_PROCESSING,
            "pattern-2": cls.BASIC_PROCESSING,
            "pattern-3": cls.BASIC_PROCESSING,
            "pattern-4": cls.SCATTER_GATHER,
            "pattern-5": cls.CONDITIONAL_WORKFLOW,
            "pattern-6": cls.NESTED_WORKFLOW,
            "pattern-7": cls.BASIC_PROCESSING,
            "pattern-8": cls.OPTIONAL_OUTPUTS,
            "pattern-9": cls.MULTIPLE_INPUTS,
            "pattern-10": cls.MULTIPLE_OUTPUTS,
            "pattern-11": cls.MULTIPLE_INPUTS,
            "pattern-12": cls.COMPLEX_PARAMETERS,
        }

        return pattern_mapping.get(pattern_id, cls.BASIC_PROCESSING)


@dataclass
class ProcessInfo:
    """Information about a deployed process."""

    process_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    deployed: bool = False
    deployment_time: Optional[datetime] = None


@dataclass
class JobInfo:
    """Information about a running job."""

    job_id: str
    process_id: str
    status: JobStatus
    progress: Optional[int] = None
    message: Optional[str] = None
    started: Optional[datetime] = None
    finished: Optional[datetime] = None
    outputs: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Execution result of a pattern."""

    pattern_id: str
    success: bool
    job_id: Optional[str] = None
    execution_time: Optional[float] = None
    message: Optional[str] = None
    outputs: Optional[Dict[str, Any]] = None


@dataclass
class TestSummary:
    """Summary of executed tests."""

    total_patterns: int
    successful_patterns: int
    failed_patterns: int
    total_execution_time: float
    results: List[ExecutionResult]

    @property
    def duration(self) -> Optional[float]:
        """Total execution duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Success rate of executions."""
        if self.executed_count == 0:
            return 0.0
        return (self.successful_count / self.executed_count) * 100


@dataclass
class ServerConfig:
    """OGC API Processes server configuration."""

    base_url: str
    auth_token: Optional[str] = None  # Legacy field, mapped to api_key
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 300

    def __post_init__(self):
        """Post-initialization to handle legacy auth_token mapping."""
        # Map legacy auth_token to api_key if not explicitly set
        if self.auth_token and not self.api_key:
            self.api_key = self.auth_token


@dataclass
class PatternConfig:
    """Configuration for a specific pattern."""

    pattern_id: str
    cwl_url: str
    parameters: Dict[str, Any]
    pattern_type: PatternType
