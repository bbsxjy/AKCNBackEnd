"""
Initialize database with tables and sample data
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, AsyncSessionLocal, Base
from app.models.user import User, UserRole
from app.models.application import Application, ApplicationStatus
from app.models.subtask import SubTask, SubTaskStatus
import datetime


async def init_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models import user, application, subtask, audit_log

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("[OK] Database tables created")


async def create_sample_data():
    """Create sample data for testing."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            from sqlalchemy import select
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("[WARNING] Sample data already exists, skipping...")
                return

            # Create test users
            admin_user = User(
                sso_user_id="SSO001",
                username="admin",
                email="admin@test.com",
                full_name="Test Admin",
                department="Platform",
                role=UserRole.ADMIN,
                is_active=True
            )

            manager_user = User(
                sso_user_id="SSO002",
                username="manager",
                email="manager@test.com",
                full_name="Test Manager",
                department="Development",
                role=UserRole.MANAGER,
                is_active=True
            )

            editor_user = User(
                sso_user_id="SSO003",
                username="editor",
                email="editor@test.com",
                full_name="Test Editor",
                department="Operations",
                role=UserRole.EDITOR,
                is_active=True
            )

            session.add_all([admin_user, manager_user, editor_user])
            await session.flush()

            # Create sample applications
            app1 = Application(
                l2_application_id="APP001",
                application_name_cn="测试应用一",
                application_name_en="Test Application 1",
                business_domain="金融服务",
                owning_team="Platform Team",
                status=ApplicationStatus.IN_DEVELOPMENT,
                progress_percentage=45.0,
                planned_migration_date=datetime.date(2024, 6, 30),
                actual_migration_date=None,
                delay_days=0,
                created_by=admin_user.id,
                updated_by=admin_user.id
            )

            app2 = Application(
                l2_application_id="APP002",
                application_name_cn="测试应用二",
                application_name_en="Test Application 2",
                business_domain="客户管理",
                owning_team="Development Team",
                status=ApplicationStatus.NOT_STARTED,
                progress_percentage=0.0,
                planned_migration_date=datetime.date(2024, 9, 30),
                actual_migration_date=None,
                delay_days=0,
                created_by=manager_user.id,
                updated_by=manager_user.id
            )

            session.add_all([app1, app2])
            await session.flush()

            # Create sample subtasks for app1
            subtasks = [
                SubTask(
                    application_id=app1.id,
                    module_name="用户认证模块",
                    sub_target="AK",
                    version_name="v1.0.0",
                    task_status=SubTaskStatus.COMPLETED,
                    progress_percentage=100,
                    is_blocked=False,
                    planned_requirement_date=datetime.date(2024, 1, 1),
                    planned_release_date=datetime.date(2024, 2, 1),
                    planned_tech_online_date=datetime.date(2024, 2, 15),
                    planned_biz_online_date=datetime.date(2024, 3, 1),
                    actual_requirement_date=datetime.date(2024, 1, 5),
                    actual_release_date=datetime.date(2024, 2, 10),
                    actual_tech_online_date=datetime.date(2024, 2, 20),
                    actual_biz_online_date=datetime.date(2024, 3, 5),
                    requirements="完成用户认证模块的AK改造",
                    technical_notes="使用JWT token替代session",
                    assigned_to="张三",
                    reviewer="李四",
                    priority=3,
                    estimated_hours=120,
                    actual_hours=130,
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                ),
                SubTask(
                    application_id=app1.id,
                    module_name="订单管理模块",
                    sub_target="云原生",
                    version_name="v2.0.0",
                    task_status=SubTaskStatus.DEV_IN_PROGRESS,
                    progress_percentage=50,
                    is_blocked=False,
                    planned_requirement_date=datetime.date(2024, 2, 1),
                    planned_release_date=datetime.date(2024, 4, 30),
                    planned_tech_online_date=datetime.date(2024, 5, 15),
                    planned_biz_online_date=datetime.date(2024, 6, 1),
                    actual_requirement_date=datetime.date(2024, 2, 15),
                    requirements="订单管理模块云原生改造",
                    technical_notes="微服务架构，使用K8s部署",
                    assigned_to="王五",
                    reviewer="赵六",
                    priority=2,
                    estimated_hours=200,
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                ),
                SubTask(
                    application_id=app1.id,
                    module_name="支付集成模块",
                    sub_target="AK",
                    version_name="v1.5.0",
                    task_status=SubTaskStatus.NOT_STARTED,
                    progress_percentage=0,
                    is_blocked=False,
                    planned_requirement_date=datetime.date(2024, 5, 1),
                    planned_release_date=datetime.date(2024, 6, 1),
                    planned_tech_online_date=datetime.date(2024, 6, 15),
                    planned_biz_online_date=datetime.date(2024, 6, 30),
                    requirements="支付集成模块AK改造",
                    assigned_to="孙七",
                    priority=1,
                    estimated_hours=160,
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                ),
                SubTask(
                    application_id=app1.id,
                    module_name="报表分析模块",
                    sub_target="云原生",
                    version_name="v3.0.0",
                    task_status=SubTaskStatus.BLOCKED,
                    progress_percentage=30,
                    is_blocked=True,
                    block_reason="等待数据库迁移完成",
                    planned_requirement_date=datetime.date(2024, 3, 1),
                    planned_release_date=datetime.date(2024, 5, 30),
                    planned_tech_online_date=datetime.date(2024, 6, 15),
                    planned_biz_online_date=datetime.date(2024, 6, 30),
                    actual_requirement_date=datetime.date(2024, 3, 10),
                    requirements="报表分析模块云原生改造",
                    technical_notes="需要先完成数据库迁移",
                    assigned_to="周八",
                    priority=2,
                    estimated_hours=180,
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                )
            ]

            session.add_all(subtasks)

            await session.commit()
            print("[OK] Sample data created successfully")

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Error creating sample data: {e}")
            raise


async def main():
    """Main function to initialize database."""
    print("Initializing database...")

    try:
        await init_tables()
        await create_sample_data()
        print("\n[OK] Database initialization completed!")
        print("\nYou can now access the API with the following test users:")
        print("  - Admin: admin@test.com (token: token_1_admin_full_access_test_2024)")
        print("  - Manager: manager@test.com")
        print("  - Editor: editor@test.com")
    except Exception as e:
        print(f"\n[ERROR] Database initialization failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())