"""
Unit tests for the NotebookParser module.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from ogc_patterns_tester.notebook_parser import NotebookParser


class TestNotebookParser:
    """Test cases for NotebookParser class."""

    @pytest.fixture
    def parser(self):
        """Create a NotebookParser instance."""
        return NotebookParser()

    def test_get_notebook_url(self, parser):
        """Test notebook URL construction."""
        url = parser.get_notebook_url("pattern-1")
        expected = (
            "https://raw.githubusercontent.com/eoap/"
            "application-package-patterns/main/docs/pattern-1.ipynb"
        )
        assert url == expected

        # Test with different pattern
        url = parser.get_notebook_url("pattern-12")
        assert url.endswith("pattern-12.ipynb")

    def test_extract_params_from_code_simple(self, parser):
        """Test extracting simple params."""
        code = """
params = {
    "aoi": "test",
    "epsg": "EPSG:4326"
}
"""
        result = parser.extract_params_from_code(code)
        assert result is not None
        assert result["aoi"] == "test"
        assert result["epsg"] == "EPSG:4326"

    def test_extract_params_from_code_nested(self, parser):
        """Test extracting nested params."""
        code = """
params = {
    "aoi": "-118.985,38.432,-118.183,38.938",
    "item": {
        "class": "URL",
        "value": "https://example.com"
    }
}
"""
        result = parser.extract_params_from_code(code)
        assert result is not None
        assert "item" in result
        assert result["item"]["class"] == "URL"
        assert result["item"]["value"] == "https://example.com"

    def test_extract_params_from_code_multiline(self, parser):
        """Test extracting multi-line params with long strings."""
        code = """
params = {
    "item": {
        "class": "URL",
        "value": "https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC08_L2SP_042033_20231007_02_T1"
    }
}
"""
        result = parser.extract_params_from_code(code)
        assert result is not None
        assert "item" in result
        assert "value" in result["item"]
        assert result["item"]["value"].startswith("https://")

    def test_extract_params_from_code_with_lists(self, parser):
        """Test extracting params with lists."""
        code = """
params = {
    "bands": ["green", "nir08"],
    "numbers": [1, 2, 3]
}
"""
        result = parser.extract_params_from_code(code)
        assert result is not None
        assert result["bands"] == ["green", "nir08"]
        assert result["numbers"] == [1, 2, 3]

    def test_extract_params_from_code_no_params(self, parser):
        """Test code without params."""
        code = """
import os
x = 5
print("hello")
"""
        result = parser.extract_params_from_code(code)
        assert result is None

    def test_extract_params_from_code_invalid_syntax(self, parser):
        """Test handling invalid syntax."""
        code = """
params = {
    "key": "value"
    # Missing closing brace
"""
        result = parser.extract_params_from_code(code)
        assert result is None

    def test_extract_params_from_notebook(self, parser):
        """Test extracting from notebook structure."""
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Title"]},
                {
                    "cell_type": "code",
                    "source": ["params = {\n", '    "key": "value"\n', "}\n"],
                },
            ]
        }

        result = parser.extract_params_from_notebook(notebook)
        assert result is not None
        assert result["key"] == "value"

    def test_extract_params_from_notebook_multiple_cells(self, parser):
        """Test finding params in multiple cells."""
        notebook = {
            "cells": [
                {"cell_type": "code", "source": ["import json\n"]},
                {"cell_type": "code", "source": ["x = 5\n"]},
                {
                    "cell_type": "code",
                    "source": ["params = {\n", '    "test": "value"\n', "}\n"],
                },
            ]
        }

        result = parser.extract_params_from_notebook(notebook)
        assert result is not None
        assert result["test"] == "value"

    def test_extract_params_from_notebook_no_params(self, parser):
        """Test notebook without params."""
        notebook = {"cells": [{"cell_type": "code", "source": ["print('hello')\n"]}]}

        result = parser.extract_params_from_notebook(notebook)
        assert result is None

    def test_save_params_to_json(self, parser, tmp_path):
        """Test saving params to JSON file."""
        params = {"aoi": "test", "bands": ["red", "green"]}

        output_file = tmp_path / "test.json"
        parser.save_params_to_json(params, output_file)

        # Verify file exists and content is correct
        assert output_file.exists()

        with open(output_file) as f:
            loaded = json.load(f)

        assert loaded == params

    def test_save_params_creates_directory(self, parser, tmp_path):
        """Test that save_params creates directory if needed."""
        output_file = tmp_path / "subdir" / "params.json"
        params = {"test": "value"}

        parser.save_params_to_json(params, output_file)

        assert output_file.exists()
        assert output_file.parent.exists()

    @patch("urllib.request.urlopen")
    def test_download_notebook_success(self, mock_urlopen, parser):
        """Test successful notebook download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"cells": [], "metadata": {}}
        ).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = parser.download_notebook("pattern-1")

        assert result is not None
        assert "cells" in result
        assert "metadata" in result

    @patch("urllib.request.urlopen")
    def test_download_notebook_404(self, mock_urlopen, parser):
        """Test notebook download with 404 error."""
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None
        )

        result = parser.download_notebook("pattern-999")
        assert result is None

    @patch("urllib.request.urlopen")
    def test_download_notebook_network_error(self, mock_urlopen, parser):
        """Test notebook download with network error."""
        mock_urlopen.side_effect = Exception("Network error")

        result = parser.download_notebook("pattern-1")
        assert result is None

    def test_sync_pattern_params_success(self, tmp_path):
        """Test successful pattern sync with mocked methods."""
        parser = NotebookParser()

        # Mock the methods individually
        test_notebook = {
            "cells": [{"cell_type": "code", "source": ["params = {'test': 'value'}"]}]
        }

        with patch.object(parser, "download_notebook", return_value=test_notebook):
            with patch.object(
                parser, "extract_params_from_notebook", return_value={"test": "value"}
            ):
                with patch.object(parser, "save_params_to_json", return_value=True):
                    result = parser.sync_pattern_params("pattern-1", tmp_path)

                    assert result is True

    @patch("ogc_patterns_tester.notebook_parser.NotebookParser.download_notebook")
    def test_sync_pattern_params_download_fails(self, mock_download, tmp_path):
        """Test sync when download fails."""
        parser = NotebookParser()
        mock_download.return_value = None

        result = parser.sync_pattern_params("pattern-1", tmp_path)

        assert result is False

    @patch("ogc_patterns_tester.notebook_parser.NotebookParser.sync_pattern_params")
    def test_sync_all_patterns(self, mock_sync, tmp_path):
        """Test syncing multiple patterns."""
        parser = NotebookParser()

        # Mock successes and failures
        mock_sync.side_effect = [True, False, True]

        patterns = ["pattern-1", "pattern-2", "pattern-3"]
        results = parser.sync_all_patterns(patterns, tmp_path)

        assert len(results) == 3
        assert results["pattern-1"] is True
        assert results["pattern-2"] is False
        assert results["pattern-3"] is True

    @patch("ogc_patterns_tester.notebook_parser.NotebookParser.sync_pattern_params")
    def test_sync_all_patterns_stop_on_error(self, mock_sync, tmp_path):
        """Test that sync stops on error by default."""
        parser = NotebookParser()

        # First succeeds, second fails
        mock_sync.side_effect = [True, False]

        patterns = ["pattern-1", "pattern-2", "pattern-3"]
        results = parser.sync_all_patterns(patterns, tmp_path, continue_on_error=False)

        # Should only have results for first two patterns
        assert len(results) == 2
        assert "pattern-3" not in results

    @patch("ogc_patterns_tester.notebook_parser.NotebookParser.sync_pattern_params")
    def test_sync_all_patterns_continue_on_error(self, mock_sync, tmp_path):
        """Test that sync continues on error when requested."""
        parser = NotebookParser()

        # First succeeds, second fails, third succeeds
        mock_sync.side_effect = [True, False, True]

        patterns = ["pattern-1", "pattern-2", "pattern-3"]
        results = parser.sync_all_patterns(patterns, tmp_path, continue_on_error=True)

        # Should have all results
        assert len(results) == 3
        assert results["pattern-1"] is True
        assert results["pattern-2"] is False
        assert results["pattern-3"] is True
