#!/usr/bin/env python3
"""
Debug script to test Excel import functionality with Chinese columns
"""

import asyncio
import sys
import os
from pathlib import Path

# Set UTF-8 for output
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app.services.excel_service import ExcelService
from app.models import User
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


async def test_import():
    """Test the import functionality with Chinese column names"""

    # Create database session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Read the test file
        test_file = 'test_chinese_columns.xlsx'
        if not Path(test_file).exists():
            print(f"Test file {test_file} not found!")
            return

        with open(test_file, 'rb') as f:
            file_content = f.read()

        print(f'File content size: {len(file_content)} bytes')

        # Create mock user
        user = User(id=1, username='test', email='test@test.com', role='admin', full_name='Test User')

        # Create service
        service = ExcelService()

        # Test import with validate_only=True
        print('\n=== Testing subtask import with validate_only=True ===')
        try:
            result = await service.import_subtasks_from_excel(
                db=db,
                file_content=file_content,
                user=user,
                validate_only=True
            )

            print(f'\nImport result:')
            for key, value in result.items():
                if key not in ('preview_data', 'errors'):
                    print(f'  {key}: {value}')

            # Check detailed breakdown
            if 'applications' in result:
                print(f'\nApplications breakdown:')
                for key, value in result['applications'].items():
                    print(f'  {key}: {value}')

            if 'subtasks' in result:
                print(f'\nSubtasks breakdown:')
                for key, value in result['subtasks'].items():
                    print(f'  {key}: {value}')

            # Show errors if any
            if result.get('errors'):
                print(f'\nErrors found ({len(result["errors"])}):')
                for err in result['errors'][:5]:
                    print(f'  - {err}')

            # Show preview data
            if result.get('preview_data'):
                print(f'\nPreview data ({len(result["preview_data"])} rows):')
                for i, row in enumerate(result['preview_data'][:3]):
                    print(f'  Row {i+1}: {list(row.keys())[:5]}...')

        except Exception as e:
            print(f'\nError during import: {e}')
            import traceback
            traceback.print_exc()

        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("Testing Excel import with Chinese column names...")
    asyncio.run(test_import())