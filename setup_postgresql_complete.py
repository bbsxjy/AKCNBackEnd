"""
Complete PostgreSQL setup - creates database, tables, and initial data
Run this after creating the PostgreSQL user and database
"""

import psycopg2
from psycopg2 import sql
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_database_sync():
    """Setup database using psycopg2 (sync)."""

    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)

    # Connection parameters
    conn_params = {
        "host": "localhost",
        "port": 5432,
        "user": "akcn_user",
        "password": "akcn_password",
        "database": "akcn_dev_db"
    }

    try:
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        print("[OK] Connected to database")

        # Check if tables exist
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]

        if table_count > 0:
            print(f"[INFO] Found {table_count} existing tables")
            response = input("Drop and recreate all tables? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return False

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Cannot connect to database: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Database 'akcn_dev_db' exists")
        print("3. User 'akcn_user' exists with password 'akcn_password'")
        print("\nTo create database and user, run as postgres user:")
        print("""
psql -U postgres
CREATE USER akcn_user WITH PASSWORD 'akcn_password';
CREATE DATABASE akcn_dev_db WITH OWNER = akcn_user;
GRANT ALL PRIVILEGES ON DATABASE akcn_dev_db TO akcn_user;
\\q
""")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def create_tables_and_data():
    """Create tables and insert initial data using SQLAlchemy."""

    from sqlalchemy import text
    from app.db.session import engine, AsyncSessionLocal
    from app.core.database import Base

    # Import all models to ensure they are registered with Base
    from app.models.user import User, UserRole
    from app.models.application import Application, ApplicationStatus, TransformationTarget
    from app.models.subtask import SubTask, SubTaskStatus
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    import datetime

    print("\n[STEP 1] Creating database tables...")

    try:
        # Create all tables
        async with engine.begin() as conn:
            # Drop all tables first
            await conn.run_sync(Base.metadata.drop_all)
            print("[INFO] Dropped existing tables")

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] Created all tables")

            # List created tables
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"[INFO] Created tables: {', '.join(tables)}")

    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        await engine.dispose()
        return False

    print("\n[STEP 2] Inserting initial data...")

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select, text

            # Check if data already exists
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("[INFO] Data already exists, skipping insertion")
                await engine.dispose()
                return True

            # Create users
            print("Creating users...")
            admin_user = User(
                sso_user_id="SSO001",
                username="admin",
                email="admin@test.com",
                full_name="System Administrator",
                department="IT Platform",
                role=UserRole.ADMIN,
                is_active=True
            )

            manager_user = User(
                sso_user_id="SSO002",
                username="manager",
                email="manager@test.com",
                full_name="Project Manager",
                department="Development",
                role=UserRole.MANAGER,
                is_active=True
            )

            editor_user = User(
                sso_user_id="SSO003",
                username="editor",
                email="editor@test.com",
                full_name="Content Editor",
                department="Operations",
                role=UserRole.EDITOR,
                is_active=True
            )

            viewer_user = User(
                sso_user_id="SSO004",
                username="viewer",
                email="viewer@test.com",
                full_name="Read Only User",
                department="Business",
                role=UserRole.VIEWER,
                is_active=True
            )

            session.add_all([admin_user, manager_user, editor_user, viewer_user])
            await session.flush()
            print("[OK] Created 4 users")

            # Create applications
            print("Creating applications...")
            app1 = Application(
                l2_id="APP001",
                app_name="Customer Management System",
                supervision_year=2025,
                transformation_target=TransformationTarget.AK,
                is_ak_completed=False,
                is_cloud_native_completed=False,
                current_stage="Development Phase",
                overall_status=ApplicationStatus.DEV_IN_PROGRESS,
                responsible_team="Platform Team",
                responsible_person="Zhang Wei",
                progress_percentage=0,
                planned_requirement_date=datetime.date(2025, 1, 1),
                planned_release_date=datetime.date(2025, 3, 15),
                planned_tech_online_date=datetime.date(2025, 4, 1),
                planned_biz_online_date=datetime.date(2025, 5, 1),
                actual_requirement_date=datetime.date(2025, 1, 10),
                is_delayed=False,
                delay_days=0,
                notes="Core customer management functions being migrated to AK platform",
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            app2 = Application(
                l2_id="APP002",
                app_name="Order Processing Platform",
                supervision_year=2025,
                transformation_target=TransformationTarget.CLOUD_NATIVE,
                is_ak_completed=False,
                is_cloud_native_completed=False,
                current_stage="Planning",
                overall_status=ApplicationStatus.NOT_STARTED,
                responsible_team="Development Team",
                responsible_person="Li Ming",
                progress_percentage=0,
                planned_requirement_date=datetime.date(2025, 3, 1),
                planned_release_date=datetime.date(2025, 6, 30),
                planned_tech_online_date=datetime.date(2025, 7, 15),
                planned_biz_online_date=datetime.date(2025, 8, 1),
                is_delayed=False,
                delay_days=0,
                notes="Full cloud-native transformation planned",
                created_by=manager_user.id,
                updated_by=manager_user.id
            )

            app3 = Application(
                l2_id="APP003",
                app_name="Financial Reporting System",
                supervision_year=2025,
                transformation_target=TransformationTarget.AK,
                is_ak_completed=True,
                is_cloud_native_completed=False,
                current_stage="Business Validation",
                overall_status=ApplicationStatus.BIZ_ONLINE,
                responsible_team="Finance Tech",
                responsible_person="Wang Fang",
                progress_percentage=0,
                planned_requirement_date=datetime.date(2024, 10, 1),
                planned_release_date=datetime.date(2024, 12, 15),
                planned_tech_online_date=datetime.date(2025, 1, 10),
                planned_biz_online_date=datetime.date(2025, 2, 1),
                actual_requirement_date=datetime.date(2024, 10, 5),
                actual_release_date=datetime.date(2024, 12, 20),
                actual_tech_online_date=datetime.date(2025, 1, 15),
                is_delayed=True,
                delay_days=5,
                notes="In final business validation phase",
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            app4 = Application(
                l2_id="APP004",
                app_name="HR Management Portal",
                supervision_year=2024,
                transformation_target=TransformationTarget.AK,
                is_ak_completed=True,
                is_cloud_native_completed=False,
                current_stage="Completed",
                overall_status=ApplicationStatus.COMPLETED,
                responsible_team="HR Technology",
                responsible_person="Chen Jun",
                progress_percentage=0,
                planned_requirement_date=datetime.date(2024, 6, 1),
                planned_release_date=datetime.date(2024, 8, 15),
                planned_tech_online_date=datetime.date(2024, 9, 1),
                planned_biz_online_date=datetime.date(2024, 10, 1),
                actual_requirement_date=datetime.date(2024, 6, 1),
                actual_release_date=datetime.date(2024, 8, 10),
                actual_tech_online_date=datetime.date(2024, 8, 28),
                actual_biz_online_date=datetime.date(2024, 9, 25),
                is_delayed=False,
                delay_days=0,
                notes="Successfully completed AK transformation",
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            session.add_all([app1, app2, app3, app4])
            await session.flush()
            print("[OK] Created 4 applications")

            # Create subtasks
            print("Creating subtasks...")
            subtask1 = SubTask(
                application_id=app1.id,
                module_name="User Authentication Module",
                sub_target="AK",
                version_name="v1.0.0",
                task_status=SubTaskStatus.COMPLETED,
                progress_percentage=0,
                is_blocked=False,
                planned_requirement_date=datetime.date(2025, 1, 1),
                planned_release_date=datetime.date(2025, 2, 1),
                planned_tech_online_date=datetime.date(2025, 2, 15),
                planned_biz_online_date=datetime.date(2025, 3, 1),
                actual_requirement_date=datetime.date(2025, 1, 10),
                actual_release_date=datetime.date(2025, 2, 5),
                requirements="Implement OAuth2.0 and JWT authentication",
                technical_notes="Using Spring Security with JWT tokens",
                assigned_to="Zhang Wei",
                reviewer="Li Ming",
                priority=3,
                estimated_hours=120,
                actual_hours=130,
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            subtask2 = SubTask(
                application_id=app1.id,
                module_name="Customer Data Management",
                sub_target="AK",
                version_name="v1.0.0",
                task_status=SubTaskStatus.DEV_IN_PROGRESS,
                progress_percentage=0,
                is_blocked=False,
                planned_requirement_date=datetime.date(2025, 2, 1),
                planned_release_date=datetime.date(2025, 3, 15),
                planned_tech_online_date=datetime.date(2025, 4, 1),
                planned_biz_online_date=datetime.date(2025, 5, 1),
                actual_requirement_date=datetime.date(2025, 2, 5),
                requirements="CRUD operations for customer data with search and filtering",
                technical_notes="Implementing with Spring Data JPA and PostgreSQL",
                assigned_to="Wang Lei",
                reviewer="Zhang Wei",
                priority=2,
                estimated_hours=200,
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            subtask3 = SubTask(
                application_id=app1.id,
                module_name="Reporting Module",
                sub_target="AK",
                version_name="v1.0.0",
                task_status=SubTaskStatus.NOT_STARTED,
                progress_percentage=0,
                is_blocked=False,
                planned_requirement_date=datetime.date(2025, 3, 15),
                planned_release_date=datetime.date(2025, 4, 15),
                planned_tech_online_date=datetime.date(2025, 4, 30),
                planned_biz_online_date=datetime.date(2025, 5, 15),
                requirements="Generate customer reports and analytics",
                assigned_to="Liu Yang",
                priority=1,
                estimated_hours=160,
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            session.add_all([subtask1, subtask2, subtask3])
            await session.flush()
            print("[OK] Created 3 subtasks")

            # Create notifications
            print("Creating notifications...")
            notification1 = Notification(
                user_id=admin_user.id,
                title="System Initialized",
                message="PostgreSQL database has been successfully initialized with test data.",
                type="info",
                is_read=False
            )

            notification2 = Notification(
                user_id=admin_user.id,
                title="Application Delayed",
                message="APP003 - Financial Reporting System is delayed by 5 days.",
                type="warning",
                is_read=False
            )

            session.add_all([notification1, notification2])
            await session.flush()
            print("[OK] Created 2 notifications")

            # Create audit logs
            print("Creating audit logs...")
            audit_log1 = AuditLog(
                table_name="applications",
                record_id=app1.id,
                operation="INSERT",
                old_values=None,
                new_values={"l2_id": "APP001", "app_name": "Customer Management System"},
                user_id=admin_user.id,
                user_ip="127.0.0.1",
                user_agent="Python/init_script"
            )

            audit_log2 = AuditLog(
                table_name="applications",
                record_id=app3.id,
                operation="UPDATE",
                old_values={"status": "DEV_IN_PROGRESS"},
                new_values={"status": "BIZ_ONLINE"},
                user_id=admin_user.id,
                user_ip="127.0.0.1",
                user_agent="Python/init_script"
            )

            session.add_all([audit_log1, audit_log2])
            await session.flush()
            print("[OK] Created audit logs")

            # Commit all changes
            await session.commit()
            print("\n[OK] All data committed successfully")

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Failed to insert data: {e}")
            import traceback
            traceback.print_exc()
            await engine.dispose()
            return False

    # Verify the setup
    print("\n[STEP 3] Verifying database setup...")

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select, func, text

            # Count records
            user_count = await session.execute(select(func.count(User.id)))
            app_count = await session.execute(select(func.count(Application.id)))
            subtask_count = await session.execute(select(func.count(SubTask.id)))
            audit_count = await session.execute(select(func.count(AuditLog.id)))
            notification_count = await session.execute(select(func.count(Notification.id)))

            print("\n[VERIFICATION] Database Statistics:")
            print(f"  Users: {user_count.scalar()}")
            print(f"  Applications: {app_count.scalar()}")
            print(f"  Subtasks: {subtask_count.scalar()}")
            print(f"  Notifications: {notification_count.scalar()}")
            print(f"  Audit Logs: {audit_count.scalar()}")

            # Test a query
            result = await session.execute(
                select(Application)
                .where(Application.overall_status == ApplicationStatus.DEV_IN_PROGRESS)
            )
            dev_apps = result.scalars().all()
            print(f"  Applications in development: {len(dev_apps)}")

            print("\n[OK] Database verification completed")

        except Exception as e:
            print(f"[ERROR] Verification failed: {e}")
            await engine.dispose()
            return False

    await engine.dispose()
    return True


async def main():
    """Main setup function."""

    # First check database connection
    if not setup_database_sync():
        return False

    # Create tables and insert data
    if not await create_tables_and_data():
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] PostgreSQL database setup completed!")
    print("=" * 60)
    print("\nDatabase: akcn_dev_db")
    print("User: akcn_user")
    print("Password: akcn_password")
    print("\nYou can now start the API server:")
    print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\nTest users:")
    print("  - Admin: admin@test.com (token: token_1_admin_full_access_test_2024)")
    print("  - Manager: manager@test.com")
    print("  - Editor: editor@test.com")
    print("  - Viewer: viewer@test.com")
    print("\nAPI documentation: http://localhost:8000/docs")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[ABORT] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)