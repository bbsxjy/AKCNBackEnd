"""
Unit tests for audit log rollback functionality
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from fastapi import status

from app.models.user import User, UserRole
from app.models.application import Application
from app.models.audit_log import AuditLog, AuditOperation
from app.services.audit_service import AuditService


@pytest.mark.asyncio
async def test_rollback_update_operation(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str
):
    """Test rollback of UPDATE operation."""

    # Create a test application
    app_data = {
        "application_name": "Test App",
        "l2_id": "TEST_001",
        "manager": "Test Manager",
        "department": "Test Dept",
        "status": "待启动",
        "total_progress": 0
    }

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create application
    response = await client.post(
        "/api/v1/applications",
        json=app_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    app_id = response.json()["id"]

    # Update application
    update_data = {
        "application_name": "Updated App",
        "status": "研发进行中",
        "total_progress": 50
    }

    response = await client.put(
        f"/api/v1/applications/{app_id}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Get audit logs
    response = await client.get(
        f"/api/v1/audit/record/applications/{app_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    audit_history = response.json()

    # Find UPDATE audit log
    update_log_id = None
    for log in audit_history["history"]:
        if log["operation"] == "UPDATE":
            update_log_id = log["id"]
            break

    assert update_log_id is not None

    # Perform rollback
    rollback_data = {
        "confirm": True,
        "reason": "Test rollback"
    }

    response = await client.post(
        f"/api/v1/audit/{update_log_id}/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    rollback_result = response.json()

    assert rollback_result["status"] == "success"
    assert rollback_result["rollback_audit_id"] > 0
    assert rollback_result["affected_record"]["operation"] == "UPDATE"

    # Verify application was rolled back
    response = await client.get(
        f"/api/v1/applications/{app_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    app_after = response.json()

    assert app_after["application_name"] == "Test App"
    assert app_after["status"] == "待启动"
    assert app_after["total_progress"] == 0


@pytest.mark.asyncio
async def test_rollback_insert_operation(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str
):
    """Test rollback of INSERT operation (delete the record)."""

    # Create a test application
    app_data = {
        "application_name": "Test Insert Rollback",
        "l2_id": "TEST_INSERT_001",
        "manager": "Test Manager",
        "department": "Test Dept",
        "status": "待启动",
        "total_progress": 0
    }

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create application
    response = await client.post(
        "/api/v1/applications",
        json=app_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    app_id = response.json()["id"]

    # Get audit logs
    response = await client.get(
        f"/api/v1/audit/record/applications/{app_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    audit_history = response.json()

    # Find INSERT audit log
    insert_log_id = None
    for log in audit_history["history"]:
        if log["operation"] == "INSERT":
            insert_log_id = log["id"]
            break

    assert insert_log_id is not None

    # Perform rollback (will delete the record)
    rollback_data = {
        "confirm": True,
        "reason": "Test rollback of INSERT"
    }

    response = await client.post(
        f"/api/v1/audit/{insert_log_id}/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    rollback_result = response.json()

    assert rollback_result["status"] == "success"
    assert rollback_result["affected_record"]["operation"] == "DELETE"

    # Verify application was deleted
    response = await client.get(
        f"/api/v1/applications/{app_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_rollback_delete_operation(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str
):
    """Test rollback of DELETE operation (restore the record)."""

    # Create a test application
    app_data = {
        "application_name": "Test Delete Rollback",
        "l2_id": "TEST_DELETE_001",
        "manager": "Test Manager",
        "department": "Test Dept",
        "status": "待启动",
        "total_progress": 0
    }

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create application
    response = await client.post(
        "/api/v1/applications",
        json=app_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    app_id = response.json()["id"]

    # Delete application
    response = await client.delete(
        f"/api/v1/applications/{app_id}",
        headers=headers
    )
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    # Get audit logs for deleted record
    response = await client.get(
        f"/api/v1/audit/record/applications/{app_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    audit_history = response.json()

    # Find DELETE audit log
    delete_log_id = None
    for log in audit_history["history"]:
        if log["operation"] == "DELETE":
            delete_log_id = log["id"]
            break

    assert delete_log_id is not None

    # Perform rollback (will restore the record)
    rollback_data = {
        "confirm": True,
        "reason": "Test rollback of DELETE"
    }

    response = await client.post(
        f"/api/v1/audit/{delete_log_id}/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    rollback_result = response.json()

    assert rollback_result["status"] == "success"
    assert rollback_result["affected_record"]["operation"] == "INSERT"

    # Verify application was restored
    response = await client.get(
        f"/api/v1/applications/{app_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    app_restored = response.json()

    assert app_restored["application_name"] == "Test Delete Rollback"
    assert app_restored["l2_id"] == "TEST_DELETE_001"


@pytest.mark.asyncio
async def test_rollback_without_confirmation(
    client: AsyncClient,
    admin_token: str
):
    """Test rollback without confirmation should fail."""

    headers = {"Authorization": f"Bearer {admin_token}"}

    rollback_data = {
        "confirm": False,
        "reason": "Test without confirmation"
    }

    response = await client.post(
        "/api/v1/audit/1/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "confirmation required" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rollback_nonexistent_audit_log(
    client: AsyncClient,
    admin_token: str
):
    """Test rollback of non-existent audit log should fail."""

    headers = {"Authorization": f"Bearer {admin_token}"}

    rollback_data = {
        "confirm": True,
        "reason": "Test non-existent"
    }

    response = await client.post(
        "/api/v1/audit/99999999/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_rollback_permission_check(
    client: AsyncClient,
    viewer_token: str
):
    """Test that only authorized users can perform rollback."""

    headers = {"Authorization": f"Bearer {viewer_token}"}

    rollback_data = {
        "confirm": True,
        "reason": "Test permission"
    }

    response = await client.post(
        "/api/v1/audit/1/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_rollback_creates_audit_log(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str
):
    """Test that rollback operation itself creates an audit log."""

    # Create and update an application
    app_data = {
        "application_name": "Test Audit Creation",
        "l2_id": "TEST_AUDIT_001",
        "manager": "Test Manager",
        "department": "Test Dept",
        "status": "待启动",
        "total_progress": 0
    }

    headers = {"Authorization": f"Bearer {admin_token}"}

    response = await client.post(
        "/api/v1/applications",
        json=app_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    app_id = response.json()["id"]

    # Update application
    update_data = {"application_name": "Updated Name"}
    response = await client.put(
        f"/api/v1/applications/{app_id}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Get audit logs
    response = await client.get(
        f"/api/v1/audit/record/applications/{app_id}",
        headers=headers
    )
    audit_history = response.json()
    initial_count = audit_history["total_operations"]

    # Find UPDATE log
    update_log_id = None
    for log in audit_history["history"]:
        if log["operation"] == "UPDATE":
            update_log_id = log["id"]
            break

    # Perform rollback
    rollback_data = {
        "confirm": True,
        "reason": "Test audit creation"
    }

    response = await client.post(
        f"/api/v1/audit/{update_log_id}/rollback",
        json=rollback_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    rollback_result = response.json()

    # Check that a new audit log was created
    response = await client.get(
        f"/api/v1/audit/record/applications/{app_id}",
        headers=headers
    )
    audit_history_after = response.json()

    assert audit_history_after["total_operations"] > initial_count

    # Verify the rollback audit log
    response = await client.get(
        f"/api/v1/audit/{rollback_result['rollback_audit_id']}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    rollback_audit = response.json()

    assert "Rollback of UPDATE" in rollback_audit["reason"]
    assert f"audit_id={update_log_id}" in rollback_audit["reason"]