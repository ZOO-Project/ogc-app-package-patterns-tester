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

"""Command line interface for the OGC API Processes patterns tester.

This module provides a complete user interface for deploying, executing
and monitoring CWL workflows on an OGC API Processes server.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .models import ServerConfig
from .patterns_manager import PatternsManager
from .utils import setup_logger

# Global reference to the active cleanup handler
# This will be updated by each CLI invocation
_active_cleanup_handler: Optional["CleanupHandler"] = None


class CleanupHandler:
    """
    Tracks current pattern and job for informational purposes.
    Note: Ctrl+C interruptions cannot perform cleanup due to API call blocking.
    """

    def __init__(self):
        self.manager: Optional[PatternsManager] = None
        self.current_pattern_id: Optional[str] = None
        self.current_job_id: Optional[str] = None


def load_server_config(config_file: Optional[str] = None) -> ServerConfig:
    """
    Load server configuration from file or default settings.

    Args:
        config_file: Path to JSON configuration file

    Returns:
        Server configuration
    """
    if config_file and Path(config_file).exists():
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        return ServerConfig(**data)
    else:
        # Default configuration
        return ServerConfig(
            base_url="http://localhost:5000", auth_token=None, timeout=1800
        )


@click.group()
@click.option(
    "--config",
    "-c",
    help="Server JSON configuration file",
    type=click.Path(exists=True),
)
@click.option(
    "--server-url",
    "-s",
    help="Base URL of the OGC API Processes server",
    default="http://localhost:5000",
)
@click.option(
    "--auth-token", "-t", help="Authentication token (optional)", default=None
)
@click.option(
    "--patterns-dir",
    "-p",
    help="Directory containing pattern files",
    default="data/patterns",
    type=click.Path(),
)
@click.option(
    "--download-dir",
    "-d",
    help="Temporary directory for CWL files",
    default="temp/cwl",
    type=click.Path(),
)
@click.option(
    "--force-download",
    "-f",
    help="Force re-download of CWL files even if they exist locally",
    is_flag=True,
    default=False,
)
@click.option("--verbose", "-v", help="Verbose mode", is_flag=True, default=False)
@click.pass_context
def cli(
    ctx,
    config: Optional[str],
    server_url: str,
    auth_token: Optional[str],
    patterns_dir: str,
    download_dir: str,
    force_download: bool,
    verbose: bool,
):
    """
    Pattern tester for OGC API Processes.

    This tool allows testing CWL application package patterns
    on a compatible OGC API Processes server.
    """
    # Configure logging
    setup_logger("ogc_patterns_tester", level="DEBUG" if verbose else "INFO")

    # Create cleanup handler and set as active global
    global _active_cleanup_handler
    cleanup_handler = CleanupHandler()
    _active_cleanup_handler = cleanup_handler

    # Load server configuration
    if config:
        server_config = load_server_config(config)
    else:
        server_config = ServerConfig(
            base_url=server_url, auth_token=auth_token, timeout=1800
        )

    # Create patterns manager
    manager = PatternsManager(
        server_config=server_config,
        patterns_dir=patterns_dir,
        download_dir=download_dir,
        force_download=force_download,
        cleanup_handler=cleanup_handler,
    )

    # Register manager in cleanup handler
    cleanup_handler.manager = manager

    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["manager"] = manager
    ctx.obj["cleanup_handler"] = cleanup_handler
    ctx.obj["verbose"] = verbose
    ctx.obj["force_download"] = force_download


@cli.command()
@click.argument("pattern_ids", nargs=-1)
@click.pass_context
def download(ctx, pattern_ids: tuple):
    """
    Download CWL workflows for specified patterns.

    If no PATTERN_IDS are specified, downloads all patterns (1-12).
    This will force re-download even if files already exist.
    """
    manager: PatternsManager = ctx.obj["manager"]

    # Determine which patterns to download
    if pattern_ids:
        patterns_to_download = list(pattern_ids)
    else:
        # Download all patterns 1-12
        patterns_to_download = [f"pattern-{i}" for i in range(1, 13)]

    click.echo(
        f"Downloading CWL workflows for {len(patterns_to_download)} pattern(s)..."
    )

    success_count = 0
    fail_count = 0

    for pattern_id in patterns_to_download:
        try:
            if manager.download_pattern_cwl(pattern_id, force=True):
                click.echo(click.style(f"✓ {pattern_id}", fg="green"))
                success_count += 1
            else:
                click.echo(click.style(f"✗ {pattern_id} - Failed", fg="red"))
                fail_count += 1
        except Exception as e:
            click.echo(click.style(f"✗ {pattern_id} - Error: {e}", fg="red"))
            fail_count += 1

    click.echo(f"\nDownload complete: {success_count} succeeded, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


@cli.command()
@click.argument("pattern_id")
@click.option(
    "--no-cleanup",
    help="Do not clean up pattern after execution",
    is_flag=True,
    default=False,
)
@click.option(
    "--timeout",
    "-T",
    help="Timeout in seconds for execution (default: 1800=30min, use 0 for unlimited)",
    default=1800,
    type=int,
)
@click.pass_context
def run(ctx, pattern_id: str, no_cleanup: bool, timeout: int):
    """
    Execute a specific pattern.

    PATTERN_ID: Pattern identifier (e.g., pattern-1)
    """
    manager: PatternsManager = ctx.obj["manager"]
    cleanup_handler: CleanupHandler = ctx.obj.get("cleanup_handler")
    verbose: bool = ctx.obj["verbose"]

    # Use active cleanup handler if not in context
    if cleanup_handler is None:
        cleanup_handler = _active_cleanup_handler

    click.echo(f"Executing pattern: {pattern_id}")

    # Check that configuration file exists
    config_file = Path(manager.patterns_dir) / f"{pattern_id}.json"
    if not config_file.exists():
        click.echo(f"Error: Configuration file not found: {config_file}", err=True)
        sys.exit(1)

    # Register current pattern in cleanup handler
    if cleanup_handler:
        cleanup_handler.current_pattern_id = pattern_id

    try:
        # Execute the pattern (cleanup is handled internally)
        result = manager.run_single_pattern(
            pattern_id=pattern_id, cleanup=not no_cleanup, timeout=timeout
        )

        # Display results
        if result.success:
            click.echo(click.style("✓ Success", fg="green", bold=True))
            if verbose and result.execution_time:
                click.echo(f"Execution time: {result.execution_time:.1f}s")
            if verbose and result.outputs:
                click.echo(f"Outputs: {len(result.outputs)} files")
        else:
            click.echo(click.style("✗ Failed", fg="red", bold=True))
            click.echo(f"Error: {result.message}", err=True)
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nExecution interrupted by user (Ctrl+C)", err=True)
        sys.exit(130)

    finally:
        # Clear cleanup handler state
        if cleanup_handler:
            cleanup_handler.current_pattern_id = None
            cleanup_handler.current_job_id = None


@cli.command()
@click.argument("pattern_ids", nargs=-1)
@click.option(
    "--no-cleanup",
    help="Do not clean up patterns after execution",
    is_flag=True,
    default=False,
)
@click.option(
    "--timeout",
    "-T",
    help="Timeout in seconds for each execution (default: 1800=30min, use 0 for unlimited)",
    default=1800,
    type=int,
)
@click.option(
    "--continue-on-error",
    help="Continue even if a pattern fails",
    is_flag=True,
    default=False,
)
@click.pass_context
def run_multiple(
    ctx, pattern_ids: tuple, no_cleanup: bool, timeout: int, continue_on_error: bool
):
    """
    Execute multiple specified patterns.

    PATTERN_IDS: List of pattern identifiers (e.g., pattern-1 pattern-2)
    """
    manager: PatternsManager = ctx.obj["manager"]

    if not pattern_ids:
        click.echo("Error: No patterns specified", err=True)
        sys.exit(1)

    click.echo(f"Executing {len(pattern_ids)} patterns: {', '.join(pattern_ids)}")

    try:
        # Execute patterns
        summary = manager.run_multiple_patterns(
            pattern_ids=list(pattern_ids), cleanup=not no_cleanup, timeout=timeout
        )

        # Display summary
        display_summary(summary, ctx.obj["verbose"])

        # Exit with error code if failures and no continue-on-error
        if summary.failed_patterns > 0 and not continue_on_error:
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nExecution interrupted by user (Ctrl+C)", err=True)
        sys.exit(130)


@cli.command()
@click.option(
    "--no-cleanup",
    help="Do not clean up patterns after execution",
    is_flag=True,
    default=False,
)
@click.option(
    "--timeout",
    "-T",
    help="Timeout in seconds for each execution (default: 1800=30min, use 0 for unlimited)",
    default=1800,
    type=int,
)
@click.option(
    "--continue-on-error",
    help="Continue even if a pattern fails",
    is_flag=True,
    default=False,
)
@click.pass_context
def run_all(ctx, no_cleanup: bool, timeout: int, continue_on_error: bool):
    """
    Execute all available patterns.
    """
    manager: PatternsManager = ctx.obj["manager"]

    click.echo("Executing all available patterns...")

    try:
        # Execute all patterns
        summary = manager.run_all_patterns(cleanup=not no_cleanup, timeout=timeout)

        # Display summary
        display_summary(summary, ctx.obj["verbose"])

        # Exit with error code if failures and no continue-on-error
        if summary.failed_patterns > 0 and not continue_on_error:
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nExecution interrupted by user (Ctrl+C)", err=True)
        sys.exit(130)


@cli.command()
@click.argument("pattern_id")
@click.pass_context
def deploy(ctx, pattern_id: str):
    """
    Deploy a pattern on the server without executing it.

    PATTERN_ID: Pattern identifier (e.g., pattern-1)
    """
    manager: PatternsManager = ctx.obj["manager"]

    click.echo(f"Deploying pattern: {pattern_id}")

    success = manager.deploy_pattern(pattern_id)

    if success:
        click.echo(click.style("✓ Pattern deployed", fg="green", bold=True))
    else:
        click.echo(click.style("✗ Deployment failed", fg="red", bold=True))
        sys.exit(1)


@cli.command()
@click.argument("pattern_id")
@click.pass_context
def cleanup(ctx, pattern_id: str):
    """
    Clean up a deployed pattern (remove it from the server).

    PATTERN_ID: Pattern identifier (e.g., pattern-1)
    """
    manager: PatternsManager = ctx.obj["manager"]

    click.echo(f"Cleaning up pattern: {pattern_id}")

    success = manager.cleanup_pattern(pattern_id)

    if success:
        click.echo(click.style("✓ Pattern cleaned up", fg="green", bold=True))
    else:
        click.echo(click.style("✗ Cleanup failed", fg="red", bold=True))
        sys.exit(1)


@cli.command()
@click.pass_context
def cleanup_all(ctx):
    """
    Clean up all deployed patterns.
    """
    manager: PatternsManager = ctx.obj["manager"]

    click.echo("Cleaning up all deployed patterns...")

    success = manager.cleanup_all()

    if success:
        click.echo(click.style("✓ All patterns cleaned up", fg="green", bold=True))
    else:
        click.echo(click.style("✗ Some cleanups failed", fg="yellow", bold=True))


@cli.command()
@click.pass_context
def status(ctx):
    """
    Display current state of the patterns manager.
    """
    manager: PatternsManager = ctx.obj["manager"]

    status_info = manager.get_status()

    click.echo("Patterns manager status:")
    click.echo(f"  Server: {status_info['server_config']['base_url']}")
    click.echo(
        f"  Authentication: {'Yes' if status_info['server_config']['auth_required'] else 'No'}"
    )
    click.echo(f"  Deployed processes: {len(status_info['deployed_processes'])}")

    if status_info["deployed_processes"]:
        for process_id in status_info["deployed_processes"]:
            click.echo(f"    - {process_id}")

    click.echo(f"  Running jobs: {len(status_info['running_jobs'])}")

    if status_info["running_jobs"]:
        for pattern_id, job_id in status_info["running_jobs"].items():
            click.echo(f"    - {pattern_id}: {job_id}")

    click.echo(f"  Completed results: {status_info['completed_results']}")


@cli.command()
@click.pass_context
def list_patterns(ctx):
    """
    List all available patterns.
    """
    manager: PatternsManager = ctx.obj["manager"]

    patterns_dir = Path(manager.patterns_dir)
    pattern_files = list(patterns_dir.glob("pattern-*.json"))

    if not pattern_files:
        click.echo("No patterns found in patterns directory")
        return

    click.echo(f"Available patterns ({len(pattern_files)}):")

    # Sort numerically by pattern number
    sorted_files = sorted(
        pattern_files,
        key=lambda x: (
            int(x.stem.split("-")[1])
            if "-" in x.stem and x.stem.split("-")[1].isdigit()
            else 0
        ),
    )

    for pattern_file in sorted_files:
        pattern_id = pattern_file.stem
        click.echo(f"  - {pattern_id}")

        # Show details if verbose
        if ctx.obj["verbose"]:
            try:
                with open(pattern_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Display some key parameters
                if "aoi" in data:
                    click.echo(f"    AOI: {data['aoi']}")
                if "bands" in data:
                    click.echo(f"    Bands: {data['bands']}")

            except Exception as e:
                click.echo(f"    Read error: {e}")


@cli.command()
@click.argument("job_id", type=str)
@click.pass_context
def check_job(ctx, job_id: str):
    """
    Check the status of a specific job.

    JOB_ID: The job identifier to check
    """
    manager: PatternsManager = ctx.obj["manager"]

    click.echo(f"Checking job status: {job_id}")

    try:
        # Use the status API to get job information
        status_response = manager.client.status_api.get_status(job_id=job_id)

        # Extract status information
        status_str = getattr(status_response, "status", "unknown")
        process_id = getattr(status_response, "processID", "unknown")
        progress = getattr(status_response, "progress", None)
        message = getattr(status_response, "message", None)
        created = getattr(status_response, "created", None)
        started = getattr(status_response, "started", None)
        finished = getattr(status_response, "finished", None)

        click.echo(f"Job ID: {job_id}")
        click.echo(f"Process: {process_id}")
        click.echo(
            f"Status: {click.style(status_str, fg='green' if status_str == 'successful' else 'yellow' if status_str == 'running' else 'red', bold=True)}"
        )

        if progress is not None:
            click.echo(f"Progress: {progress}%")

        if message:
            click.echo(f"Message: {message}")

        if created:
            click.echo(f"Created: {created}")

        if started:
            click.echo(f"Started: {started}")

        if finished:
            click.echo(f"Finished: {finished}")

        # Show job URL for manual checking
        click.echo(f"Job URL: {manager.client.base_url}/jobs/{job_id}")

    except Exception as e:
        click.echo(click.style(f"Error checking job: {e}", fg="red"), err=True)
        sys.exit(1)


def display_summary(summary, verbose: bool = False):
    """
    Display test summary in a formatted way.

    Args:
        summary: Test summary
        verbose: Detailed display
    """
    click.echo("\n" + "=" * 50)
    click.echo("TEST SUMMARY")
    click.echo("=" * 50)

    # General statistics
    click.echo(f"Patterns tested: {summary.total_patterns}")

    if summary.successful_patterns > 0:
        click.echo(
            click.style(
                f"✓ Success: {summary.successful_patterns}", fg="green", bold=True
            )
        )

    if summary.failed_patterns > 0:
        click.echo(
            click.style(f"✗ Failed: {summary.failed_patterns}", fg="red", bold=True)
        )

    click.echo(f"Total time: {summary.total_execution_time:.1f}s")

    if verbose:
        click.echo("\nDetails by pattern:")
        for result in summary.results:
            status_icon = "✓" if result.success else "✗"
            status_color = "green" if result.success else "red"

            click.echo(
                click.style(f"  {status_icon} {result.pattern_id}", fg=status_color),
                nl=False,
            )

            if result.execution_time:
                click.echo(f" ({result.execution_time:.1f}s)", nl=False)

            if not result.success and result.message:
                click.echo(f" - {result.message}", nl=False)

            click.echo()  # New line


@cli.command()
@click.argument("pattern_ids", nargs=-1)
@click.option(
    "--output-dir",
    "-o",
    help="Output directory for JSON files",
    default="data/patterns",
    type=click.Path(),
)
@click.option("--all", "sync_all", is_flag=True, help="Sync all patterns (1-12)")
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Continue syncing even if some patterns fail",
)
@click.pass_context
def sync_params(ctx, pattern_ids, output_dir, sync_all, continue_on_error):
    """
    Synchronize pattern parameters from GitHub notebooks.

    Downloads Jupyter notebooks from the eoap/application-package-patterns
    repository, extracts the 'params' variable, and saves to local JSON files.

    Examples:

        # Sync a single pattern
        ogc-patterns-tester sync-params pattern-1

        # Sync multiple patterns
        ogc-patterns-tester sync-params pattern-1 pattern-2 pattern-3

        # Sync all patterns (1-12)
        ogc-patterns-tester --all sync-params

        # Custom output directory
        ogc-patterns-tester sync-params pattern-1 --output-dir custom/params
    """
    from .notebook_parser import NotebookParser

    output_path = Path(output_dir)

    # Determine which patterns to sync
    if sync_all:
        patterns_to_sync = [f"pattern-{i}" for i in range(1, 13)]
        click.echo("Syncing all patterns (1-12)...")
    elif pattern_ids:
        patterns_to_sync = list(pattern_ids)
    else:
        click.echo("Error: Specify pattern IDs or use --all flag", err=True)
        click.echo("\nExamples:", err=True)
        click.echo("  ogc-patterns-tester sync-params pattern-1", err=True)
        click.echo("  ogc-patterns-tester sync-params --all", err=True)
        sys.exit(1)

    click.echo(f"Output directory: {output_path}\n")

    # Create parser and sync
    parser = NotebookParser()
    results = parser.sync_all_patterns(
        patterns_to_sync, output_path, continue_on_error=continue_on_error
    )

    # Display results
    click.echo("\n" + "=" * 50)
    click.echo("Sync Results:")
    click.echo("=" * 50)

    for pattern_id, success in results.items():
        if success:
            click.echo(click.style(f"✓ {pattern_id}", fg="green"))
        else:
            click.echo(click.style(f"✗ {pattern_id}", fg="red"))

    successful = sum(1 for v in results.values() if v)
    total = len(results)

    click.echo("=" * 50)
    click.echo(f"Summary: {successful}/{total} patterns synced successfully")

    if successful < total:
        sys.exit(1)


if __name__ == "__main__":
    cli()
