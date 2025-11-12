"""
Test runner for all unit tests.
Runs all test suites and generates a comprehensive report.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from tests import (
    test_normalize_workspace,
    test_profanity_filter,
    test_image_filtering,
    test_url_validation,
    test_filter_workspace,
    test_compatibility_limits
)


def run_all_tests(verbosity=2):
    """
    Run all test suites with specified verbosity.
    
    Args:
        verbosity (int): Level of test output detail (0-2)
    
    Returns:
        unittest.TestResult: Test results object
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test modules
    test_modules = [
        test_normalize_workspace,
        test_profanity_filter,
        test_image_filtering,
        test_url_validation,
        test_filter_workspace,
        test_compatibility_limits
    ]
    
    for module in test_modules:
        suite.addTests(loader.loadTestsFromModule(module))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


def main():
    """Main entry point for test runner"""
    print("=" * 70)
    print("Kasm Community Images Explorer - Unit Test Suite")
    print("=" * 70)
    print()
    
    result = run_all_tests(verbosity=2)
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
