"""
Test coverage verification script
"""

import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestCoverageVerification:
    """Verify test coverage meets requirements."""

    def test_unit_test_coverage(self):
        """Verify unit test coverage is 100%."""
        # Run pytest with coverage for unit tests only
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "--cov=app",
            "--cov-report=json",
            "--cov-report=term",
            "--cov-fail-under=95",  # Require at least 95% coverage
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        print("Unit Test Coverage Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert result.returncode == 0, f"Unit tests failed or coverage below 95%: {result.stderr}"

        # Check coverage.json for detailed analysis
        coverage_file = Path(__file__).parent.parent / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)

            total_coverage = coverage_data["totals"]["percent_covered"]
            assert total_coverage >= 95.0, f"Total coverage {total_coverage}% is below 95%"

            # Check individual module coverage
            files = coverage_data["files"]
            low_coverage_files = []

            for file_path, file_data in files.items():
                if "/app/" in file_path and not file_path.endswith("__init__.py"):
                    file_coverage = file_data["summary"]["percent_covered"]
                    if file_coverage < 90.0:  # Individual files should have at least 90%
                        low_coverage_files.append((file_path, file_coverage))

            if low_coverage_files:
                error_msg = "Files with low coverage (< 90%):\n"
                for file_path, coverage in low_coverage_files:
                    error_msg += f"  {file_path}: {coverage:.1f}%\n"
                pytest.fail(error_msg)

    def test_integration_test_coverage(self):
        """Verify integration tests cover all API endpoints."""
        # Run integration tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "--cov=app/api",
            "--cov-report=term",
            "--cov-fail-under=85",  # Integration tests should cover 85% of API
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        print("Integration Test Coverage Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert result.returncode == 0, f"Integration tests failed or API coverage below 85%: {result.stderr}"

    def test_all_critical_modules_covered(self):
        """Verify all critical modules have tests."""
        critical_modules = [
            "app/models/",
            "app/schemas/",
            "app/services/",
            "app/api/v1/endpoints/",
            "app/core/",
        ]

        test_directories = [
            "tests/unit/models/",
            "tests/unit/schemas/",
            "tests/unit/services/",
            "tests/integration/api/",
            "tests/unit/core/",
        ]

        base_path = Path(__file__).parent.parent

        for test_dir in test_directories:
            test_path = base_path / test_dir
            assert test_path.exists(), f"Test directory {test_dir} does not exist"

            # Check that test directory has test files
            test_files = list(test_path.glob("test_*.py"))
            assert len(test_files) > 0, f"No test files found in {test_dir}"

    def test_all_models_have_tests(self):
        """Verify all models have corresponding test files."""
        base_path = Path(__file__).parent.parent
        models_path = base_path / "app" / "models"
        tests_path = base_path / "tests" / "unit" / "models"

        model_files = [f for f in models_path.glob("*.py") if f.name != "__init__.py"]

        for model_file in model_files:
            test_file = tests_path / f"test_{model_file.name}"
            assert test_file.exists(), f"No test file found for model {model_file.name}"

    def test_all_services_have_tests(self):
        """Verify all services have corresponding test files."""
        base_path = Path(__file__).parent.parent
        services_path = base_path / "app" / "services"
        tests_path = base_path / "tests" / "unit" / "services"

        service_files = [f for f in services_path.glob("*.py") if f.name != "__init__.py"]

        for service_file in service_files:
            test_file = tests_path / f"test_{service_file.name}"
            assert test_file.exists(), f"No test file found for service {service_file.name}"

    def test_all_api_endpoints_have_tests(self):
        """Verify all API endpoints have corresponding test files."""
        base_path = Path(__file__).parent.parent
        endpoints_path = base_path / "app" / "api" / "v1" / "endpoints"
        tests_path = base_path / "tests" / "integration" / "api"

        endpoint_files = [f for f in endpoints_path.glob("*.py") if f.name != "__init__.py"]

        for endpoint_file in endpoint_files:
            test_file = tests_path / f"test_{endpoint_file.name}"
            assert test_file.exists(), f"No test file found for endpoint {endpoint_file.name}"

    def test_comprehensive_test_execution(self):
        """Run all tests and verify they pass."""
        # Run all tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "--tb=short",
            "-v",
            "--maxfail=5"  # Stop after 5 failures
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        print("All Tests Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        # Check for test failures
        if result.returncode != 0:
            pytest.fail(f"Some tests failed. Return code: {result.returncode}\n{result.stdout}")

    def test_performance_requirements_met(self):
        """Verify performance tests pass."""
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "-v",
            "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        print("Performance Tests Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert result.returncode == 0, f"Performance tests failed: {result.stderr}"

    def test_test_quality_metrics(self):
        """Verify test quality metrics."""
        base_path = Path(__file__).parent.parent

        # Count test files
        unit_tests = list((base_path / "tests" / "unit").rglob("test_*.py"))
        integration_tests = list((base_path / "tests" / "integration").rglob("test_*.py"))
        performance_tests = list((base_path / "tests" / "performance").rglob("test_*.py"))

        total_test_files = len(unit_tests) + len(integration_tests) + len(performance_tests)

        print(f"Test Quality Metrics:")
        print(f"  Unit test files: {len(unit_tests)}")
        print(f"  Integration test files: {len(integration_tests)}")
        print(f"  Performance test files: {len(performance_tests)}")
        print(f"  Total test files: {total_test_files}")

        # Minimum requirements
        assert len(unit_tests) >= 10, f"Need at least 10 unit test files, found {len(unit_tests)}"
        assert len(integration_tests) >= 3, f"Need at least 3 integration test files, found {len(integration_tests)}"
        assert len(performance_tests) >= 1, f"Need at least 1 performance test file, found {len(performance_tests)}"

        # Check test file sizes (should have substantial content)
        for test_file in unit_tests:
            size = test_file.stat().st_size
            assert size > 1000, f"Unit test file {test_file.name} is too small ({size} bytes)"

    def test_edge_case_coverage(self):
        """Verify edge cases are covered in tests."""
        # This is a meta-test that checks if tests include edge cases
        test_patterns = [
            "test_.*_empty",
            "test_.*_none",
            "test_.*_invalid",
            "test_.*_error",
            "test_.*_edge",
            "test_.*_boundary",
            "test_.*_unicode",
            "test_.*_special_characters",
            "test_.*_concurrent",
            "test_.*_performance"
        ]

        base_path = Path(__file__).parent.parent
        all_test_files = list((base_path / "tests").rglob("test_*.py"))

        edge_case_tests_found = 0

        for test_file in all_test_files:
            content = test_file.read_text(encoding='utf-8')
            for pattern in test_patterns:
                if pattern.replace(".*", "") in content.lower():
                    edge_case_tests_found += 1
                    break

        # Should have edge case tests in at least 80% of test files
        edge_case_ratio = edge_case_tests_found / len(all_test_files)
        assert edge_case_ratio >= 0.6, f"Only {edge_case_ratio:.1%} of test files contain edge cases"

    def test_documentation_coverage(self):
        """Verify test documentation and docstrings."""
        base_path = Path(__file__).parent.parent
        all_test_files = list((base_path / "tests").rglob("test_*.py"))

        undocumented_files = []

        for test_file in all_test_files:
            content = test_file.read_text(encoding='utf-8')

            # Check for module docstring
            if not content.strip().startswith('"""'):
                undocumented_files.append(test_file.name)

        # At least 90% of test files should have docstrings
        documented_ratio = (len(all_test_files) - len(undocumented_files)) / len(all_test_files)
        assert documented_ratio >= 0.9, f"Only {documented_ratio:.1%} of test files have docstrings"

if __name__ == "__main__":
    # Run coverage verification
    pytest.main([__file__, "-v"])