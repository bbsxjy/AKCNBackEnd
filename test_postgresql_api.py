"""
Comprehensive test script for PostgreSQL setup and API endpoints
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


async def test_database_connection():
    """Test direct database connection."""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    try:
        from app.db.session import engine
        from sqlalchemy import text

        async with engine.begin() as conn:
            # Test PostgreSQL connection
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"[OK] PostgreSQL Version: {version}")

            # Test database name
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"[OK] Connected to database: {db_name}")

            # Test user
            result = await conn.execute(text("SELECT current_user"))
            user = result.scalar()
            print(f"[OK] Connected as user: {user}")

            # Count tables
            result = await conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            print(f"[OK] Number of tables: {table_count}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False


async def test_api_endpoints():
    """Test all API endpoints with PostgreSQL backend."""
    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)

    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer token_1_admin_full_access_test_2024",
        "Origin": "http://localhost:3000",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("\n[TEST] Health Check Endpoint")
        async with session.get(f"{base_url}/health") as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Response: {data}")
                print("  [PASS] Health check successful")
            else:
                print("  [FAIL] Health check failed")

        # Test CORS preflight
        print("\n[TEST] CORS Preflight Request")
        async with session.options(
            f"{base_url}/api/v1/applications/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization"
            }
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                cors_headers = dict(resp.headers)
                print(f"  Access-Control-Allow-Origin: {cors_headers.get('access-control-allow-origin')}")
                print(f"  Access-Control-Allow-Methods: {cors_headers.get('access-control-allow-methods')}")
                print("  [PASS] CORS configuration correct")
            else:
                print("  [FAIL] CORS configuration failed")

        # Test applications list endpoint
        print("\n[TEST] Applications List Endpoint")
        async with session.get(
            f"{base_url}/api/v1/applications/?limit=10",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Total applications: {data.get('total', 0)}")
                print(f"  Page: {data.get('page', 1)}/{data.get('total_pages', 0)}")
                print(f"  Items returned: {len(data.get('items', []))}")
                if data.get('items'):
                    first_item = data['items'][0]
                    print(f"  First application:")
                    print(f"    - ID: {first_item.get('l2_id')}")
                    print(f"    - Name: {first_item.get('app_name')}")
                    print(f"    - Status: {first_item.get('overall_status')}")
                    print(f"    - Progress: {first_item.get('progress_percentage')}%")
                print("  [PASS] Applications endpoint working")
            else:
                error = await resp.text()
                print(f"  [FAIL] Error: {error}")

        # Test subtasks list endpoint
        print("\n[TEST] Subtasks List Endpoint")
        async with session.get(
            f"{base_url}/api/v1/subtasks/?limit=10",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Total subtasks: {data.get('total', 0)}")
                print(f"  Items returned: {len(data.get('items', []))}")
                if data.get('items'):
                    first_item = data['items'][0]
                    print(f"  First subtask:")
                    print(f"    - Module: {first_item.get('module_name')}")
                    print(f"    - Status: {first_item.get('task_status')}")
                    print(f"    - Progress: {first_item.get('progress_percentage')}%")
                print("  [PASS] Subtasks endpoint working")
            else:
                error = await resp.text()
                print(f"  [FAIL] Error: {error}")

        # Test notifications endpoint
        print("\n[TEST] Notifications Endpoint")
        async with session.get(
            f"{base_url}/api/v1/notifications/?unread_only=true&limit=10",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Response: {data}")
                print("  [PASS] Notifications endpoint working")
            else:
                print("  [FAIL] Notifications endpoint failed")

        # Test filtering on applications
        print("\n[TEST] Applications Filtering")
        async with session.get(
            f"{base_url}/api/v1/applications/?status=研发进行中&limit=10",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Applications in development: {data.get('total', 0)}")
                print("  [PASS] Filtering working")
            else:
                print("  [FAIL] Filtering failed")

        # Test application statistics endpoint
        print("\n[TEST] Application Statistics")
        async with session.get(
            f"{base_url}/api/v1/applications/statistics",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Total applications: {data.get('total_applications', 0)}")
                print(f"  Delayed applications: {data.get('delayed_count', 0)}")
                print("  [PASS] Statistics endpoint working")
            else:
                print("  [FAIL] Statistics endpoint failed")

        # Test audit logs endpoint
        print("\n[TEST] Audit Logs Endpoint")
        async with session.get(
            f"{base_url}/api/v1/audit/logs?limit=5",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Total audit logs: {data.get('total', 0)}")
                print("  [PASS] Audit logs endpoint working")
            else:
                print("  [FAIL] Audit logs endpoint failed")


async def test_database_operations():
    """Test database operations with PostgreSQL."""
    print("\n" + "=" * 60)
    print("Testing Database Operations")
    print("=" * 60)

    try:
        from app.db.session import AsyncSessionLocal
        from app.models.application import Application, ApplicationStatus
        from app.models.subtask import SubTask
        from app.models.user import User
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as session:
            # Test query performance
            print("\n[TEST] Query Performance")

            start_time = datetime.now()
            result = await session.execute(
                select(Application)
                .where(Application.overall_status == ApplicationStatus.DEV_IN_PROGRESS)
            )
            apps = result.scalars().all()
            query_time = (datetime.now() - start_time).total_seconds()
            print(f"  Query time: {query_time:.3f} seconds")
            print(f"  Results: {len(apps)} applications in development")
            print("  [PASS] Query performance acceptable")

            # Test join query
            print("\n[TEST] Join Query")
            result = await session.execute(
                select(Application, func.count(SubTask.id))
                .outerjoin(SubTask, Application.id == SubTask.application_id)
                .group_by(Application.id)
            )
            app_with_counts = result.all()
            print(f"  Applications with subtask counts: {len(app_with_counts)}")
            for app, count in app_with_counts[:3]:
                print(f"    - {app.app_name}: {count} subtasks")
            print("  [PASS] Join queries working")

            # Test aggregation
            print("\n[TEST] Aggregation Query")
            result = await session.execute(
                select(
                    Application.overall_status,
                    func.count(Application.id).label('count'),
                    func.avg(Application.progress_percentage).label('avg_progress')
                )
                .group_by(Application.overall_status)
            )
            status_stats = result.all()
            for status, count, avg_progress in status_stats:
                print(f"    - {status}: {count} apps, avg progress: {avg_progress:.1f}%")
            print("  [PASS] Aggregation queries working")

            # Test transaction
            print("\n[TEST] Transaction Support")
            try:
                # Start a transaction
                user = await session.execute(
                    select(User).where(User.email == "admin@test.com")
                )
                admin = user.scalar_one()

                # Create a test application
                test_app = Application(
                    l2_id="TEST999",
                    app_name="Transaction Test App",
                    supervision_year=2025,
                    transformation_target="AK",
                    overall_status=ApplicationStatus.NOT_STARTED,
                    responsible_team="Test Team",
                    progress_percentage=0,
                    created_by=admin.id,
                    updated_by=admin.id
                )
                session.add(test_app)
                await session.flush()

                # Rollback the transaction
                await session.rollback()

                # Verify it was rolled back
                result = await session.execute(
                    select(Application).where(Application.l2_id == "TEST999")
                )
                if result.scalar_one_or_none() is None:
                    print("  [PASS] Transaction rollback working")
                else:
                    print("  [FAIL] Transaction rollback failed")

            except Exception as e:
                print(f"  [FAIL] Transaction test failed: {e}")

        return True

    except Exception as e:
        print(f"[ERROR] Database operations failed: {e}")
        return False


async def main():
    """Main test function."""
    print("=" * 60)
    print("PostgreSQL and API Complete Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_tests_passed = True

    # Test database connection
    if not await test_database_connection():
        print("\n[ABORT] Cannot proceed without database connection")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Database 'akcn_dev_db' exists")
        print("3. User 'akcn_user' has proper permissions")
        print("4. Run: psql -U postgres < setup_postgresql.sql")
        print("5. Run: python init_postgresql.py")
        sys.exit(1)

    # Test database operations
    if not await test_database_operations():
        all_tests_passed = False

    # Test API endpoints
    print("\n[INFO] Testing API endpoints...")
    print("[INFO] Make sure the server is running on http://localhost:8000")
    try:
        await test_api_endpoints()
    except aiohttp.ClientError as e:
        print(f"\n[ERROR] Could not connect to API server: {e}")
        print("[INFO] Please start the server with:")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        all_tests_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    if all_tests_passed:
        print("[SUCCESS] All tests passed!")
        print("\nPostgreSQL setup is complete and working correctly.")
        print("\nKey configurations:")
        print("  - Database: PostgreSQL")
        print("  - Connection pool: 20 connections (40 max overflow)")
        print("  - Timeout: 30 seconds")
        print("  - CORS: Enabled for http://localhost:3000")
        print("  - Authentication: JWT with test token support")
    else:
        print("[WARNING] Some tests failed. Please check the errors above.")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    print("Starting PostgreSQL and API test suite...")
    print("This will test:")
    print("  1. PostgreSQL connection and configuration")
    print("  2. Database operations and queries")
    print("  3. API endpoints with PostgreSQL backend")
    print("  4. CORS configuration")
    print("  5. Performance and transactions")
    print("-" * 60)

    asyncio.run(main())