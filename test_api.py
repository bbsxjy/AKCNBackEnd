"""
Test script to verify all API endpoints are working correctly
"""

import asyncio
import aiohttp
import json


async def test_api():
    """Test all API endpoints."""
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer token_1_admin_full_access_test_2024",
        "Origin": "http://localhost:3000",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("Testing health endpoint...")
        async with session.get(f"{base_url}/health") as resp:
            print(f"  Status: {resp.status}")
            data = await resp.json()
            print(f"  Response: {data}")

        # Test CORS preflight
        print("\nTesting CORS preflight...")
        async with session.options(
            f"{base_url}/api/v1/applications/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization"
            }
        ) as resp:
            print(f"  Status: {resp.status}")
            print(f"  CORS Headers: {dict(resp.headers)}")

        # Test notifications endpoint
        print("\nTesting notifications endpoint...")
        async with session.get(
            f"{base_url}/api/v1/notifications/?unread_only=true&limit=10",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            data = await resp.json()
            print(f"  Response: {data}")

        # Test applications list endpoint
        print("\nTesting applications list endpoint...")
        async with session.get(
            f"{base_url}/api/v1/applications/?limit=10",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Total applications: {data.get('total', 0)}")
                print(f"  Page: {data.get('page', 1)}/{data.get('total_pages', 0)}")
                print(f"  Items returned: {len(data.get('items', []))}")
                if data.get('items'):
                    first_item = data['items'][0]
                    print(f"  First application: {first_item.get('app_name', 'N/A')} (ID: {first_item.get('l2_id', 'N/A')})")
            else:
                error = await resp.text()
                print(f"  Error: {error}")

        # Test subtasks list endpoint
        print("\nTesting subtasks list endpoint...")
        async with session.get(
            f"{base_url}/api/v1/subtasks/?limit=10",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"  Total subtasks: {data.get('total', 0)}")
                print(f"  Items returned: {len(data.get('items', []))}")
            else:
                error = await resp.text()
                print(f"  Error: {error}")

        # Test applications test endpoint
        print("\nTesting applications test endpoint...")
        async with session.get(
            f"{base_url}/api/v1/applications/test",
            headers=headers
        ) as resp:
            print(f"  Status: {resp.status}")
            data = await resp.json()
            print(f"  Response: {data}")

        print("\nAll tests completed!")


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the server is running on http://localhost:8000")
    print("-" * 50)
    asyncio.run(test_api())