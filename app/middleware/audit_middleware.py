"""
Audit middleware for automatic audit log creation
"""

import json
import uuid
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from app.core.database import get_db
from app.services.audit_service import AuditService
from app.models.audit_log import AuditOperation
from app.models.user import User


class AuditMiddleware:
    """Middleware for automatic audit logging."""

    def __init__(self):
        self.audit_service = AuditService()
        self.excluded_paths = [
            "/docs",
            "/openapi.json",
            "/health",
            "/metrics",
            "/audit"  # Don't audit the audit endpoints themselves
        ]
        self.excluded_tables = [
            "audit_logs"  # Don't audit the audit logs table
        ]

    async def __call__(self, request: Request, call_next: Callable):
        """Process request and create audit logs if needed."""

        # Skip audit for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Generate request ID for correlation
        request_id = str(uuid.uuid4())

        # Store request context
        request.state.audit_request_id = request_id
        request.state.audit_user_ip = self._get_client_ip(request)
        request.state.audit_user_agent = request.headers.get("user-agent")

        # Process the request
        response = await call_next(request)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"

    async def create_audit_log_for_model(
        self,
        db: AsyncSession,
        model_instance: Any,
        operation: AuditOperation,
        user: Optional[User] = None,
        request_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None
    ):
        """Create audit log for a model instance."""

        # Skip if table is excluded
        table_name = model_instance.__tablename__
        if table_name in self.excluded_tables:
            return

        # Get model data
        new_values = self._extract_model_values(model_instance)
        record_id = getattr(model_instance, 'id', None)

        if record_id is None:
            # Can't audit without record ID
            return

        try:
            await self.audit_service.create_audit_log(
                db=db,
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                old_values=old_values,
                new_values=new_values,
                user_id=user.id if user else None,
                request_id=request_id,
                user_ip=user_ip,
                user_agent=user_agent,
                reason=reason
            )
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Audit logging failed: {str(e)}")

    def _extract_model_values(self, model_instance: Any) -> Dict[str, Any]:
        """Extract values from a SQLAlchemy model instance."""
        values = {}
        mapper = inspect(model_instance.__class__)

        for column in mapper.columns:
            column_name = column.name
            value = getattr(model_instance, column_name, None)

            # Convert non-serializable types
            if value is not None:
                if hasattr(value, 'isoformat'):  # datetime, date, time
                    values[column_name] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    values[column_name] = json.loads(json.dumps(value, default=str))
                else:
                    values[column_name] = value

        return values

    def _get_changed_values(self, old_instance: Any, new_instance: Any) -> tuple:
        """Compare two model instances and return old/new values."""
        old_values = self._extract_model_values(old_instance)
        new_values = self._extract_model_values(new_instance)
        return old_values, new_values


# Utility functions for manual audit logging

async def audit_create(
    db: AsyncSession,
    model_instance: Any,
    user: Optional[User] = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None
):
    """Manually create audit log for INSERT operation."""
    middleware = AuditMiddleware()
    await middleware.create_audit_log_for_model(
        db=db,
        model_instance=model_instance,
        operation=AuditOperation.INSERT,
        user=user,
        request_id=request_id,
        user_ip=user_ip,
        user_agent=user_agent,
        reason=reason
    )


async def audit_update(
    db: AsyncSession,
    old_instance: Any,
    new_instance: Any,
    user: Optional[User] = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None
):
    """Manually create audit log for UPDATE operation."""
    middleware = AuditMiddleware()
    old_values, _ = middleware._get_changed_values(old_instance, new_instance)

    await middleware.create_audit_log_for_model(
        db=db,
        model_instance=new_instance,
        operation=AuditOperation.UPDATE,
        user=user,
        request_id=request_id,
        user_ip=user_ip,
        user_agent=user_agent,
        reason=reason,
        old_values=old_values
    )


async def audit_delete(
    db: AsyncSession,
    model_instance: Any,
    user: Optional[User] = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None
):
    """Manually create audit log for DELETE operation."""
    middleware = AuditMiddleware()
    old_values = middleware._extract_model_values(model_instance)

    await middleware.create_audit_log_for_model(
        db=db,
        model_instance=model_instance,
        operation=AuditOperation.DELETE,
        user=user,
        request_id=request_id,
        user_ip=user_ip,
        user_agent=user_agent,
        reason=reason,
        old_values=old_values
    )