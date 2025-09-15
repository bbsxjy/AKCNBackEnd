"""
Manual test script for rollback functionality
Run this after starting the FastAPI server
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.models.application import Application
from app.models.audit_log import AuditLog, AuditOperation
from app.services.audit_service import AuditService
from app.core.config import settings


async def test_rollback():
    """Test rollback functionality manually."""

    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        audit_service = AuditService()

        print("=== Manual Rollback Test ===\n")

        # Step 1: Create a test application
        print("Step 1: Creating test application...")
        test_app = Application(
            app_name="Test App for Rollback",
            l2_id="TEST_MANUAL_001",
            supervision_year=2024,
            transformation_target="AK",
            responsible_team="Test Team",
            responsible_person="Test Manager",
            overall_status="待启动",
            progress_percentage=0
        )
        db.add(test_app)
        await db.commit()
        await db.refresh(test_app)
        app_id = test_app.id
        print(f"Created application with ID: {app_id}")

        # Create INSERT audit log
        insert_audit = await audit_service.create_audit_log(
            db=db,
            table_name="applications",
            record_id=app_id,
            operation=AuditOperation.INSERT,
            old_values=None,
            new_values={
                "app_name": "Test App for Rollback",
                "l2_id": "TEST_MANUAL_001",
                "supervision_year": 2024,
                "transformation_target": "AK",
                "responsible_team": "Test Team",
                "responsible_person": "Test Manager",
                "overall_status": "待启动",
                "progress_percentage": 0
            },
            user_id=1
        )
        print(f"Created INSERT audit log with ID: {insert_audit.id}")

        # Step 2: Update the application
        print("\nStep 2: Updating application...")
        old_values = {
            "app_name": test_app.app_name,
            "overall_status": test_app.overall_status,
            "progress_percentage": test_app.progress_percentage
        }

        test_app.app_name = "Updated Test App"
        test_app.overall_status = "研发进行中"
        test_app.progress_percentage = 50
        await db.commit()
        print("Application updated")

        # Create UPDATE audit log
        update_audit = await audit_service.create_audit_log(
            db=db,
            table_name="applications",
            record_id=app_id,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values={
                "app_name": "Updated Test App",
                "overall_status": "研发进行中",
                "progress_percentage": 50
            },
            user_id=1
        )
        print(f"Created UPDATE audit log with ID: {update_audit.id}")

        # Step 3: Test rollback of UPDATE operation
        print("\nStep 3: Testing rollback of UPDATE operation...")
        try:
            rollback_result = await audit_service.rollback_change(
                db=db,
                audit_log_id=update_audit.id,
                user_id=1,
                reason="Testing rollback functionality"
            )
            print("Rollback successful!")
            print(f"  Rollback audit ID: {rollback_result['rollback_audit_id']}")
            print(f"  Operation: {rollback_result['affected_record']['operation']}")
            print(f"  Restored values: {rollback_result['affected_record']['restored_values']}")

            # Verify the rollback
            await db.refresh(test_app)
            assert test_app.app_name == "Test App for Rollback"
            assert test_app.overall_status == "待启动"
            assert test_app.progress_percentage == 0
            print("✅ Rollback verification passed!")

        except Exception as e:
            print(f"❌ Rollback failed: {e}")

        # Step 4: Test rollback of INSERT operation (delete)
        print("\nStep 4: Testing rollback of INSERT operation...")
        try:
            # First, get the current count of applications
            from sqlalchemy import select, func
            count_before = await db.scalar(select(func.count(Application.id)))

            rollback_result = await audit_service.rollback_change(
                db=db,
                audit_log_id=insert_audit.id,
                user_id=1,
                reason="Testing rollback of INSERT"
            )
            print("Rollback successful!")
            print(f"  Operation: {rollback_result['affected_record']['operation']}")

            # Verify the record was deleted
            count_after = await db.scalar(select(func.count(Application.id)))
            assert count_after == count_before - 1
            print("✅ INSERT rollback (DELETE) verification passed!")

        except Exception as e:
            print(f"❌ Rollback failed: {e}")

        # Step 5: Test rollback of DELETE operation (restore)
        print("\nStep 5: Creating another test app for DELETE rollback test...")
        test_app2 = Application(
            app_name="Test App for Delete",
            l2_id="TEST_MANUAL_002",
            supervision_year=2024,
            transformation_target="AK",
            responsible_team="Test Team 2",
            responsible_person="Test Manager 2",
            overall_status="待启动",
            progress_percentage=0
        )
        db.add(test_app2)
        await db.commit()
        await db.refresh(test_app2)
        app2_id = test_app2.id
        print(f"Created application with ID: {app2_id}")

        # Store values before deletion
        delete_old_values = {
            "id": app2_id,
            "app_name": "Test App for Delete",
            "l2_id": "TEST_MANUAL_002",
            "supervision_year": 2024,
            "transformation_target": "AK",
            "responsible_team": "Test Team 2",
            "responsible_person": "Test Manager 2",
            "overall_status": "待启动",
            "progress_percentage": 0
        }

        # Delete the application
        await db.delete(test_app2)
        await db.commit()
        print("Application deleted")

        # Create DELETE audit log
        delete_audit = await audit_service.create_audit_log(
            db=db,
            table_name="applications",
            record_id=app2_id,
            operation=AuditOperation.DELETE,
            old_values=delete_old_values,
            new_values=None,
            user_id=1
        )
        print(f"Created DELETE audit log with ID: {delete_audit.id}")

        # Test rollback of DELETE (restore)
        print("\nTesting rollback of DELETE operation...")
        try:
            rollback_result = await audit_service.rollback_change(
                db=db,
                audit_log_id=delete_audit.id,
                user_id=1,
                reason="Testing rollback of DELETE"
            )
            print("Rollback successful!")
            print(f"  Operation: {rollback_result['affected_record']['operation']}")
            print(f"  Restored values: {rollback_result['affected_record']['restored_values']}")

            # Verify the record was restored
            result = await db.execute(
                select(Application).where(Application.id == app2_id)
            )
            restored_app = result.scalar_one_or_none()
            assert restored_app is not None
            assert restored_app.app_name == "Test App for Delete"
            assert restored_app.l2_id == "TEST_MANUAL_002"
            print("✅ DELETE rollback (INSERT) verification passed!")

        except Exception as e:
            print(f"❌ Rollback failed: {e}")

        print("\n=== All rollback tests completed ===")


if __name__ == "__main__":
    print(f"Starting test at: {datetime.now()}")
    asyncio.run(test_rollback())
    print(f"Completed at: {datetime.now()}")