"""
Complete PostgreSQL Database Setup Script
==========================================
Creates database, tables, and comprehensive test data for AKCN Project Management System

Prerequisites:
1. PostgreSQL 14+ installed and running
2. Python 3.8+ with required packages (pip install -r requirements.txt)

Usage:
  python setup_postgresql.py [--reset] [--no-data]

Options:
  --reset    Drop and recreate all tables (default: prompt if tables exist)
  --no-data  Create schema only, skip test data insertion
"""

import psycopg2
from psycopg2 import sql
import asyncio
import sys
import os
import argparse
from datetime import datetime, timedelta, date, timezone
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_database_config():
    """Get database configuration from environment variables or defaults."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "akcn_user"),
        "password": os.getenv("DB_PASSWORD", "akcn_password"),
        "database": os.getenv("DB_NAME", "akcn_dev_db")
    }


def setup_database_sync(reset=False):
    """Setup database using psycopg2 (sync)."""

    print("=" * 80)
    print("AKCN PostgreSQL Database Setup")
    print("=" * 80)

    # Connection parameters
    conn_params = get_database_config()

    print("\nDatabase Configuration:")
    print(f"  Host: {conn_params['host']}:{conn_params['port']}")
    print(f"  Database: {conn_params['database']}")
    print(f"  User: {conn_params['user']}")

    try:
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        print("[✓] Connected to database")

        # Check PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"[ℹ] PostgreSQL version: {version.split(',')[0]}")

        # Check if tables exist
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name NOT LIKE 'alembic%'
        """)
        table_count = cursor.fetchone()[0]

        if table_count > 0:
            print(f"\n[⚠] Found {table_count} existing tables")
            if not reset:
                response = input("Drop and recreate all tables? (yes/no): ")
                if response.lower() != 'yes':
                    print("Setup cancelled.")
                    return False
            else:
                print("[ℹ] Reset mode: Will drop and recreate all tables")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"\n[✗] Cannot connect to database: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure PostgreSQL service is running:")
        print("   Windows: Check Services (services.msc)")
        print("   Linux: sudo systemctl status postgresql")
        print("\n2. Create database and user (run as postgres user):")
        print(f"""
   psql -U postgres
   CREATE USER {conn_params['user']} WITH PASSWORD '{conn_params['password']}';
   CREATE DATABASE {conn_params['database']} WITH OWNER = {conn_params['user']};
   GRANT ALL PRIVILEGES ON DATABASE {conn_params['database']} TO {conn_params['user']};
   \\q
""")
        print("\n3. Update .env file with correct credentials")
        return False
    except Exception as e:
        print(f"[✗] Unexpected error: {e}")
        return False


async def create_tables_and_data(skip_data=False):
    """Create tables and insert comprehensive test data."""

    from sqlalchemy import text
    from app.db.session import engine, AsyncSessionLocal
    from app.core.database import Base

    # Import all models to ensure they are registered with Base
    from app.models.user import User, UserRole
    from app.models.application import Application, ApplicationStatus, TransformationTarget
    from app.models.subtask import SubTask, SubTaskStatus
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification, NotificationType

    print("\n" + "=" * 80)
    print("Database Schema Creation")
    print("=" * 80)

    try:
        # Create all tables
        async with engine.begin() as conn:
            # Drop all tables first
            await conn.run_sync(Base.metadata.drop_all)
            print("[✓] Dropped existing tables")

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("[✓] Created all tables")

            # List created tables
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"\n[ℹ] Created {len(tables)} tables:")
            for table in tables:
                print(f"    • {table}")

    except Exception as e:
        print(f"[✗] Failed to create tables: {e}")
        await engine.dispose()
        return False

    if skip_data:
        print("\n[ℹ] Skipping test data insertion (--no-data flag)")
        await engine.dispose()
        return True

    print("\n" + "=" * 80)
    print("Test Data Generation")
    print("=" * 80)

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select

            # Check if data already exists
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("[ℹ] Data already exists, skipping insertion")
                await engine.dispose()
                return True

            # Create comprehensive test data
            print("\n[1/6] Creating users...")
            users = []

            # Standard test users
            admin_user = User(
                sso_user_id="SSO001",
                username="admin",
                email="admin@test.com",
                full_name="System Administrator",
                department="IT Platform",
                role=UserRole.ADMIN,
                is_active=True
            )
            users.append(admin_user)

            manager_user = User(
                sso_user_id="SSO002",
                username="manager",
                email="manager@test.com",
                full_name="Project Manager",
                department="Development",
                role=UserRole.MANAGER,
                is_active=True
            )
            users.append(manager_user)

            editor_user = User(
                sso_user_id="SSO003",
                username="editor",
                email="editor@test.com",
                full_name="Content Editor",
                department="Operations",
                role=UserRole.EDITOR,
                is_active=True
            )
            users.append(editor_user)

            viewer_user = User(
                sso_user_id="SSO004",
                username="viewer",
                email="viewer@test.com",
                full_name="Read Only User",
                department="Business",
                role=UserRole.VIEWER,
                is_active=True
            )
            users.append(viewer_user)

            # Additional test users
            test_users = [
                ("Zhang Wei", "zhangwei", "Platform Team"),
                ("Li Ming", "liming", "Development Team"),
                ("Wang Fang", "wangfang", "Finance Tech"),
                ("Chen Jun", "chenjun", "HR Technology"),
                ("Liu Yang", "liuyang", "Data Analytics"),
                ("Zhou Qiang", "zhouqiang", "Security Team"),
                ("Wu Dan", "wudan", "QA Team"),
                ("Huang Lei", "huanglei", "Infrastructure")
            ]

            for i, (name, username, dept) in enumerate(test_users, 5):
                user = User(
                    sso_user_id=f"SSO{i:03d}",
                    username=username,
                    email=f"{username}@test.com",
                    full_name=name,
                    department=dept,
                    role=random.choice([UserRole.EDITOR, UserRole.VIEWER]),
                    is_active=True
                )
                users.append(user)

            session.add_all(users)
            await session.flush()
            print(f"    ✓ Created {len(users)} users")

            # Create applications with diverse statuses
            print("\n[2/6] Creating applications...")
            applications = []

            # Application templates for realistic test data
            app_templates = [
                # Completed applications
                ("APP001", "HR Management Portal", "HR Technology", ApplicationStatus.COMPLETED, TransformationTarget.AK, 2024),
                ("APP002", "Employee Self-Service", "HR Technology", ApplicationStatus.COMPLETED, TransformationTarget.AK, 2024),

                # In business online
                ("APP003", "Financial Reporting System", "Finance Tech", ApplicationStatus.BIZ_ONLINE, TransformationTarget.AK, 2025),
                ("APP004", "Budget Management", "Finance Tech", ApplicationStatus.BIZ_ONLINE, TransformationTarget.CLOUD_NATIVE, 2025),

                # In development
                ("APP005", "Customer Management System", "Platform Team", ApplicationStatus.DEV_IN_PROGRESS, TransformationTarget.AK, 2025),
                ("APP006", "Order Processing Platform", "Development Team", ApplicationStatus.DEV_IN_PROGRESS, TransformationTarget.CLOUD_NATIVE, 2025),
                ("APP007", "Inventory Management", "Operations", ApplicationStatus.DEV_IN_PROGRESS, TransformationTarget.AK, 2025),

                # Not started
                ("APP008", "Marketing Automation", "Marketing Tech", ApplicationStatus.NOT_STARTED, TransformationTarget.CLOUD_NATIVE, 2025),
                ("APP009", "Analytics Dashboard", "Data Analytics", ApplicationStatus.NOT_STARTED, TransformationTarget.AK, 2025),
                ("APP010", "Security Monitoring", "Security Team", ApplicationStatus.NOT_STARTED, TransformationTarget.CLOUD_NATIVE, 2025),

                # Additional applications for testing
                ("APP011", "Payment Gateway", "Platform Team", ApplicationStatus.DEV_IN_PROGRESS, TransformationTarget.AK, 2025),
                ("APP012", "Notification Service", "Platform Team", ApplicationStatus.BIZ_ONLINE, TransformationTarget.CLOUD_NATIVE, 2025),
                ("APP013", "Document Management", "Operations", ApplicationStatus.NOT_STARTED, TransformationTarget.AK, 2025),
                ("APP014", "Workflow Engine", "Development Team", ApplicationStatus.DEV_IN_PROGRESS, TransformationTarget.CLOUD_NATIVE, 2025),
                ("APP015", "API Gateway", "Platform Team", ApplicationStatus.COMPLETED, TransformationTarget.CLOUD_NATIVE, 2024),
            ]

            base_date = date.today()
            for l2_id, name, team, status, target, year in app_templates:
                # Calculate dates based on status
                if status == ApplicationStatus.COMPLETED:
                    planned_req = base_date - timedelta(days=180)
                    planned_rel = planned_req + timedelta(days=45)
                    planned_tech = planned_rel + timedelta(days=30)
                    planned_biz = planned_tech + timedelta(days=30)
                    actual_req = planned_req + timedelta(days=random.randint(-5, 5))
                    actual_rel = planned_rel + timedelta(days=random.randint(-5, 5))
                    actual_tech = planned_tech + timedelta(days=random.randint(-5, 5))
                    actual_biz = planned_biz + timedelta(days=random.randint(-5, 5))
                    is_delayed = False
                    delay_days = 0
                elif status == ApplicationStatus.BIZ_ONLINE:
                    planned_req = base_date - timedelta(days=120)
                    planned_rel = planned_req + timedelta(days=45)
                    planned_tech = planned_rel + timedelta(days=30)
                    planned_biz = base_date + timedelta(days=15)
                    actual_req = planned_req + timedelta(days=random.randint(-3, 7))
                    actual_rel = planned_rel + timedelta(days=random.randint(-3, 10))
                    actual_tech = planned_tech + timedelta(days=random.randint(0, 15))
                    actual_biz = None
                    is_delayed = actual_tech > planned_tech
                    delay_days = (actual_tech - planned_tech).days if is_delayed else 0
                elif status == ApplicationStatus.DEV_IN_PROGRESS:
                    planned_req = base_date - timedelta(days=60)
                    planned_rel = base_date + timedelta(days=30)
                    planned_tech = planned_rel + timedelta(days=30)
                    planned_biz = planned_tech + timedelta(days=30)
                    actual_req = planned_req + timedelta(days=random.randint(0, 10))
                    actual_rel = None
                    actual_tech = None
                    actual_biz = None
                    is_delayed = base_date > planned_rel
                    delay_days = (base_date - planned_rel).days if is_delayed else 0
                else:  # NOT_STARTED
                    planned_req = base_date + timedelta(days=30)
                    planned_rel = planned_req + timedelta(days=60)
                    planned_tech = planned_rel + timedelta(days=30)
                    planned_biz = planned_tech + timedelta(days=30)
                    actual_req = None
                    actual_rel = None
                    actual_tech = None
                    actual_biz = None
                    is_delayed = False
                    delay_days = 0

                # Find responsible person from users
                responsible = random.choice([u for u in users if u.department == team or u.role == UserRole.MANAGER])

                app = Application(
                    l2_id=l2_id,
                    app_name=name,
                    supervision_year=year,
                    transformation_target=target,
                    is_ak_completed=(target == TransformationTarget.AK and status == ApplicationStatus.COMPLETED),
                    is_cloud_native_completed=(target == TransformationTarget.CLOUD_NATIVE and status == ApplicationStatus.COMPLETED),
                    current_stage=status.value,
                    overall_status=status,
                    responsible_team=team,
                    responsible_person=responsible.full_name,
                    progress_percentage=0,  # Will be calculated from subtasks
                    planned_requirement_date=planned_req,
                    planned_release_date=planned_rel,
                    planned_tech_online_date=planned_tech,
                    planned_biz_online_date=planned_biz,
                    actual_requirement_date=actual_req,
                    actual_release_date=actual_rel,
                    actual_tech_online_date=actual_tech,
                    actual_biz_online_date=actual_biz,
                    is_delayed=is_delayed,
                    delay_days=delay_days,
                    notes=f"Test application for {target.value} transformation",
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                )
                applications.append(app)

            session.add_all(applications)
            await session.flush()
            print(f"    ✓ Created {len(applications)} applications")

            # Create subtasks
            print("\n[3/6] Creating subtasks...")
            subtasks = []

            # Subtask templates
            subtask_templates = [
                "Authentication Module",
                "Data Management Module",
                "API Gateway Integration",
                "Frontend UI Components",
                "Database Migration",
                "Caching Layer",
                "Message Queue Integration",
                "Monitoring & Logging",
                "Security Hardening",
                "Performance Optimization",
                "Documentation",
                "Testing Suite"
            ]

            for app in applications:
                # Number of subtasks based on application status
                if app.overall_status == ApplicationStatus.COMPLETED:
                    num_subtasks = random.randint(8, 12)
                elif app.overall_status == ApplicationStatus.BIZ_ONLINE:
                    num_subtasks = random.randint(6, 10)
                elif app.overall_status == ApplicationStatus.DEV_IN_PROGRESS:
                    num_subtasks = random.randint(4, 8)
                else:
                    num_subtasks = random.randint(2, 5)

                selected_modules = random.sample(subtask_templates, min(num_subtasks, len(subtask_templates)))

                for i, module in enumerate(selected_modules):
                    # Determine subtask status based on application status
                    if app.overall_status == ApplicationStatus.COMPLETED:
                        task_status = SubTaskStatus.COMPLETED
                    elif app.overall_status == ApplicationStatus.BIZ_ONLINE:
                        if i < len(selected_modules) * 0.7:
                            task_status = SubTaskStatus.COMPLETED
                        else:
                            task_status = random.choice([SubTaskStatus.BIZ_ONLINE, SubTaskStatus.TECH_ONLINE])
                    elif app.overall_status == ApplicationStatus.DEV_IN_PROGRESS:
                        if i < len(selected_modules) * 0.3:
                            task_status = SubTaskStatus.COMPLETED
                        elif i < len(selected_modules) * 0.6:
                            task_status = random.choice([SubTaskStatus.DEV_IN_PROGRESS, SubTaskStatus.TESTING])
                        else:
                            task_status = random.choice([SubTaskStatus.NOT_STARTED, SubTaskStatus.REQUIREMENT_ANALYSIS])
                    else:
                        task_status = SubTaskStatus.NOT_STARTED

                    # Calculate dates based on task status
                    if task_status == SubTaskStatus.COMPLETED:
                        actual_dates = {
                            'actual_requirement_date': app.planned_requirement_date + timedelta(days=random.randint(0, 10)),
                            'actual_release_date': app.planned_release_date + timedelta(days=random.randint(-5, 10)),
                            'actual_tech_online_date': app.planned_tech_online_date + timedelta(days=random.randint(-5, 10)) if app.planned_tech_online_date else None,
                            'actual_biz_online_date': app.planned_biz_online_date + timedelta(days=random.randint(-5, 10)) if app.planned_biz_online_date else None
                        }
                    elif task_status in [SubTaskStatus.BIZ_ONLINE, SubTaskStatus.TECH_ONLINE]:
                        actual_dates = {
                            'actual_requirement_date': app.planned_requirement_date + timedelta(days=random.randint(0, 10)),
                            'actual_release_date': app.planned_release_date + timedelta(days=random.randint(0, 10)),
                            'actual_tech_online_date': app.planned_tech_online_date + timedelta(days=random.randint(0, 10)) if app.planned_tech_online_date else None,
                            'actual_biz_online_date': None
                        }
                    elif task_status in [SubTaskStatus.DEV_IN_PROGRESS, SubTaskStatus.TESTING]:
                        actual_dates = {
                            'actual_requirement_date': app.planned_requirement_date + timedelta(days=random.randint(0, 10)),
                            'actual_release_date': None,
                            'actual_tech_online_date': None,
                            'actual_biz_online_date': None
                        }
                    else:
                        actual_dates = {
                            'actual_requirement_date': None,
                            'actual_release_date': None,
                            'actual_tech_online_date': None,
                            'actual_biz_online_date': None
                        }

                    subtask = SubTask(
                        application_id=app.id,
                        module_name=module,
                        sub_target=app.transformation_target.value,
                        version_name=f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                        task_status=task_status,
                        progress_percentage=0,  # Will be calculated
                        is_blocked=random.random() < 0.1,  # 10% chance of being blocked
                        planned_requirement_date=app.planned_requirement_date,
                        planned_release_date=app.planned_release_date,
                        planned_tech_online_date=app.planned_tech_online_date,
                        planned_biz_online_date=app.planned_biz_online_date,
                        **actual_dates,
                        requirements=f"Implement {module.lower()} for {app.app_name}",
                        technical_notes=f"Using microservices architecture with {app.transformation_target.value}",
                        assigned_to=random.choice(users).full_name,
                        reviewer=random.choice([u for u in users if u.role in [UserRole.ADMIN, UserRole.MANAGER]]).full_name,
                        priority=random.randint(1, 5),
                        estimated_hours=random.randint(40, 200),
                        actual_hours=random.randint(30, 220) if task_status != SubTaskStatus.NOT_STARTED else None,
                        created_by=admin_user.id,
                        updated_by=admin_user.id
                    )
                    subtasks.append(subtask)

            session.add_all(subtasks)
            await session.flush()
            print(f"    ✓ Created {len(subtasks)} subtasks")

            # Create notifications
            print("\n[4/6] Creating notifications...")
            notifications = []

            # System notifications
            for user in users[:4]:  # Create for main test users
                notifications.append(Notification(
                    user_id=user.id,
                    title="Welcome to AKCN System",
                    message="Your account has been successfully created. Please review your assigned tasks.",
                    type=NotificationType.INFO,
                    is_read=False
                ))

            # Delay notifications
            for app in applications:
                if app.is_delayed:
                    notifications.append(Notification(
                        user_id=admin_user.id,
                        title=f"Application Delayed: {app.app_name}",
                        message=f"Application {app.l2_id} is delayed by {app.delay_days} days. Please review the timeline.",
                        type=NotificationType.WARNING,
                        is_read=False
                    ))

            # Task assignment notifications
            for subtask in random.sample(subtasks, min(10, len(subtasks))):
                assigned_user = next((u for u in users if u.full_name == subtask.assigned_to), None)
                if assigned_user:
                    notifications.append(Notification(
                        user_id=assigned_user.id,
                        title=f"New Task Assigned: {subtask.module_name}",
                        message=f"You have been assigned to work on {subtask.module_name} for application {subtask.application_id}",
                        type=NotificationType.INFO,
                        is_read=random.choice([True, False])
                    ))

            session.add_all(notifications)
            await session.flush()
            print(f"    ✓ Created {len(notifications)} notifications")

            # Create audit logs
            print("\n[5/6] Creating audit logs...")
            audit_logs = []

            # Create audit logs for applications
            for app in applications[:10]:  # Sample audit logs
                audit_logs.append(AuditLog(
                    table_name="applications",
                    record_id=app.id,
                    operation="INSERT",
                    old_values=None,
                    new_values={
                        "l2_id": app.l2_id,
                        "app_name": app.app_name,
                        "status": app.overall_status.value
                    },
                    user_id=admin_user.id,
                    user_ip="127.0.0.1",
                    user_agent="PostgreSQL Setup Script"
                ))

                # Add some UPDATE logs
                if app.overall_status != ApplicationStatus.NOT_STARTED:
                    audit_logs.append(AuditLog(
                        table_name="applications",
                        record_id=app.id,
                        operation="UPDATE",
                        old_values={"status": "NOT_STARTED"},
                        new_values={"status": app.overall_status.value},
                        user_id=manager_user.id,
                        user_ip="192.168.1.100",
                        user_agent="Mozilla/5.0"
                    ))

            # Create audit logs for subtasks
            for subtask in subtasks[:20]:  # Sample audit logs
                audit_logs.append(AuditLog(
                    table_name="sub_tasks",
                    record_id=subtask.id,
                    operation="INSERT",
                    old_values=None,
                    new_values={
                        "module_name": subtask.module_name,
                        "status": subtask.task_status.value
                    },
                    user_id=editor_user.id,
                    user_ip="10.0.0.50",
                    user_agent="FastAPI Client"
                ))

            session.add_all(audit_logs)
            await session.flush()
            print(f"    ✓ Created {len(audit_logs)} audit logs")

            # Calculate progress for all applications
            print("\n[6/6] Calculating application progress...")
            from app.services.calculation_service import CalculationService
            calc_service = CalculationService()

            for app in applications:
                await calc_service.calculate_application_progress(session, app.id)

            print(f"    ✓ Calculated progress for {len(applications)} applications")

            # Commit all changes
            await session.commit()
            print("\n[✓] All data committed successfully")

        except Exception as e:
            await session.rollback()
            print(f"\n[✗] Failed to insert data: {e}")
            import traceback
            traceback.print_exc()
            await engine.dispose()
            return False

    # Verify the setup
    print("\n" + "=" * 80)
    print("Database Verification")
    print("=" * 80)

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select, func

            # Count records in each table
            user_count = await session.scalar(select(func.count(User.id)))
            app_count = await session.scalar(select(func.count(Application.id)))
            subtask_count = await session.scalar(select(func.count(SubTask.id)))
            audit_count = await session.scalar(select(func.count(AuditLog.id)))
            notification_count = await session.scalar(select(func.count(Notification.id)))

            print("\nDatabase Statistics:")
            print(f"  • Users:         {user_count:,}")
            print(f"  • Applications:  {app_count:,}")
            print(f"  • Subtasks:      {subtask_count:,}")
            print(f"  • Notifications: {notification_count:,}")
            print(f"  • Audit Logs:    {audit_count:,}")

            # Application status distribution
            print("\nApplication Status Distribution:")
            for status in ApplicationStatus:
                count = await session.scalar(
                    select(func.count(Application.id))
                    .where(Application.overall_status == status)
                )
                if count > 0:
                    print(f"  • {status.value:20} {count:3} applications")

            # Subtask status distribution
            print("\nSubtask Status Distribution:")
            for status in SubTaskStatus:
                count = await session.scalar(
                    select(func.count(SubTask.id))
                    .where(SubTask.task_status == status)
                )
                if count > 0:
                    print(f"  • {status.value:20} {count:3} subtasks")

            print("\n[✓] Database verification completed")

        except Exception as e:
            print(f"[✗] Verification failed: {e}")
            await engine.dispose()
            return False

    await engine.dispose()
    return True


async def main(args):
    """Main setup function."""

    print("\nAKCN Project Management System")
    print("PostgreSQL Database Setup Tool")
    print("-" * 80)

    # Check database connection
    if not setup_database_sync(reset=args.reset):
        return False

    # Create tables and insert data
    if not await create_tables_and_data(skip_data=args.no_data):
        return False

    print("\n" + "=" * 80)
    print("✨ Database Setup Completed Successfully!")
    print("=" * 80)

    config = get_database_config()
    print("\nConnection Details:")
    print(f"  Database: {config['database']}")
    print(f"  Host:     {config['host']}:{config['port']}")
    print(f"  User:     {config['user']}")

    print("\nNext Steps:")
    print("1. Start the API server:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n2. Access API documentation:")
    print("   http://localhost:8000/docs")

    if not args.no_data:
        print("\n3. Test user credentials:")
        print("   • Admin:   admin@test.com    (Full access)")
        print("   • Manager: manager@test.com  (Department management)")
        print("   • Editor:  editor@test.com   (Edit permissions)")
        print("   • Viewer:  viewer@test.com   (Read-only)")
        print("\n   Test token: token_1_admin_full_access_test_2024")

    print("\n4. Environment variables (.env file):")
    print(f"""   DATABASE_URL=postgresql+asyncpg://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}
   JWT_SECRET_KEY=your-secret-key-change-in-production
   JWT_ALGORITHM=HS256""")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup PostgreSQL database for AKCN system")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables without prompting")
    parser.add_argument("--no-data", action="store_true", help="Create schema only, skip test data")
    args = parser.parse_args()

    try:
        success = asyncio.run(main(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[!] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)