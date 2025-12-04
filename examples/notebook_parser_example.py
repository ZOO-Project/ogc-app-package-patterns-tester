"""
Example: Using the NotebookParser programmatically

This example demonstrates how to use the NotebookParser class
to extract parameters from GitHub notebooks and save them locally.
"""

from pathlib import Path

from ogc_patterns_tester.notebook_parser import NotebookParser


def example_single_pattern():
    """Sync a single pattern."""
    print("Example 1: Sync single pattern")
    print("-" * 60)

    parser = NotebookParser()
    output_dir = Path("data/patterns")

    # Sync pattern-1
    success = parser.sync_pattern_params("pattern-1", output_dir)

    if success:
        print("✓ Successfully synced pattern-1")
        print(f"  File: {output_dir / 'pattern-1.json'}")
    else:
        print("✗ Failed to sync pattern-1")

    print()


def example_multiple_patterns():
    """Sync multiple patterns."""
    print("Example 2: Sync multiple patterns")
    print("-" * 60)

    parser = NotebookParser()
    output_dir = Path("data/patterns")

    patterns = ["pattern-1", "pattern-2", "pattern-3"]

    results = parser.sync_all_patterns(
        patterns,
        output_dir,
        continue_on_error=True
    )

    # Display results
    for pattern_id, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {pattern_id}")

    successful = sum(1 for v in results.values() if v)
    print(f"\nSummary: {successful}/{len(results)} patterns synced")
    print()


def example_all_patterns():
    """Sync all patterns (1-12)."""
    print("Example 3: Sync all patterns")
    print("-" * 60)

    parser = NotebookParser()
    output_dir = Path("data/patterns")

    # Generate all pattern IDs
    all_patterns = [f"pattern-{i}" for i in range(1, 13)]

    results = parser.sync_all_patterns(
        all_patterns,
        output_dir,
        continue_on_error=True
    )

    successful = sum(1 for v in results.values() if v)
    print(f"Summary: {successful}/{len(results)} patterns synced successfully")
    print()


def example_custom_extraction():
    """Download and extract params manually."""
    print("Example 4: Manual extraction")
    print("-" * 60)

    parser = NotebookParser()

    # Download notebook
    notebook = parser.download_notebook("pattern-1")

    if notebook:
        print("✓ Downloaded notebook")

        # Extract params
        params = parser.extract_params_from_notebook(notebook)

        if params:
            print("✓ Extracted params:")
            import json
            print(json.dumps(params, indent=2))
        else:
            print("✗ No params found")
    else:
        print("✗ Failed to download notebook")

    print()


def example_with_error_handling():
    """Sync with proper error handling."""
    print("Example 5: Error handling")
    print("-" * 60)

    parser = NotebookParser()
    output_dir = Path("data/patterns")

    # Try to sync a non-existent pattern
    patterns = ["pattern-1", "pattern-99", "pattern-2"]

    results = parser.sync_all_patterns(
        patterns,
        output_dir,
        continue_on_error=True  # Continue even if pattern-99 fails
    )

    # Analyze results
    successful = [p for p, ok in results.items() if ok]
    failed = [p for p, ok in results.items() if not ok]

    if successful:
        print(f"✓ Successful: {', '.join(successful)}")

    if failed:
        print(f"✗ Failed: {', '.join(failed)}")

    print()


if __name__ == "__main__":
    print("="*60)
    print("NotebookParser Examples")
    print("="*60)
    print()

    # Run examples
    example_single_pattern()
    example_multiple_patterns()
    example_all_patterns()
    example_custom_extraction()
    example_with_error_handling()

    print("="*60)
    print("All examples completed!")
    print("="*60)
