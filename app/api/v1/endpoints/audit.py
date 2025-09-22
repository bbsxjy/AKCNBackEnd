"""
Audit Log API endpoints
"""

import time
import io
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User, UserRole
from app.models.audit_log import AuditOperation
from app.services.audit_service import AuditService
from app.schemas.audit import (
    AuditLogResponse, AuditLogListResponse, AuditLogFilter,
    RecordHistoryResponse, UserActivityResponse, AuditStatistics,
    DataChangesSummary, ComplianceReport, AuditCleanupRequest,
    AuditCleanupResult, AuditHealthCheck, RollbackRequest, RollbackResponse,
    AuditExportRequest, AuditExportResponse
)

router = APIRouter()
audit_service = AuditService()


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    operation: Optional[AuditOperation] = Query(None, description="Filter by operation"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    search: Optional[str] = Query(None, description="Search in reason, user agent, or request ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """List audit logs with filtering and pagination."""

    try:
        audit_logs, total = await audit_service.list_audit_logs(
            db=db,
            skip=skip,
            limit=limit,
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            search=search
        )

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1

        # Transform to response format
        items = []
        for log in audit_logs:
            item = AuditLogResponse(
                id=log.id,
                table_name=log.table_name,
                record_id=log.record_id,
                operation=log.operation,
                old_values=log.old_values,
                new_values=log.new_values,
                changed_fields=log.changed_fields,
                request_id=log.request_id,
                user_ip=log.user_ip,
                user_agent=log.user_agent,
                reason=log.reason,
                metadata=log.extra_data,
                user_id=log.user_id,
                username=log.user.username if log.user else None,
                user_full_name=log.user.full_name if log.user else None,
                created_at=log.created_at,
                is_insert=log.is_insert,
                is_update=log.is_update,
                is_delete=log.is_delete,
                field_changes=log.get_field_changes()
            )
            items.append(item)

        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            items=items
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get audit log by ID."""
    audit_log = await audit_service.get_audit_log(db=db, audit_log_id=audit_log_id)
    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    return AuditLogResponse(
        id=audit_log.id,
        table_name=audit_log.table_name,
        record_id=audit_log.record_id,
        operation=audit_log.operation,
        old_values=audit_log.old_values,
        new_values=audit_log.new_values,
        changed_fields=audit_log.changed_fields,
        request_id=audit_log.request_id,
        user_ip=audit_log.user_ip,
        user_agent=audit_log.user_agent,
        reason=audit_log.reason,
        metadata=audit_log.metadata,
        user_id=audit_log.user_id,
        username=audit_log.user.username if audit_log.user else None,
        user_full_name=audit_log.user.full_name if audit_log.user else None,
        created_at=audit_log.created_at,
        is_insert=audit_log.is_insert,
        is_update=audit_log.is_update,
        is_delete=audit_log.is_delete,
        field_changes=audit_log.get_field_changes()
    )


@router.get("/record/{table_name}/{record_id}", response_model=RecordHistoryResponse)
async def get_record_history(
    table_name: str,
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Get complete history for a specific record."""
    try:
        history = await audit_service.get_record_history(
            db=db,
            table_name=table_name,
            record_id=record_id
        )

        # Return empty history instead of 404 if no audit records exist
        if not history:
            return RecordHistoryResponse(
                table_name=table_name,
                record_id=record_id,
                history=[],
                total_operations=0,
                created_at=None,
                last_modified_at=None,
                created_by=None,
                last_modified_by=None
            )

        # Transform history
        history_items = []
        for log in history:
            item = AuditLogResponse(
                id=log.id,
                table_name=log.table_name,
                record_id=log.record_id,
                operation=log.operation,
                old_values=log.old_values,
                new_values=log.new_values,
                changed_fields=log.changed_fields,
                request_id=log.request_id,
                user_ip=log.user_ip,
                user_agent=log.user_agent,
                reason=log.reason,
                metadata=log.extra_data,
                user_id=log.user_id,
                username=log.user.username if log.user else None,
                user_full_name=log.user.full_name if log.user else None,
                created_at=log.created_at,
                is_insert=log.is_insert,
                is_update=log.is_update,
                is_delete=log.is_delete,
                field_changes=log.get_field_changes()
            )
            history_items.append(item)

        # Find creation and last modification info
        creation_log = None
        latest_log = history[0] if history else None

        for log in reversed(history):
            if log.operation == AuditOperation.INSERT:
                creation_log = log
                break

        return RecordHistoryResponse(
            table_name=table_name,
            record_id=record_id,
            history=history_items,
            total_operations=len(history),
            created_at=creation_log.created_at if creation_log else None,
            last_modified_at=latest_log.created_at if latest_log else None,
            created_by=creation_log.user.username if creation_log and creation_log.user else None,
            last_modified_by=latest_log.user.username if latest_log and latest_log.user else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve record history: {str(e)}"
        )


@router.get("/user/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: int,
    start_date: Optional[date] = Query(None, description="Start date for activity"),
    end_date: Optional[date] = Query(None, description="End date for activity"),
    limit: int = Query(100, ge=1, le=500, description="Limit for recent activity"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get audit activity for a specific user."""
    try:
        # Get user info
        from sqlalchemy import select
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get activity
        activity = await audit_service.get_user_activity(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        # Process activity data
        operations_breakdown = {}
        tables_affected = set()
        recent_activity = []

        for log in activity:
            # Count operations
            op = log.operation
            operations_breakdown[op] = operations_breakdown.get(op, 0) + 1

            # Track tables
            tables_affected.add(log.table_name)

            # Add to recent activity
            item = AuditLogResponse(
                id=log.id,
                table_name=log.table_name,
                record_id=log.record_id,
                operation=log.operation,
                old_values=log.old_values,
                new_values=log.new_values,
                changed_fields=log.changed_fields,
                request_id=log.request_id,
                user_ip=log.user_ip,
                user_agent=log.user_agent,
                reason=log.reason,
                metadata=log.extra_data,
                user_id=log.user_id,
                username=log.user.username,
                user_full_name=log.user.full_name,
                created_at=log.created_at,
                is_insert=log.is_insert,
                is_update=log.is_update,
                is_delete=log.is_delete,
                field_changes=log.get_field_changes()
            )
            recent_activity.append(item)

        return UserActivityResponse(
            user_id=user_id,
            username=user.username,
            full_name=user.full_name,
            activity_period={
                "start_date": start_date.isoformat() if start_date else "N/A",
                "end_date": end_date.isoformat() if end_date else "N/A"
            },
            total_operations=len(activity),
            operations_breakdown=operations_breakdown,
            tables_affected=list(tables_affected),
            recent_activity=recent_activity
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user activity: {str(e)}"
        )


@router.get("/statistics", response_model=AuditStatistics)
async def get_audit_statistics(
    start_date: Optional[date] = Query(None, description="Start date for statistics"),
    end_date: Optional[date] = Query(None, description="End date for statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get audit log statistics."""
    try:
        stats = await audit_service.get_audit_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        return AuditStatistics(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/record/{table_name}/{record_id}/summary", response_model=DataChangesSummary)
async def get_data_changes_summary(
    table_name: str,
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Get summary of all changes made to a specific record."""
    try:
        summary = await audit_service.get_data_changes_summary(
            db=db,
            table_name=table_name,
            record_id=record_id
        )
        return DataChangesSummary(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve changes summary: {str(e)}"
        )


@router.post("/export")
async def export_audit_trail(
    export_request: AuditExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Export audit trail data in various formats.

    Supported formats:
    - json: Returns data as JSON response
    - csv: Returns downloadable CSV file
    - excel: Returns downloadable Excel file with summary
    """
    try:
        export_format = export_request.format.lower()

        # Apply filters from request
        table_name = export_request.table_name
        record_id = export_request.record_id
        user_id = export_request.user_id
        operation = export_request.operation
        start_date = export_request.start_date
        end_date = export_request.end_date

        if export_format == "csv":
            # Export to CSV
            csv_data = await audit_service.export_audit_trail_to_csv(
                db=db,
                table_name=table_name,
                record_id=record_id,
                user_id=user_id,
                operation=operation,
                start_date=start_date,
                end_date=end_date
            )

            filename = f"audit_trail_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            return StreamingResponse(
                io.BytesIO(csv_data),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )

        elif export_format == "excel":
            # Export to Excel
            excel_data = await audit_service.export_audit_trail_to_excel(
                db=db,
                table_name=table_name,
                record_id=record_id,
                user_id=user_id,
                operation=operation,
                start_date=start_date,
                end_date=end_date
            )

            filename = f"audit_trail_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
            return StreamingResponse(
                io.BytesIO(excel_data),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }
            )

        else:  # Default to JSON
            # Export as JSON
            export_data = await audit_service.export_audit_trail(
                db=db,
                table_name=table_name,
                record_id=record_id,
                start_date=start_date,
                end_date=end_date
            )

            return AuditExportResponse(
                export_format="json",
                total_records=len(export_data),
                export_timestamp=datetime.utcnow(),
                filters_applied={
                    "table_name": table_name,
                    "record_id": record_id,
                    "user_id": user_id,
                    "operation": operation.value if operation else None,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                data=export_data
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit trail: {str(e)}"
        )


@router.get("/compliance/report", response_model=ComplianceReport)
async def get_compliance_report(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Generate compliance report for audit trail."""
    try:
        report = await audit_service.get_compliance_report(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        return ComplianceReport(**report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.post("/cleanup", response_model=AuditCleanupResult)
async def cleanup_old_audit_logs(
    cleanup_request: AuditCleanupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Clean up old audit logs beyond retention period."""
    if not cleanup_request.dry_run and not cleanup_request.confirm_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must set confirm_deletion=true for actual deletion"
        )

    try:
        start_time = time.time()

        if cleanup_request.dry_run:
            # Count logs that would be deleted
            from datetime import timedelta
            cutoff_date = date.today() - timedelta(days=cleanup_request.days_to_keep)

            from sqlalchemy import func, select
            count_result = await db.execute(
                select(func.count(audit_service.model.id))
                .where(audit_service.model.created_at < cutoff_date)
            )
            logs_identified = count_result.scalar()
            logs_deleted = 0
        else:
            # Actually delete logs
            logs_deleted = await audit_service.cleanup_old_logs(
                db=db,
                days_to_keep=cleanup_request.days_to_keep
            )
            logs_identified = logs_deleted

        execution_time = int((time.time() - start_time) * 1000)

        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=cleanup_request.days_to_keep)

        return AuditCleanupResult(
            logs_identified=logs_identified,
            logs_deleted=logs_deleted,
            dry_run=cleanup_request.dry_run,
            cutoff_date=cutoff_date.isoformat(),
            execution_time_ms=execution_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup audit logs: {str(e)}"
        )


@router.get("/health", response_model=AuditHealthCheck)
async def audit_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Check audit system health."""
    try:
        from sqlalchemy import func, select, text
        from datetime import timedelta

        start_time = time.time()

        # Basic counts
        total_logs_result = await db.execute(select(func.count(audit_service.model.id)))
        total_logs = total_logs_result.scalar()

        # Last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        last_24h_result = await db.execute(
            select(func.count(audit_service.model.id))
            .where(audit_service.model.created_at >= yesterday)
        )
        logs_last_24h = last_24h_result.scalar()

        # Oldest and newest logs
        oldest_result = await db.execute(
            select(func.min(audit_service.model.created_at))
        )
        oldest_log = oldest_result.scalar()

        newest_result = await db.execute(
            select(func.max(audit_service.model.created_at))
        )
        newest_log = newest_result.scalar()

        # Calculate average logs per day
        if oldest_log and newest_log:
            days_span = (newest_log - oldest_log).days or 1
            average_logs_per_day = total_logs / days_span
        else:
            average_logs_per_day = 0

        # Performance metrics
        execution_time = int((time.time() - start_time) * 1000)
        performance_metrics = {
            "health_check_time_ms": execution_time,
            "database_responsive": True
        }

        # Identify issues
        issues = []
        if total_logs == 0:
            issues.append("No audit logs found - audit system may not be functioning")
        elif logs_last_24h == 0:
            issues.append("No audit logs in the last 24 hours")

        if execution_time > 5000:  # 5 seconds
            issues.append("Slow database response time")

        status = "healthy" if not issues else "warning" if len(issues) == 1 else "unhealthy"

        return AuditHealthCheck(
            status=status,
            total_logs=total_logs,
            logs_last_24h=logs_last_24h,
            average_logs_per_day=average_logs_per_day,
            oldest_log=oldest_log.isoformat() if oldest_log else None,
            newest_log=newest_log.isoformat() if newest_log else None,
            storage_size_mb=None,  # Would require database-specific queries
            performance_metrics=performance_metrics,
            issues=issues
        )

    except Exception as e:
        return AuditHealthCheck(
            status="unhealthy",
            total_logs=0,
            logs_last_24h=0,
            average_logs_per_day=0,
            oldest_log=None,
            newest_log=None,
            storage_size_mb=None,
            performance_metrics={"error": str(e)},
            issues=[f"Health check failed: {str(e)}"]
        )


@router.post("/{audit_log_id}/rollback", response_model=RollbackResponse)
async def rollback_audit_change(
    audit_log_id: int,
    rollback_request: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    Rollback a change based on audit log entry.

    This endpoint allows authorized users to rollback a previously recorded change:
    - For INSERT operations: The record will be deleted
    - For UPDATE operations: The old values will be restored
    - For DELETE operations: The record will be re-inserted with original values

    Note: The rollback operation itself will be recorded in the audit log.
    """

    if not rollback_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rollback confirmation required. Set confirm=true to proceed."
        )

    try:
        # Get request context
        import uuid
        request_id = str(uuid.uuid4())

        # Perform rollback
        result = await audit_service.rollback_change(
            db=db,
            audit_log_id=audit_log_id,
            user_id=current_user.id,
            reason=rollback_request.reason,
            request_id=request_id,
            user_ip=None,  # Would be extracted from request in production
            user_agent=None  # Would be extracted from request headers in production
        )

        # Format response
        return RollbackResponse(
            status="success",
            rollback_audit_id=result["rollback_audit_id"],
            affected_record=result["affected_record"],
            message=f"Successfully rolled back audit log {audit_log_id}. "
                   f"Operation: {result['affected_record']['operation']} on "
                   f"{result['affected_record']['table']} record {result['affected_record']['id']}"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback audit change: {str(e)}"
        )