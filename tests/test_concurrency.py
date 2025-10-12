"""
Test concurrency control mechanisms
"""

import asyncio
import sys
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.application import Application
from app.utils.concurrency import (
    with_retry,
    acquire_row_lock,
    LockContext,
    update_with_version_check,
    OptimisticLockError
)


async def test_optimistic_locking():
    """Test optimistic locking with version field"""
    print("\n" + "="*80)
    print("Test 1: Optimistic Locking (Version Control)")
    print("="*80)

    async with AsyncSessionLocal() as db:
        # Get an application
        result = await db.execute(select(Application).limit(1))
        app = result.scalar_one_or_none()

        if not app:
            print("[X] No application found for testing")
            return

        print(f"[OK] Found application: {app.l2_id} (version: {app.version})")

        # Simulate concurrent update
        current_version = app.version
        print(f"[OK] Current version: {current_version}")

        # First update (should succeed)
        try:
            await update_with_version_check(
                db,
                app,
                expected_version=current_version,
                current_status="Test Update 1"
            )
            await db.refresh(app)
            print(f"[OK] First update succeeded, new version: {app.version}")
        except OptimisticLockError as e:
            print(f"[X] First update failed: {e}")

        # Second update with old version (should fail)
        try:
            await update_with_version_check(
                db,
                app,
                expected_version=current_version,  # Using old version
                current_status="Test Update 2"
            )
            print(f"[X] Second update should have failed but didn't!")
        except OptimisticLockError as e:
            print(f"[OK] Second update correctly failed: {e}")


async def test_pessimistic_locking():
    """Test pessimistic locking with SELECT FOR UPDATE"""
    print("\n" + "="*80)
    print("Test 2: Pessimistic Locking (SELECT FOR UPDATE)")
    print("="*80)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).limit(1))
        app = result.scalar_one_or_none()

        if not app:
            print("[X] No application found for testing")
            return

        print(f"[OK] Found application: {app.l2_id}")

        # Test with acquire_row_lock (LockContext requires transaction context)
        app_to_lock = await acquire_row_lock(db, Application, app.id, for_update=True)
        if app_to_lock:
            print(f"[OK] Successfully locked application {app_to_lock.l2_id}")
            old_status = app_to_lock.current_status
            app_to_lock.current_status = "Locked Test"
            await db.commit()
            await db.refresh(app_to_lock)
            print(f"[OK] Updated status from '{old_status}' to '{app_to_lock.current_status}'")
        else:
            print("[X] Failed to acquire lock")


async def test_concurrent_updates():
    """Test concurrent updates with retry mechanism"""
    print("\n" + "="*80)
    print("Test 3: Concurrent Updates with Retry")
    print("="*80)

    @with_retry(max_retries=3, retry_delay=0.05)
    async def update_status(app_id: int, status: str, user_num: int):
        async with AsyncSessionLocal() as db:
            async with db.begin():
                app = await acquire_row_lock(db, Application, app_id)
                if app:
                    print(f"  User {user_num}: Updating to '{status}'")
                    app.current_status = status
                    await db.commit()
                    return True
        return False

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).limit(1))
        app = result.scalar_one_or_none()

        if not app:
            print("[X] No application found for testing")
            return

        app_id = app.id
        print(f"[OK] Testing concurrent updates on application {app.l2_id}")

        # Simulate 5 concurrent users updating the same application
        tasks = [
            update_status(app_id, f"状态_{i}", i)
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        error_count = sum(1 for r in results if isinstance(r, Exception))

        print(f"\n[OK] Results: {success_count} succeeded, {error_count} errors")

        # Show final status
        await db.refresh(app)
        print(f"[OK] Final status: {app.current_status}")


async def test_read_write_split():
    """Test read/write database splitting"""
    print("\n" + "="*80)
    print("Test 4: Read/Write Split Configuration")
    print("="*80)

    from app.core.database import async_engine, async_read_engine
    from app.core.config import settings

    print(f"[OK] Read/Write Split Enabled: {settings.ENABLE_READ_WRITE_SPLIT}")
    print(f"[OK] Write Engine URL: {async_engine.url}")
    print(f"[OK] Read Engine URL: {async_read_engine.url}")

    if async_engine == async_read_engine:
        print("[!] Using same engine for read and write (split not configured)")
    else:
        print("[OK] Using separate engines for read and write")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DATABASE CONCURRENCY CONTROL TESTS")
    print("="*80)

    try:
        await test_read_write_split()
        await test_optimistic_locking()
        await test_pessimistic_locking()
        await test_concurrent_updates()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)

    except Exception as e:
        print(f"\n[X] Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
