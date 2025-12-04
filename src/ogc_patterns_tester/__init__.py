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

"""OGC API Processes Patterns Tester.

This package allows testing of CWL application package patterns
on an OGC API Processes compatible server using the ogc-api-client module.
"""

from .client import OGCApiClient
from .models import (
    ExecutionResult,
    JobInfo,
    JobStatus,
    PatternConfig,
    PatternType,
    ProcessInfo,
    ServerConfig,
    TestSummary,
)
from .patterns_manager import PatternsManager
from .utils import setup_logger

__version__ = "0.1.0"
__author__ = "Assistant AI"
__email__ = "assistant@example.com"

__all__ = [
    "OGCApiClient",
    "ExecutionResult",
    "JobInfo",
    "JobStatus",
    "PatternConfig",
    "PatternType",
    "PatternsManager",
    "ProcessInfo",
    "ServerConfig",
    "TestSummary",
    "setup_logger",
]

__version__ = "0.1.0"
__author__ = "EOEPCA Team"
__email__ = "info@eoepca.org"


__all__ = [
    "OGCApiClient",
    "PatternsManager",
]
