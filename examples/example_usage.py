#!/usr/bin/env python3
"""
Example of programmatic usage of the OGC API Processes patterns tester.

This script shows how to use the package classes directly
without going through the command-line interface.
"""

import json
from pathlib import Path

from ogc_patterns_tester import PatternsManager, ServerConfig, setup_logger


def main():
    """Main usage example."""

    # Logging configuration
    logger = setup_logger("example", level="INFO")
    logger.info("Starting example")

    # Server configuration
    server_config = ServerConfig(
        base_url="http://localhost:5000",
        auth_token=None,  # No authentication for this example
        timeout=300
    )

    # Create the patterns manager
    manager = PatternsManager(
        server_config=server_config,
        patterns_dir="data/patterns",
        download_dir="temp/cwl"
    )

    try:
        # Example 1: Execute a single pattern
        logger.info("Example 1: Single pattern execution")
        result = manager.run_single_pattern("pattern-1", cleanup=True, timeout=300)

        if result.success:
            logger.info(f"Pattern {result.pattern_id} executed successfully")
            logger.info(f"Execution time: {result.execution_time:.1f}s")
        else:
            logger.error(f"Pattern {result.pattern_id} failed: {result.message}")

        # Example 2: Execute multiple patterns
        logger.info("Example 2: Multiple patterns execution")
        pattern_ids = ["pattern-1", "pattern-2", "pattern-3"]
        summary = manager.run_multiple_patterns(pattern_ids, cleanup=True, timeout=300)

        logger.info(f"Results: {summary.successful_patterns}/{summary.total_patterns} successful")
        logger.info(f"Total time: {summary.total_execution_time:.1f}s")

        # Display details for each pattern
        for result in summary.results:
            status = "✓" if result.success else "✗"
            logger.info(f"  {status} {result.pattern_id} ({result.execution_time:.1f}s)")

        # Example 3: Manual deployment/cleanup management
        logger.info("Example 3: Manual lifecycle management")

        pattern_id = "pattern-1"

        # Deployment
        logger.info(f"Deploying {pattern_id}")
        if manager.deploy_pattern(pattern_id):
            logger.info("Deployment successful")

            # Execution
            logger.info(f"Executing {pattern_id}")
            job_id = manager.execute_pattern(pattern_id)

            if job_id:
                logger.info(f"Job created: {job_id}")

                # Monitoring
                logger.info("Monitoring job")
                result = manager.monitor_job(pattern_id, timeout=300)

                if result.success:
                    logger.info("Execution successful")
                    if result.outputs:
                        logger.info(f"Outputs produced: {len(result.outputs)}")
                else:
                    logger.error(f"Execution failed: {result.message}")

            # Cleanup
            logger.info(f"Cleaning up {pattern_id}")
            if manager.cleanup_pattern(pattern_id):
                logger.info("Cleanup successful")

        # Example 4: Status check
        logger.info("Example 4: Manager status")
        status = manager.get_status()
        logger.info(f"Deployed processes: {len(status['deployed_processes'])}")
        logger.info(f"Running jobs: {len(status['running_jobs'])}")

    except Exception as e:
        logger.error(f"Error during execution: {e}")
    finally:
        # Final cleanup
        logger.info("Final cleanup of all patterns")
        manager.cleanup_all()
        logger.info("Example completed")


def example_custom_config():
    """Example usage with custom configuration."""

    logger = setup_logger("custom_example", level="DEBUG")

    # Custom configuration
    server_config = ServerConfig(
        base_url="https://my-ogc-server.example.com",
        auth_token="my-secret-token",
        timeout=600  # Longer timeout
    )

    # Custom directories
    manager = PatternsManager(
        server_config=server_config,
        patterns_dir="my-patterns",
        download_dir="cwl-cache"
    )

    # Connection test (only displays configuration)
    status = manager.get_status()
    logger.info(f"Configured server: {status['server_config']['base_url']}")
    logger.info(f"Auth required: {status['server_config']['auth_required']}")


def save_results_example():
    """Example of saving results."""

    logger = setup_logger("save_example")

    # Simple configuration
    server_config = ServerConfig(base_url="http://localhost:5000")
    manager = PatternsManager(server_config)

    # Execute some patterns
    pattern_ids = ["pattern-1", "pattern-2"]
    summary = manager.run_multiple_patterns(pattern_ids, cleanup=True)

    # Save results
    results_file = Path("results/test_results.json")
    results_file.parent.mkdir(exist_ok=True)

    # Convert to dictionary for serialization
    results_data = {
        "total_patterns": summary.total_patterns,
        "successful_patterns": summary.successful_patterns,
        "failed_patterns": summary.failed_patterns,
        "total_execution_time": summary.total_execution_time,
        "results": [
            {
                "pattern_id": r.pattern_id,
                "success": r.success,
                "execution_time": r.execution_time,
                "message": r.message,
                "job_id": r.job_id,
                "outputs_count": len(r.outputs) if r.outputs else 0
            }
            for r in summary.results
        ]
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved in {results_file}")


if __name__ == "__main__":
    # Choose which example to run
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "custom":
            example_custom_config()
        elif sys.argv[1] == "save":
            save_results_example()
        else:
            print("Usage: python example_usage.py [custom|save]")
    else:
        main()
