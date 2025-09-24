"""
Test script for Excel import functionality
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

async def test_excel_import():
    """Test Excel import with sample data"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    
    # Login first to get token
    async with aiohttp.ClientSession() as session:
        # Login
        login_data = {
            "username": "admin@test.com",
            "password": "test123"
        }
        
        async with session.post(f"{base_url}/api/v1/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {await resp.text()}")
                return
            
            auth_response = await resp.json()
            token = auth_response.get("access_token")
            
            if not token:
                print("No token received")
                return
                
            print(f"[INFO] Successfully logged in")
            
        # Set authorization header
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Find an Excel file to test
        excel_files = []
        for ext in ['*.xlsx', '*.xls']:
            excel_files.extend(Path('.').glob(ext))
        
        if not excel_files:
            print("[WARNING] No Excel files found in current directory")
            print("[INFO] Creating a simple test Excel file...")
            
            import openpyxl
            from datetime import date
            
            # Create test workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "总追踪表"
            
            # Add headers
            headers_row = [
                "L2ID", "L2应用", "档位", "所属L1", "所属项目",
                "监管验收年份", "改造目标", "是否已完成AK", "是否已完成云原生",
                "当前改造阶段", "改造状态", "开发模式", "运维模式",
                "开发负责人", "开发团队", "运维负责人", "运维团队",
                "所属指标", "验收状态", "备注"
            ]
            ws.append(headers_row)
            
            # Add sample data
            test_data = [
                "TEST001", "测试应用1", "第一级", "测试系统", "2024年测试项目",
                2024, "AK", "否", "否",
                "开发中", "研发进行中", "敏捷", "DevOps",
                "张三", "测试团队A", "李四", "运维团队A",
                "KPI001", "待验收", "测试数据"
            ]
            ws.append(test_data)
            
            test_file = "test_import.xlsx"
            wb.save(test_file)
            print(f"[INFO] Created test file: {test_file}")
            excel_files = [Path(test_file)]
        
        # Test with the first Excel file found
        test_file = excel_files[0]
        print(f"[INFO] Testing with file: {test_file}")
        
        # Read file content
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        # Prepare multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field('file',
                           file_content,
                           filename=test_file.name,
                           content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Test import
        print(f"[INFO] Sending import request...")
        
        try:
            async with session.post(
                f"{base_url}/api/v1/excel/import/applications",
                data=form_data,
                headers=headers
            ) as resp:
                print(f"[INFO] Response status: {resp.status}")
                
                if resp.status == 200:
                    result = await resp.json()
                    print(f"[SUCCESS] Import completed successfully!")
                    print(f"[INFO] Results:")
                    print(f"  - Total rows: {result.get('total_rows', 0)}")
                    print(f"  - Processed: {result.get('processed_rows', 0)}")
                    print(f"  - Updated: {result.get('updated_rows', 0)}")
                    print(f"  - Skipped: {result.get('skipped_rows', 0)}")
                    
                    if result.get('errors'):
                        print(f"[WARNING] Errors encountered:")
                        for error in result['errors'][:5]:  # Show first 5 errors
                            print(f"  - {error}")
                else:
                    error_text = await resp.text()
                    print(f"[ERROR] Import failed with status {resp.status}")
                    print(f"[ERROR] Response: {error_text}")
                    
                    # Try to parse as JSON for better error display
                    try:
                        error_json = json.loads(error_text)
                        if 'detail' in error_json:
                            print(f"[ERROR] Detail: {error_json['detail']}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("[INFO] Starting Excel import test...")
    asyncio.run(test_excel_import())
    print("[INFO] Test completed")