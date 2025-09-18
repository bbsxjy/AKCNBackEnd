"""
Test script to verify Excel import functionality works without greenlet errors
"""

import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from openpyxl import Workbook

from app.models import User
from app.services.excel_service import ExcelService
from app.core.config import settings


async def test_subtask_import():
    """Test subtask import with multiple rows"""

    # Create database session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get or create a test user
        user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="admin"
        )

        # Create test Excel file with subtasks
        wb = Workbook()
        ws = wb.active
        ws.title = "SubTasks"

        # Headers
        headers = [
            'l2_id', 'sub_target', 'version_name', 'task_status',
            'progress_percentage', 'is_blocked', 'block_reason',
            'planned_requirement_date', 'planned_release_date',
            'planned_tech_online_date', 'planned_biz_online_date',
            'notes'
        ]

        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)

        # Add test data - 20 rows to test the issue
        test_data = []
        for i in range(1, 21):
            row_data = [
                f'L2_TEST_{i:03d}',  # l2_id
                'AK',  # sub_target
                f'v1.{i}',  # version_name
                '研发进行中',  # task_status
                50 + i,  # progress_percentage
                False,  # is_blocked
                '',  # block_reason
                '2024-01-15',  # planned_requirement_date
                '2024-02-15',  # planned_release_date
                '2024-02-28',  # planned_tech_online_date
                '2024-03-15',  # planned_biz_online_date
                f'Test subtask {i}'  # notes
            ]
            test_data.append(row_data)

            for col, value in enumerate(row_data, 1):
                ws.cell(row=i+1, column=col, value=value)

        # Save to bytes
        from io import BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        file_content = excel_buffer.getvalue()

        print(f"Created test Excel file with {len(test_data)} rows of subtask data")

        # Test import
        excel_service = ExcelService()

        print("\n=== Starting Excel Import Test ===")
        print(f"Importing {len(test_data)} subtasks...")

        try:
            result = await excel_service.import_subtasks_from_excel(
                db=db,
                file_content=file_content,
                user=user,
                validate_only=False
            )

            print("\n=== Import Results ===")
            print(f"Success: {result['success']}")
            print(f"Total rows: {result['total_rows']}")
            print(f"Imported: {result.get('processed_rows', 0)}")
            print(f"Updated: {result.get('updated_rows', 0)}")
            print(f"Skipped: {result.get('skipped_rows', 0)}")

            if result.get('errors'):
                print(f"\nErrors found: {len(result['errors'])}")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"  - Row {error.get('row')}: {error.get('message')}")

            # Check if the greenlet error occurred
            if result['success'] and result.get('processed_rows', 0) > 1:
                print("\n[SUCCESS] Import completed without greenlet errors!")
                print(f"   Successfully processed {result.get('processed_rows', 0)} rows")
            elif not result['success']:
                print("\n[FAILED] Import failed")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
            else:
                print("\n[WARNING] Only 1 row processed, possible greenlet issue")

        except Exception as e:
            print(f"\n[ERROR] during import: {e}")
            import traceback
            traceback.print_exc()

        await engine.dispose()


if __name__ == "__main__":
    print("Testing Excel import functionality...")
    asyncio.run(test_subtask_import())