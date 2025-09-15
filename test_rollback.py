"""
Test script for audit log rollback functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


async def test_rollback():
    """Test the audit log rollback functionality."""

    async with aiohttp.ClientSession() as session:

        # Step 1: Login to get auth token
        print("Step 1: Authenticating...")
        login_data = {
            "username": "admin",
            "password": "admin123"  # Replace with actual credentials
        }

        # For this test, we'll assume token is already available
        # In production, you would get this from SSO
        headers = {
            "Authorization": "Bearer YOUR_TOKEN_HERE",  # Replace with actual token
            "Content-Type": "application/json"
        }

        # Step 2: Create a test application record
        print("\nStep 2: Creating test application...")
        app_data = {
            "application_name": "Test App for Rollback",
            "l2_id": "TEST_ROLLBACK_001",
            "manager": "Test Manager",
            "department": "Test Department",
            "status": "待启动",
            "total_progress": 0
        }

        try:
            async with session.post(
                f"{BASE_URL}/applications",
                headers=headers,
                json=app_data
            ) as response:
                if response.status == 201:
                    created_app = await response.json()
                    app_id = created_app["id"]
                    print(f"Created application with ID: {app_id}")
                else:
                    print(f"Failed to create application: {response.status}")
                    return
        except Exception as e:
            print(f"Error creating application: {e}")
            return

        # Step 3: Update the application
        print("\nStep 3: Updating application...")
        update_data = {
            "application_name": "Updated Test App",
            "status": "研发进行中",
            "total_progress": 50
        }

        try:
            async with session.put(
                f"{BASE_URL}/applications/{app_id}",
                headers=headers,
                json=update_data
            ) as response:
                if response.status == 200:
                    print("Application updated successfully")
                else:
                    print(f"Failed to update application: {response.status}")
        except Exception as e:
            print(f"Error updating application: {e}")

        # Step 4: Get audit logs for this record
        print("\nStep 4: Getting audit logs...")
        try:
            async with session.get(
                f"{BASE_URL}/audit/record/applications/{app_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    audit_history = await response.json()
                    print(f"Found {audit_history['total_operations']} audit logs")

                    # Find the UPDATE operation
                    update_log_id = None
                    for log in audit_history["history"]:
                        if log["operation"] == "UPDATE":
                            update_log_id = log["id"]
                            print(f"Found UPDATE audit log with ID: {update_log_id}")
                            print(f"Old values: {json.dumps(log['old_values'], indent=2)}")
                            print(f"New values: {json.dumps(log['new_values'], indent=2)}")
                            break
                else:
                    print(f"Failed to get audit logs: {response.status}")
                    return
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return

        # Step 5: Perform rollback
        if update_log_id:
            print(f"\nStep 5: Rolling back audit log {update_log_id}...")
            rollback_data = {
                "confirm": True,
                "reason": "Testing rollback functionality"
            }

            try:
                async with session.post(
                    f"{BASE_URL}/audit/{update_log_id}/rollback",
                    headers=headers,
                    json=rollback_data
                ) as response:
                    if response.status == 200:
                        rollback_result = await response.json()
                        print("Rollback successful!")
                        print(f"Status: {rollback_result['status']}")
                        print(f"Rollback audit ID: {rollback_result['rollback_audit_id']}")
                        print(f"Message: {rollback_result['message']}")
                        print(f"Restored values: {json.dumps(rollback_result['affected_record']['restored_values'], indent=2)}")
                    else:
                        error_detail = await response.text()
                        print(f"Failed to rollback: {response.status}")
                        print(f"Error: {error_detail}")
            except Exception as e:
                print(f"Error performing rollback: {e}")

        # Step 6: Verify rollback by checking the application
        print("\nStep 6: Verifying rollback...")
        try:
            async with session.get(
                f"{BASE_URL}/applications/{app_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    app_after_rollback = await response.json()
                    print("Application after rollback:")
                    print(f"  Name: {app_after_rollback['application_name']}")
                    print(f"  Status: {app_after_rollback['status']}")
                    print(f"  Progress: {app_after_rollback['total_progress']}")

                    # Verify the values were restored
                    if app_after_rollback["application_name"] == "Test App for Rollback":
                        print("\n✅ Rollback verified successfully! Original values restored.")
                    else:
                        print("\n❌ Rollback verification failed! Values not restored correctly.")
                else:
                    print(f"Failed to get application: {response.status}")
        except Exception as e:
            print(f"Error verifying rollback: {e}")

        # Step 7: Clean up - delete the test application
        print("\nStep 7: Cleaning up test data...")
        try:
            async with session.delete(
                f"{BASE_URL}/applications/{app_id}",
                headers=headers
            ) as response:
                if response.status in [200, 204]:
                    print("Test application deleted successfully")
                else:
                    print(f"Failed to delete test application: {response.status}")
        except Exception as e:
            print(f"Error deleting test application: {e}")


async def test_rollback_edge_cases():
    """Test edge cases for rollback functionality."""

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": "Bearer YOUR_TOKEN_HERE",  # Replace with actual token
            "Content-Type": "application/json"
        }

        # Test 1: Try to rollback non-existent audit log
        print("\nTest 1: Rollback non-existent audit log...")
        rollback_data = {
            "confirm": True,
            "reason": "Testing non-existent rollback"
        }

        try:
            async with session.post(
                f"{BASE_URL}/audit/99999999/rollback",
                headers=headers,
                json=rollback_data
            ) as response:
                if response.status == 404:
                    print("✅ Correctly returned 404 for non-existent audit log")
                else:
                    print(f"❌ Unexpected status: {response.status}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: Try to rollback without confirmation
        print("\nTest 2: Rollback without confirmation...")
        rollback_data = {
            "confirm": False,
            "reason": "Testing without confirmation"
        }

        try:
            async with session.post(
                f"{BASE_URL}/audit/1/rollback",
                headers=headers,
                json=rollback_data
            ) as response:
                if response.status == 400:
                    print("✅ Correctly rejected rollback without confirmation")
                else:
                    print(f"❌ Unexpected status: {response.status}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("=== Audit Log Rollback Test Suite ===")
    print(f"Started at: {datetime.now()}")

    # Run main test
    asyncio.run(test_rollback())

    # Run edge case tests
    asyncio.run(test_rollback_edge_cases())

    print(f"\nCompleted at: {datetime.now()}")
    print("=== Test Suite Complete ===")