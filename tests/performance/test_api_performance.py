"""
Performance tests for API endpoints
"""

import pytest
import time
import asyncio
from datetime import datetime, timezone


class TestAPIPerformance:
    """Test API performance requirements."""

    @pytest.mark.asyncio
    async def test_application_list_performance(self, client, mock_admin_auth, performance_monitor, db_with_full_data):
        """Test application list API performance."""
        performance_monitor.start()

        response = client.get("/api/v1/applications/?limit=100")

        metrics = performance_monitor.stop()

        assert response.status_code == 200
        assert metrics["elapsed_time"] < 2.0  # Must be under 2 seconds
        assert metrics["memory_delta"] < 50 * 1024 * 1024  # Less than 50MB memory increase

    @pytest.mark.asyncio
    async def test_application_create_performance(self, client, mock_admin_auth, performance_monitor):
        """Test application creation performance."""
        application_data = {
            "l2_id": f"L2_PERF_TEST_{int(time.time())}",
            "app_name": "Performance Test Application"
        }

        performance_monitor.start()

        response = client.post("/api/v1/applications/", json=application_data)

        metrics = performance_monitor.stop()

        assert response.status_code == 200
        assert metrics["elapsed_time"] < 1.0  # Must be under 1 second

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, async_client, mock_admin_auth, performance_monitor):
        """Test concurrent request handling performance."""
        async def make_request(client, endpoint):
            async with client as ac:
                response = await ac.get(endpoint)
                return response

        performance_monitor.start()

        # Create 50 concurrent requests
        tasks = [
            make_request(async_client, f"/api/v1/applications/?page={i}")
            for i in range(1, 51)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        metrics = performance_monitor.stop()

        # Check that most requests succeeded
        success_count = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code == 200
        )

        assert success_count >= 40  # At least 80% success rate
        assert metrics["elapsed_time"] < 10.0  # All requests under 10 seconds

    @pytest.mark.asyncio
    async def test_database_query_performance(self, client, mock_admin_auth, performance_monitor, db_with_full_data):
        """Test database query performance."""
        performance_monitor.start()

        # Complex query with filters and sorting
        response = client.get(
            "/api/v1/applications/?supervision_year=2024&"
            "transformation_target=AK&sort_by=app_name&limit=50"
        )

        metrics = performance_monitor.stop()

        assert response.status_code == 200
        assert metrics["elapsed_time"] < 1.5  # Database queries under 1.5 seconds

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, client, mock_admin_auth, performance_monitor, db_with_full_data):
        """Test bulk operations performance."""
        bulk_data = {
            "application_ids": list(range(1, 11)),  # 10 applications
            "update_data": {"current_status": "研发进行中"}
        }

        performance_monitor.start()

        response = client.post("/api/v1/applications/bulk/update", json=bulk_data)

        metrics = performance_monitor.stop()

        assert response.status_code == 200
        assert metrics["elapsed_time"] < 3.0  # Bulk operations under 3 seconds

    @pytest.mark.asyncio
    async def test_report_generation_performance(self, client, mock_admin_auth, performance_monitor):
        """Test report generation performance."""
        report_request = {
            "report_type": "progress_summary",
            "supervision_year": 2024,
            "include_details": True
        }

        performance_monitor.start()

        response = client.post("/api/v1/reports/progress-summary", json=report_request)

        metrics = performance_monitor.stop()

        assert response.status_code == 200
        assert metrics["elapsed_time"] < 5.0  # Report generation under 5 seconds

    @pytest.mark.asyncio
    async def test_excel_export_performance(self, client, mock_admin_auth, performance_monitor, db_with_full_data):
        """Test Excel export performance."""
        export_request = {
            "supervision_year": 2024,
            "include_subtasks": True
        }

        performance_monitor.start()

        response = client.post("/api/v1/excel/export/applications", json=export_request)

        metrics = performance_monitor.stop()

        assert response.status_code == 200
        assert metrics["elapsed_time"] < 10.0  # Excel export under 10 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, client, mock_admin_auth, performance_monitor):
        """Test memory usage stability over multiple requests."""
        initial_memory = None
        memory_samples = []

        for i in range(20):
            performance_monitor.start()

            response = client.get(f"/api/v1/applications/?page={i + 1}")

            metrics = performance_monitor.stop()

            if initial_memory is None:
                initial_memory = metrics["current_memory"]

            memory_samples.append(metrics["current_memory"])

            assert response.status_code == 200

        # Memory usage should not grow significantly
        max_memory = max(memory_samples)
        memory_growth = max_memory - initial_memory
        assert memory_growth < 100 * 1024 * 1024  # Less than 100MB growth

    @pytest.mark.asyncio
    async def test_response_time_consistency(self, client, mock_admin_auth):
        """Test response time consistency across multiple requests."""
        response_times = []

        for _ in range(10):
            start_time = time.time()

            response = client.get("/api/v1/applications/?limit=10")

            elapsed = time.time() - start_time
            response_times.append(elapsed)

            assert response.status_code == 200

        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Check consistency
        assert avg_time < 1.0  # Average under 1 second
        assert max_time < 2.0  # Maximum under 2 seconds
        assert (max_time - min_time) < 1.0  # Variation under 1 second

    @pytest.mark.asyncio
    async def test_load_testing_simulation(self, async_client, mock_admin_auth):
        """Simulate load testing with multiple concurrent users."""
        async def simulate_user_session(client, user_id):
            """Simulate a user session with multiple actions."""
            async with client as ac:
                # List applications
                await ac.get("/api/v1/applications/")

                # Get statistics
                await ac.get("/api/v1/applications/statistics")

                # Create application
                app_data = {
                    "l2_id": f"L2_LOAD_TEST_{user_id}_{int(time.time())}",
                    "app_name": f"Load Test App {user_id}"
                }
                await ac.post("/api/v1/applications/", json=app_data)

                return True

        start_time = time.time()

        # Simulate 20 concurrent users
        tasks = [
            simulate_user_session(async_client, i)
            for i in range(20)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed_time = time.time() - start_time

        # Check results
        success_count = sum(1 for r in results if r is True)

        assert success_count >= 15  # At least 75% success rate
        assert elapsed_time < 30.0  # Complete load test under 30 seconds

    @pytest.mark.asyncio
    async def test_database_connection_performance(self, client, mock_admin_auth):
        """Test database connection pooling and performance."""
        # Make rapid consecutive requests to test connection pooling
        start_time = time.time()

        responses = []
        for _ in range(10):
            response = client.get("/api/v1/applications/statistics")
            responses.append(response)

        elapsed_time = time.time() - start_time

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # Should complete quickly due to connection pooling
        assert elapsed_time < 5.0

        # Average time per request should be low
        avg_time_per_request = elapsed_time / 10
        assert avg_time_per_request < 0.5

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, client, mock_admin_auth):
        """Test that error handling doesn't significantly impact performance."""
        start_time = time.time()

        # Make requests that will result in 404 errors
        error_responses = []
        for i in range(10):
            response = client.get(f"/api/v1/applications/{1000 + i}")  # Non-existent IDs
            error_responses.append(response)

        elapsed_time = time.time() - start_time

        # All should return 404
        assert all(r.status_code == 404 for r in error_responses)

        # Error handling should be fast
        assert elapsed_time < 2.0

        # Compare with successful requests
        start_time = time.time()
        success_response = client.get("/api/v1/applications/")
        success_elapsed = time.time() - start_time

        # Error responses shouldn't be significantly slower
        avg_error_time = elapsed_time / 10
        assert avg_error_time <= success_elapsed * 2  # At most 2x slower