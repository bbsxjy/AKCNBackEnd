"""
PostgreSQL Database Initialization Script
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.session import engine, AsyncSessionLocal, Base
from app.models.user import User, UserRole
from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.audit_log import AuditLog
from app.core.config import settings
import datetime


async def check_database_connection():
    """Check if we can connect to PostgreSQL."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"[OK] Connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"[ERROR] Cannot connect to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Run 'psql -U postgres < setup_postgresql.sql' to create databases")
        print("3. Check DATABASE_URL in .env file")
        return False


async def create_tables():
    """Create all tables using SQLAlchemy models."""
    try:
        async with engine.begin() as conn:
            # Drop all tables first for clean setup
            await conn.run_sync(Base.metadata.drop_all)
            print("[INFO] Dropped existing tables")

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] Created all tables")

            # Verify tables were created
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
        raise


async def insert_initial_data():
    """Insert initial data into the database."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            from sqlalchemy import select
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("[WARNING] Data already exists, skipping data insertion")
                return

            # Create users
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
            applications = []

            # Application 1 - In Development
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
                progress_percentage=45,
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
            applications.append(app1)

            # Application 2 - Not Started
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
            applications.append(app2)

            # Application 3 - Business Online
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
                progress_percentage=85,
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
            applications.append(app3)

            # Application 4 - Completed
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
                progress_percentage=100,
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
            applications.append(app4)

            session.add_all(applications)
            await session.flush()
            print(f"[OK] Created {len(applications)} applications")

            # Create subtasks
            subtasks = []

            # Subtasks for app1
            subtask1 = SubTask(
                application_id=app1.id,
                module_name="User Authentication Module",
                sub_target="AK",
                version_name="v1.0.0",
                task_status=SubTaskStatus.COMPLETED,
                progress_percentage=100,
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
            subtasks.append(subtask1)

            subtask2 = SubTask(
                application_id=app1.id,
                module_name="Customer Data Management",
                sub_target="AK",
                version_name="v1.0.0",
                task_status=SubTaskStatus.DEV_IN_PROGRESS,
                progress_percentage=60,
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
            subtasks.append(subtask2)

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
            subtasks.append(subtask3)

            # Subtasks for app2
            subtask4 = SubTask(
                application_id=app2.id,
                module_name="Order Service",
                sub_target="Cloud Native",
                version_name="v2.0.0",
                task_status=SubTaskStatus.NOT_STARTED,
                progress_percentage=0,
                is_blocked=False,
                planned_requirement_date=datetime.date(2025, 3, 1),
                planned_release_date=datetime.date(2025, 5, 1),
                planned_tech_online_date=datetime.date(2025, 6, 1),
                planned_biz_online_date=datetime.date(2025, 7, 1),
                requirements="Microservice for order processing",
                technical_notes="Using Kubernetes and Docker",
                assigned_to="Li Ming",
                priority=3,
                estimated_hours=300,
                created_by=manager_user.id,
                updated_by=manager_user.id
            )
            subtasks.append(subtask4)

            subtask5 = SubTask(
                application_id=app2.id,
                module_name="Payment Integration",
                sub_target="Cloud Native",
                version_name="v2.0.0",
                task_status=SubTaskStatus.NOT_STARTED,
                progress_percentage=0,
                is_blocked=True,
                block_reason="Waiting for payment gateway approval",
                planned_requirement_date=datetime.date(2025, 4, 1),
                planned_release_date=datetime.date(2025, 6, 1),
                planned_tech_online_date=datetime.date(2025, 6, 15),
                planned_biz_online_date=datetime.date(2025, 7, 15),
                requirements="Integrate with payment gateways",
                assigned_to="Zhao Chen",
                priority=2,
                estimated_hours=240,
                created_by=manager_user.id,
                updated_by=manager_user.id
            )
            subtasks.append(subtask5)

            # Subtasks for app3
            subtask6 = SubTask(
                application_id=app3.id,
                module_name="Financial Report Engine",
                sub_target="AK",
                version_name="v1.2.0",
                task_status=SubTaskStatus.TESTING,
                progress_percentage=90,
                is_blocked=False,
                planned_requirement_date=datetime.date(2024, 10, 1),
                planned_release_date=datetime.date(2024, 12, 1),
                planned_tech_online_date=datetime.date(2025, 1, 10),
                planned_biz_online_date=datetime.date(2025, 2, 1),
                actual_requirement_date=datetime.date(2024, 10, 5),
                actual_release_date=datetime.date(2024, 12, 10),
                actual_tech_online_date=datetime.date(2025, 1, 15),
                requirements="Generate financial reports with real-time data",
                technical_notes="Using Apache Spark for data processing",
                test_notes="Performance testing in progress",
                assigned_to="Wang Fang",
                reviewer="Chen Jun",
                priority=3,
                estimated_hours=280,
                actual_hours=290,
                created_by=admin_user.id,
                updated_by=admin_user.id
            )
            subtasks.append(subtask6)

            session.add_all(subtasks)
            await session.flush()
            print(f"[OK] Created {len(subtasks)} subtasks")

            # Create audit logs
            audit_log1 = AuditLog(
                table_name="applications",
                record_id=app1.id,
                action="CREATE",
                old_values=None,
                new_values={"l2_id": "APP001", "app_name": "Customer Management System"},
                user_id=admin_user.id,
                ip_address="127.0.0.1",
                user_agent="Python/init_script"
            )

            audit_log2 = AuditLog(
                table_name="applications",
                record_id=app3.id,
                action="UPDATE",
                old_values={"status": "DEV_IN_PROGRESS"},
                new_values={"status": "BIZ_ONLINE"},
                user_id=admin_user.id,
                ip_address="127.0.0.1",
                user_agent="Python/init_script"
            )

            session.add_all([audit_log1, audit_log2])
            await session.flush()
            print("[OK] Created audit logs")

            # Commit all changes
            await session.commit()
            print("[OK] All data committed successfully")

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Failed to insert data: {e}")
            raise


async def verify_setup():
    """Verify the database setup is complete."""
    async with AsyncSessionLocal() as session:
        try:
            # Count records in each table
            from sqlalchemy import select, func

            user_count = await session.execute(select(func.count(User.id)))
            app_count = await session.execute(select(func.count(Application.id)))
            subtask_count = await session.execute(select(func.count(SubTask.id)))
            audit_count = await session.execute(select(func.count(AuditLog.id)))

            print("\n[VERIFICATION] Database Statistics:")
            print(f"  Users: {user_count.scalar()}")
            print(f"  Applications: {app_count.scalar()}")
            print(f"  Subtasks: {subtask_count.scalar()}")
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
            raise


async def main():
    """Main function to initialize PostgreSQL database."""
    print("=" * 60)
    print("PostgreSQL Database Initialization")
    print("=" * 60)

    # Check connection
    if not await check_database_connection():
        print("\n[ABORT] Cannot proceed without database connection")
        sys.exit(1)

    try:
        # Create tables
        print("\n[STEP 1] Creating database tables...")
        await create_tables()

        # Insert initial data
        print("\n[STEP 2] Inserting initial data...")
        await insert_initial_data()

        # Verify setup
        print("\n[STEP 3] Verifying database setup...")
        await verify_setup()

        print("\n" + "=" * 60)
        print("[SUCCESS] PostgreSQL database initialization completed!")
        print("=" * 60)
        print("\nYou can now start the API server with:")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nTest users:")
        print("  - Admin: admin@test.com (token: token_1_admin_full_access_test_2024)")
        print("  - Manager: manager@test.com")
        print("  - Editor: editor@test.com")
        print("  - Viewer: viewer@test.com")
        print("\nAPI documentation: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n[FATAL] Database initialization failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())