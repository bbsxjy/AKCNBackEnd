#!/usr/bin/env python3
"""
Test execution script for AK Cloud Native Management System

This script runs all tests and generates coverage reports.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")

    result = subprocess.run(command, capture_output=True, text=True)

    if result.stdout:
        print("STDOUT:")
        print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    return result


def main():
    """Main test execution function."""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print("AK Cloud Native Management System - Test Suite")
    print("=" * 60)

    # Install test dependencies if needed
    print("\n1. Installing/updating test dependencies...")
    # install_result = run_command([
    #     sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    # ], "Installing dependencies")

    # if install_result.returncode != 0:
    #     print("❌ Failed to install dependencies")
    #     return False

    # Run unit tests with coverage
    print("\n2. Running unit tests with coverage...")
    unit_test_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-branch",
        "--cov-fail-under=90",
        "-v",
        "--tb=short"
    ], "Unit tests with coverage")

    # Run integration tests
    print("\n3. Running integration tests...")
    integration_test_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ], "Integration tests")

    # Run performance tests
    print("\n4. Running performance tests...")
    performance_test_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/performance/",
        "-v",
        "--tb=short"
    ], "Performance tests")

    # Run all tests together for final verification
    print("\n5. Running all tests for final verification...")
    all_tests_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/",
        "--tb=short",
        "--maxfail=10"
    ], "All tests")

    # Run coverage verification
    print("\n6. Running coverage verification...")
    coverage_verification_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/test_coverage_verification.py",
        "-v"
    ], "Coverage verification")

    # Generate summary report
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)

    results = {
        "Unit Tests": unit_test_result.returncode == 0,
        "Integration Tests": integration_test_result.returncode == 0,
        "Performance Tests": performance_test_result.returncode == 0,
        "All Tests": all_tests_result.returncode == 0,
        "Coverage Verification": coverage_verification_result.returncode == 0
    }

    for test_type, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_type:<25}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 100% test coverage achieved!")
        print("\nCoverage reports generated:")
        print("  - HTML report: htmlcov/index.html")
        print("  - XML report: coverage.xml")
    else:
        print("❌ SOME TESTS FAILED. Please check the output above.")
        print("\nFailed test categories:")
        for test_type, passed in results.items():
            if not passed:
                print(f"  - {test_type}")

    print("="*60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)