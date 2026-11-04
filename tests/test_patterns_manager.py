"""Tests for the patterns manager."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from ogc_patterns_tester.cli import cli
from ogc_patterns_tester.patterns_manager import PatternsManager


@pytest.mark.parametrize("ref", ["v1.0.0", "release/test", "abc123"])
def test_repository_reference(server_config, tmp_path, ref):
    patterns = tmp_path / "patterns"
    patterns.mkdir()
    (patterns / "pattern-1.json").write_text("{}")
    cache = tmp_path / "cwl"
    default = PatternsManager(server_config, str(patterns), str(cache))
    (cache / "pattern-1.cwl").write_text("cached main")
    manager = PatternsManager(
        server_config, str(patterns), str(cache), patterns_ref=ref
    )
    config = manager.load_pattern_config("pattern-1")
    assert config is not None
    assert f"/{ref.replace('/', '%2F')}/cwl-workflow/" in config.cwl_url
    assert default.download_dir == cache
    assert manager.download_dir != cache
    assert manager.download_dir.parent == cache
    with patch(
        "ogc_patterns_tester.patterns_manager.download_cwl_file",
        return_value=True,
    ) as download:
        assert manager.prepare_pattern("pattern-1")
        download.assert_called_once_with(
            config.cwl_url, str(manager.download_dir / "pattern-1.cwl")
        )
    other = PatternsManager(
        server_config, str(patterns), str(cache), patterns_ref="other"
    )
    assert other.download_dir != manager.download_dir
    with patch.object(manager, "prepare_pattern", return_value=True), patch.object(
        manager.client, "deploy_process"
    ) as deploy:
        assert manager.deploy_pattern("pattern-1")
        deploy.assert_called_once_with(
            "pattern-1", str(manager.download_dir / "pattern-1.cwl")
        )


def test_cli_reference():
    with patch("ogc_patterns_tester.cli.PatternsManager") as manager:
        result = CliRunner().invoke(
            cli, ["--patterns-ref", "v1.0.0", "download", "pattern-1"]
        )
        assert result.exit_code == 0, result.output
        assert manager.call_args.kwargs["patterns_ref"] == "v1.0.0"


def test_sync_params_reference(tmp_path):
    with patch("ogc_patterns_tester.cli.PatternsManager") as manager, patch(
        "ogc_patterns_tester.notebook_parser.NotebookParser"
    ) as parser:
        manager.return_value.patterns_ref = "v1.0.0"
        result = CliRunner().invoke(
            cli,
            [
                "--patterns-ref",
                "v1.0.0",
                "sync-params",
                "pattern-1",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output
        parser.assert_called_once_with(patterns_ref="v1.0.0")


class TestPatternsManager:
    """Test cases for PatternsManager class."""

    def test_manager_initialization(self, server_config, temp_dir):
        """Test patterns manager initialization."""
        patterns_dir = temp_dir / "patterns"
        download_dir = temp_dir / "downloads"

        manager = PatternsManager(
            server_config=server_config,
            patterns_dir=str(patterns_dir),
            download_dir=str(download_dir),
        )

        assert manager.server_config == server_config
        assert manager.patterns_dir == patterns_dir
        assert manager.download_dir == download_dir
        assert patterns_dir.exists()
        assert download_dir.exists()

    def test_load_pattern_config_success(
        self, server_config, temp_dir, sample_pattern_config
    ):
        """Test successful pattern configuration loading."""
        patterns_dir = temp_dir / "patterns"
        patterns_dir.mkdir()

        # Create pattern config file
        config_file = patterns_dir / "test-pattern-1.json"
        with open(config_file, "w") as f:
            json.dump(sample_pattern_config, f)

        manager = PatternsManager(
            server_config=server_config,
            patterns_dir=str(patterns_dir),
            download_dir=str(temp_dir / "downloads"),
        )

        # Execute
        config = manager.load_pattern_config("test-pattern-1")

        # Verify
        assert config is not None
        assert config.pattern_id == "test-pattern-1"
        # Le système génère automatiquement l'URL à partir du pattern_id
        assert "test-pattern-1.cwl" in config.cwl_url

    def test_load_pattern_config_file_not_found(self, server_config, temp_dir):
        """Test pattern configuration loading with missing file."""
        manager = PatternsManager(
            server_config=server_config,
            patterns_dir=str(temp_dir / "patterns"),
            download_dir=str(temp_dir / "downloads"),
        )

        config = manager.load_pattern_config("nonexistent-pattern")

        assert config is None

    def test_download_pattern_cwl_success(self, server_config, temp_dir):
        """Test successful CWL pattern download."""
        # Create patterns directory and config file
        patterns_dir = temp_dir / "patterns"
        patterns_dir.mkdir()

        # Create pattern config file required by download_pattern_cwl
        config_file = patterns_dir / "test-pattern.json"
        config_data = {
            "pattern_id": "test-pattern",
            "cwl_url": "https://example.com/test-pattern.cwl",
            "parameters": {},
            "pattern_type": "basic_processing",
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Mock download_cwl_file from utils
        with patch(
            "ogc_patterns_tester.patterns_manager.download_cwl_file"
        ) as mock_download:
            mock_download.return_value = True

            manager = PatternsManager(
                server_config=server_config,
                patterns_dir=str(patterns_dir),
                download_dir=str(temp_dir / "downloads"),
            )

            # Execute
            result = manager.download_pattern_cwl("test-pattern")

            # Verify - download_pattern_cwl retourne un booléen
            assert result is True
            mock_download.assert_called_once()

    def test_download_pattern_cwl_http_error(self, server_config, temp_dir):
        """Test CWL pattern download with HTTP error."""
        # Mock urllib.request.urlopen to raise error
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("404 Not Found")

            manager = PatternsManager(
                server_config=server_config,
                patterns_dir=str(temp_dir / "patterns"),
                download_dir=str(temp_dir / "downloads"),
            )

            # Execute - download_pattern_cwl retourne False en cas d'erreur
            result = manager.download_pattern_cwl("test-pattern")

            # Verify
            assert result is False

    def test_deploy_pattern_success(
        self,
        server_config,
        temp_dir,
        mock_ogc_client,
        sample_pattern_config,
    ):
        """Test successful pattern deployment."""
        # Setup
        patterns_dir = temp_dir / "patterns"
        patterns_dir.mkdir()
        download_dir = temp_dir / "downloads"
        download_dir.mkdir()

        config_file = patterns_dir / "test-pattern.json"
        with open(config_file, "w") as f:
            json.dump(sample_pattern_config, f)

        # Create a dummy CWL file
        cwl_file = download_dir / "test-pattern.cwl"
        cwl_file.write_text("cwlVersion: v1.0\nclass: CommandLineTool")

        mock_process_info = Mock()
        mock_process_info.deployed = True
        mock_ogc_client.deploy_process.return_value = mock_process_info

        manager = PatternsManager(
            server_config=server_config,
            patterns_dir=str(patterns_dir),
            download_dir=str(download_dir),
        )
        manager.client = mock_ogc_client

        # Execute
        result = manager.deploy_pattern("test-pattern")

        # Verify
        assert result is True
        mock_ogc_client.deploy_process.assert_called_once()

    def test_deploy_pattern_config_not_found(
        self, server_config, temp_dir, mock_ogc_client
    ):
        """Test pattern deployment with missing configuration."""
        manager = PatternsManager(
            server_config=server_config,
            patterns_dir=str(temp_dir / "patterns"),
            download_dir=str(temp_dir / "downloads"),
        )
        manager.client = mock_ogc_client

        result = manager.deploy_pattern("nonexistent-pattern")

        assert result is False
