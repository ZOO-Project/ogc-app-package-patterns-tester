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

"""Notebook parser for extracting pattern parameters from Jupyter notebooks.

This module parses Jupyter notebooks from the eoap/application-package-patterns
repository to extract the 'params' variable and generate local JSON parameter files.
"""

import json
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import setup_logger


class NotebookParser:
    """Parser for extracting parameters from Jupyter notebooks."""

    # GitHub repository configuration
    GITHUB_REPO = "eoap/application-package-patterns"
    GITHUB_BRANCH = "main"
    DOCS_PATH = "docs"

    def __init__(self):
        """Initialize the notebook parser."""
        self.logger = setup_logger(__name__)

    def get_notebook_url(self, pattern_id: str) -> str:
        """
        Get the raw GitHub URL for a pattern's notebook.

        Args:
            pattern_id: Pattern identifier (e.g., "pattern-1")

        Returns:
            Raw GitHub URL for the notebook
        """
        notebook_name = f"{pattern_id}.ipynb"
        return (
            f"https://raw.githubusercontent.com/{self.GITHUB_REPO}/"
            f"{self.GITHUB_BRANCH}/{self.DOCS_PATH}/{notebook_name}"
        )

    def download_notebook(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Download a notebook from GitHub.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Notebook content as dictionary, or None if download fails
        """
        url = self.get_notebook_url(pattern_id)
        self.logger.info(f"Downloading notebook from {url}")

        try:
            with urllib.request.urlopen(url) as response:
                notebook = json.loads(response.read().decode("utf-8"))
            self.logger.info(f"✓ Downloaded notebook for {pattern_id}")
            return notebook
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.logger.warning(f"Notebook not found for {pattern_id} (404)")
            else:
                self.logger.error(
                    f"HTTP error downloading notebook: {e.code} - {e.reason}"
                )
            return None
        except Exception as e:
            self.logger.error(f"Error downloading notebook for {pattern_id}: {e}")
            return None

    def extract_params_from_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Extract the 'params' variable from Python code using brace matching.

        Handles nested dictionaries and multi-line strings properly.

        Args:
            code: Python code string

        Returns:
            Extracted parameters dictionary, or None if not found
        """
        import ast

        if not code or "params" not in code:
            return None

        # Find "params = {"
        params_pattern = r"params\s*=\s*\{"
        match = re.search(params_pattern, code)

        if not match:
            return None

        # Start from the opening brace
        start_pos = match.end() - 1  # Position of the opening '{'

        # Track brace depth to find matching closing brace
        brace_count = 0
        in_string = False
        quote_char = None
        escape_next = False
        end_pos = start_pos

        for i in range(start_pos, len(code)):
            char = code[i]

            # Handle escape sequences
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            # Handle strings
            if char in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    in_string = False
                    quote_char = None
                continue

            # Only count braces outside of strings
            if not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break

        if brace_count != 0:
            self.logger.error("Unmatched braces in params definition")
            return None

        # Extract the complete params dictionary
        params_str = code[start_pos:end_pos]

        # Try to parse using ast.literal_eval first (most reliable)
        try:
            params = ast.literal_eval(params_str)
            if isinstance(params, dict):
                self.logger.debug("Successfully parsed params with ast.literal_eval")
                return params
        except Exception as e:
            self.logger.debug(f"ast.literal_eval failed: {e}, trying JSON fallback")

        # Fallback: try JSON parsing with Python syntax conversion
        try:
            params_json = params_str.replace("'", '"')
            params_json = re.sub(r":\s*True\b", ": true", params_json)
            params_json = re.sub(r":\s*False\b", ": false", params_json)
            params_json = re.sub(r":\s*None\b", ": null", params_json)
            # Remove trailing commas before closing braces
            params_json = re.sub(r",(\s*[}\]])", r"\1", params_json)
            params = json.loads(params_json)
            self.logger.debug("Successfully parsed params with JSON fallback")
            return params
        except Exception as e:
            self.logger.error(f"Failed to parse params: {e}")
            return None

    def extract_params_from_notebook(
        self, notebook: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract parameters from a Jupyter notebook.

        Searches all code cells for a 'params' variable definition.

        Args:
            notebook: Notebook dictionary (parsed JSON)

        Returns:
            Extracted parameters, or None if not found
        """
        if "cells" not in notebook:
            self.logger.error("Invalid notebook format: no 'cells' key")
            return None

        # Search through all code cells
        for cell in notebook["cells"]:
            if cell.get("cell_type") != "code":
                continue

            # Get cell source (can be string or list of strings)
            source = cell.get("source", [])
            if isinstance(source, list):
                code = "".join(source)
            else:
                code = source

            # Look for params definition in this cell
            params = self.extract_params_from_code(code)
            if params:
                self.logger.info("✓ Found params in notebook")
                return params

        self.logger.warning("No 'params' variable found in notebook")
        return None

    def save_params_to_json(self, params: Dict[str, Any], output_file: Path) -> bool:
        """
        Save parameters to a JSON file.

        Args:
            params: Parameters dictionary
            output_file: Output file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON with nice formatting
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(params, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✓ Saved parameters to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving parameters: {e}")
            return False

    def sync_pattern_params(self, pattern_id: str, output_dir: Path) -> bool:
        """
        Synchronize parameters for a single pattern.

        Downloads the notebook, extracts params, and saves to JSON.

        Args:
            pattern_id: Pattern identifier (e.g., "pattern-1")
            output_dir: Directory where JSON files will be saved

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Syncing parameters for {pattern_id}...")

        # Download notebook
        notebook = self.download_notebook(pattern_id)
        if not notebook:
            return False

        # Extract params
        params = self.extract_params_from_notebook(notebook)
        if not params:
            return False

        # Save to JSON
        output_file = output_dir / f"{pattern_id}.json"
        return self.save_params_to_json(params, output_file)

    def sync_all_patterns(
        self, pattern_ids: List[str], output_dir: Path, continue_on_error: bool = True
    ) -> Dict[str, bool]:
        """
        Synchronize parameters for multiple patterns.

        Args:
            pattern_ids: List of pattern identifiers
            output_dir: Directory where JSON files will be saved
            continue_on_error: Continue even if some patterns fail

        Returns:
            Dictionary mapping pattern_id to success status
        """
        results = {}

        for pattern_id in pattern_ids:
            try:
                success = self.sync_pattern_params(pattern_id, output_dir)
                results[pattern_id] = success

                if not success and not continue_on_error:
                    self.logger.error(f"Stopping due to error with {pattern_id}")
                    break
            except Exception as e:
                self.logger.error(f"Error syncing {pattern_id}: {e}")
                results[pattern_id] = False

                if not continue_on_error:
                    break

        # Summary
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        self.logger.info(f"\nSync complete: {successful}/{total} patterns updated")

        return results
