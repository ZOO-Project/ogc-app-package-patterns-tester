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

"""Utilities for the OGC patterns tester.
"""

import functools
import time
from pathlib import Path
from typing import Any, Callable

import requests


def setup_logger(name: str, level: str = "INFO") -> Any:
    """
    Set up logger configuration.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    try:
        from loguru import logger

        return logger
    except ImportError:
        import logging

        logging.basicConfig(level=getattr(logging, level.upper()))
        return logging.getLogger(name)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        raise e

                    delay = base_delay * (2**attempt)
                    time.sleep(delay)

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def download_cwl_file(url: str, output_path: str) -> bool:
    """
    Download a CWL file from a URL.

    Args:
        url: URL to download from
        output_path: Local path to save the file

    Returns:
        True if download successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Create directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        return True

    except Exception:
        return False
