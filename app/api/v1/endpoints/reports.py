"""
Report Generation API endpoints
"""

import time
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import Response, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.report_service import ReportService, ReportType as ServiceReportType
from app.schemas.report import (
    ProgressSummaryRequest, ProgressSummaryResponse,
    DepartmentComparisonRequest, DepartmentComparisonResponse,
    DelayedProjectsRequest, DelayedProjectsResponse,
    TrendAnalysisRequest, TrendAnalysisResponse,
    CustomReportRequest, CustomReportResponse,
    ReportExportRequest, ReportExportResponse,
    ReportListRequest, ReportListResponse,
    ReportHealthCheck, ReportTemplate,
    ExportFormat
)

router = APIRouter()
report_service = ReportService()


@router.post("/progress-summary", response_model=ProgressSummaryResponse)
async def generate_progress_summary_report(
    request: ProgressSummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Generate progress summary report."""

    start_time = time.time()

    try:
        report_data = await report_service.generate_progress_summary_report(
            db=db,
            supervision_year=request.supervision_year,
            responsible_team=request.responsible_team,
            transformation_target=request.transformation_target,
            include_details=request.include_details
        )

        # Add metadata
        generation_time = int((time.time() - start_time) * 1000)
        report_data["generation_time_ms"] = generation_time

        # Handle export if requested
        if request.export_format and request.export_format != ExportFormat.JSON:
            export_url = await _export_report(
                report_data,
                request.export_format,
                "progress_summary"
            )
            report_data["export_url"] = export_url

        return ProgressSummaryResponse(**report_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate progress summary report: {str(e)}"
        )


@router.post("/department-comparison", response_model=DepartmentComparisonResponse)
async def generate_department_comparison_report(
    request: DepartmentComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Generate department/team comparison report."""

    start_time = time.time()

    try:
        report_data = await report_service.generate_department_comparison_report(
            db=db,
            supervision_year=request.supervision_year,
            include_subtasks=request.include_subtasks
        )

        # Add metadata
        generation_time = int((time.time() - start_time) * 1000)
        report_data["generation_time_ms"] = generation_time

        # Handle export if requested
        if request.export_format and request.export_format != ExportFormat.JSON:
            export_url = await _export_report(
                report_data,
                request.export_format,
                "department_comparison"
            )
            report_data["export_url"] = export_url

        return DepartmentComparisonResponse(**report_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate department comparison report: {str(e)}"
        )


@router.post("/delayed-projects", response_model=DelayedProjectsResponse)
async def generate_delayed_projects_report(
    request: DelayedProjectsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Generate delayed projects report with analysis."""

    start_time = time.time()

    try:
        report_data = await report_service.generate_delayed_projects_report(
            db=db,
            supervision_year=request.supervision_year,
            responsible_team=request.responsible_team,
            severity_threshold=request.severity_threshold
        )

        # Add metadata
        generation_time = int((time.time() - start_time) * 1000)
        report_data["generation_time_ms"] = generation_time

        # Handle export if requested
        if request.export_format and request.export_format != ExportFormat.JSON:
            export_url = await _export_report(
                report_data,
                request.export_format,
                "delayed_projects"
            )
            report_data["export_url"] = export_url

        return DelayedProjectsResponse(**report_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate delayed projects report: {str(e)}"
        )


@router.post("/trend-analysis", response_model=TrendAnalysisResponse)
async def generate_trend_analysis_report(
    request: TrendAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Generate trend analysis report with historical data."""

    start_time = time.time()

    try:
        report_data = await report_service.generate_trend_analysis_report(
            db=db,
            supervision_year=request.supervision_year,
            time_period=request.time_period.value,
            metrics=request.metrics
        )

        # Add metadata
        generation_time = int((time.time() - start_time) * 1000)
        report_data["generation_time_ms"] = generation_time

        # Handle export if requested
        if request.export_format and request.export_format != ExportFormat.JSON:
            export_url = await _export_report(
                report_data,
                request.export_format,
                "trend_analysis"
            )
            report_data["export_url"] = export_url

        return TrendAnalysisResponse(**report_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend analysis report: {str(e)}"
        )


@router.post("/custom", response_model=CustomReportResponse)
async def generate_custom_report(
    request: CustomReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Generate custom report based on user configuration."""

    start_time = time.time()

    try:
        # Convert configuration to dict
        config_dict = request.report_config.dict()

        report_data = await report_service.generate_custom_report(
            db=db,
            report_config=config_dict
        )

        # Add metadata
        generation_time = int((time.time() - start_time) * 1000)
        report_data["generation_time_ms"] = generation_time

        # Save as template if requested
        template_saved = False
        if request.save_as_template:
            template_id = await _save_report_template(
                config_dict,
                current_user.id
            )
            template_saved = True
            report_data["template_id"] = template_id

        report_data["template_saved"] = template_saved

        # Handle export if requested
        if request.export_format and request.export_format != ExportFormat.JSON:
            export_url = await _export_report(
                report_data,
                request.export_format,
                "custom_report"
            )
            report_data["export_url"] = export_url

        return CustomReportResponse(**report_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom report: {str(e)}"
        )


@router.post("/export", response_model=ReportExportResponse)
async def export_report(
    request: ReportExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Export report in specified format."""

    try:
        # Generate unique file name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"{request.report_type.value}_{timestamp}"

        if request.export_format == ExportFormat.PDF:
            file_name += ".pdf"
            # Generate PDF (using reportlab or similar)
            file_content = await _generate_pdf_report(request.report_data, request.template_style)

        elif request.export_format == ExportFormat.EXCEL:
            file_name += ".xlsx"
            # Generate Excel (using openpyxl)
            file_content = await _generate_excel_report(request.report_data, request.include_charts)

        elif request.export_format == ExportFormat.HTML:
            file_name += ".html"
            # Generate HTML report
            file_content = await _generate_html_report(request.report_data, request.include_charts)

        elif request.export_format == ExportFormat.CSV:
            file_name += ".csv"
            # Generate CSV
            file_content = await _generate_csv_report(request.report_data)

        else:
            raise ValueError(f"Unsupported export format: {request.export_format}")

        # Save file and generate download URL
        download_url = await _save_export_file(file_content, file_name)

        # Schedule cleanup after 1 hour
        background_tasks.add_task(_cleanup_export_file, file_name, 3600)

        return ReportExportResponse(
            success=True,
            export_format=request.export_format,
            file_name=file_name,
            file_size_bytes=len(file_content),
            download_url=download_url,
            expires_at=(datetime.utcnow().replace(microsecond=0) + timedelta(hours=1)).isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export report: {str(e)}"
        )


@router.get("/templates", response_model=List[ReportTemplate])
async def list_report_templates(
    report_type: Optional[ServiceReportType] = Query(None, description="Filter by report type"),
    is_public: Optional[bool] = Query(None, description="Filter by public templates"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """List available report templates."""

    # Mock template data - in production, query from database
    templates = [
        {
            "template_id": "tpl_001",
            "template_name": "月度进度报表",
            "report_type": ServiceReportType.PROGRESS_SUMMARY,
            "configuration": {
                "filters": {"supervision_year": 2024},
                "include_details": True
            },
            "created_by": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "usage_count": 15,
            "is_public": True
        },
        {
            "template_id": "tpl_002",
            "template_name": "团队绩效对比",
            "report_type": ServiceReportType.DEPARTMENT_COMPARISON,
            "configuration": {
                "include_subtasks": True
            },
            "created_by": 1,
            "created_at": "2024-01-05T10:30:00Z",
            "usage_count": 8,
            "is_public": True
        },
        {
            "template_id": "tpl_003",
            "template_name": "风险项目追踪",
            "report_type": ServiceReportType.DELAYED_PROJECTS,
            "configuration": {
                "severity_threshold": 14
            },
            "created_by": current_user.id,
            "created_at": "2024-01-10T14:00:00Z",
            "usage_count": 5,
            "is_public": False
        }
    ]

    # Filter templates
    filtered_templates = templates

    if report_type:
        filtered_templates = [t for t in filtered_templates if t["report_type"] == report_type]

    if is_public is not None:
        filtered_templates = [t for t in filtered_templates if t["is_public"] == is_public]

    # Filter by ownership (private templates only visible to owner)
    final_templates = []
    for template in filtered_templates:
        if template["is_public"] or template["created_by"] == current_user.id:
            final_templates.append(ReportTemplate(**template))

    return final_templates


@router.get("/history", response_model=ReportListResponse)
async def get_report_history(
    request: ReportListRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Get report generation history."""

    # Mock history data - in production, query from database
    mock_reports = [
        {
            "report_id": str(uuid.uuid4()),
            "report_type": ServiceReportType.PROGRESS_SUMMARY,
            "generated_by": current_user.id,
            "generated_at": "2024-01-15T10:30:00Z",
            "filters_applied": {"supervision_year": 2024},
            "data_snapshot_time": "2024-01-15T10:29:55Z",
            "generation_time_ms": 2500,
            "export_formats": [ExportFormat.JSON, ExportFormat.PDF, ExportFormat.EXCEL]
        },
        {
            "report_id": str(uuid.uuid4()),
            "report_type": ServiceReportType.DELAYED_PROJECTS,
            "generated_by": current_user.id,
            "generated_at": "2024-01-14T14:20:00Z",
            "filters_applied": {"severity_threshold": 7},
            "data_snapshot_time": "2024-01-14T14:19:50Z",
            "generation_time_ms": 3200,
            "export_formats": [ExportFormat.JSON, ExportFormat.EXCEL]
        }
    ]

    # Apply filters
    filtered_reports = mock_reports

    if request.report_type:
        filtered_reports = [r for r in filtered_reports if r["report_type"] == request.report_type]

    # Sort reports
    if request.sort_order == "desc":
        filtered_reports.sort(key=lambda x: x[request.sort_by], reverse=True)
    else:
        filtered_reports.sort(key=lambda x: x[request.sort_by])

    # Paginate
    total = len(filtered_reports)
    start = request.skip
    end = start + request.limit
    paginated_reports = filtered_reports[start:end]

    return ReportListResponse(
        total=total,
        page=(request.skip // request.limit) + 1,
        page_size=request.limit,
        reports=paginated_reports
    )


@router.get("/health", response_model=ReportHealthCheck)
async def report_service_health_check(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Check report service health and status."""

    try:
        # Mock health metrics - in production, gather real metrics
        return ReportHealthCheck(
            status="healthy",
            active_generations=2,
            queue_depth=5,
            average_generation_time_ms=2800.5,
            total_generated_today=45,
            error_rate_percentage=1.5,
            cache_hit_rate=75.3
        )

    except Exception as e:
        return ReportHealthCheck(
            status="unhealthy",
            active_generations=0,
            queue_depth=0,
            average_generation_time_ms=0,
            total_generated_today=0,
            error_rate_percentage=100,
            cache_hit_rate=0
        )


@router.get("/chart-types")
async def get_available_chart_types(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Get available chart types and their configurations."""

    return {
        "chart_types": [
            {
                "type": "bar",
                "name": "柱状图",
                "description": "适用于分类数据对比",
                "supports_multiple_series": True,
                "recommended_for": ["comparison", "distribution"]
            },
            {
                "type": "line",
                "name": "折线图",
                "description": "适用于趋势展示",
                "supports_multiple_series": True,
                "recommended_for": ["trend", "time_series"]
            },
            {
                "type": "pie",
                "name": "饼图",
                "description": "适用于占比分析",
                "supports_multiple_series": False,
                "recommended_for": ["proportion", "composition"]
            },
            {
                "type": "doughnut",
                "name": "环形图",
                "description": "类似饼图，中心镂空",
                "supports_multiple_series": False,
                "recommended_for": ["proportion", "composition"]
            },
            {
                "type": "area",
                "name": "面积图",
                "description": "适用于累积趋势",
                "supports_multiple_series": True,
                "recommended_for": ["trend", "cumulative"]
            },
            {
                "type": "radar",
                "name": "雷达图",
                "description": "适用于多维度对比",
                "supports_multiple_series": True,
                "recommended_for": ["multi_dimension", "comparison"]
            }
        ]
    }


@router.get("/metrics")
async def get_available_metrics(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Get available metrics for reports."""

    return {
        "metrics": [
            {
                "id": "total_count",
                "name": "总数量",
                "description": "记录总数",
                "data_type": "integer",
                "aggregation": "count"
            },
            {
                "id": "average_progress",
                "name": "平均进度",
                "description": "平均进度百分比",
                "data_type": "float",
                "aggregation": "average",
                "unit": "%"
            },
            {
                "id": "completion_rate",
                "name": "完成率",
                "description": "完成项目占比",
                "data_type": "float",
                "aggregation": "percentage",
                "unit": "%"
            },
            {
                "id": "delay_rate",
                "name": "延期率",
                "description": "延期项目占比",
                "data_type": "float",
                "aggregation": "percentage",
                "unit": "%"
            },
            {
                "id": "blocked_tasks",
                "name": "阻塞任务",
                "description": "阻塞任务数量",
                "data_type": "integer",
                "aggregation": "count"
            },
            {
                "id": "team_count",
                "name": "团队数量",
                "description": "涉及团队数",
                "data_type": "integer",
                "aggregation": "distinct_count"
            }
        ]
    }


# Helper functions

async def _export_report(
    report_data: Dict[str, Any],
    export_format: ExportFormat,
    report_type: str
) -> str:
    """Export report and return download URL."""
    # Implementation would handle actual export
    # For now, return mock URL
    return f"/api/v1/reports/download/{report_type}_{uuid.uuid4()}.{export_format.value}"


async def _save_report_template(
    config: Dict[str, Any],
    user_id: int
) -> str:
    """Save report configuration as template."""
    # Implementation would save to database
    # For now, return mock template ID
    return f"tpl_{uuid.uuid4().hex[:8]}"


async def _generate_pdf_report(
    data: Dict[str, Any],
    template_style: str
) -> bytes:
    """Generate PDF report."""
    # Implementation would use reportlab or similar
    # For now, return mock content
    return b"PDF content"


async def _generate_excel_report(
    data: Dict[str, Any],
    include_charts: bool
) -> bytes:
    """Generate Excel report."""
    # Implementation would use openpyxl
    # For now, return mock content
    import io
    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Report"

    # Add headers
    worksheet.append(["Report Generated", datetime.utcnow().isoformat()])

    # Save to bytes
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output.getvalue()


async def _generate_html_report(
    data: Dict[str, Any],
    include_charts: bool
) -> bytes:
    """Generate HTML report."""
    # Implementation would use Jinja2 templates
    # For now, return mock content
    html = f"""
    <html>
    <head><title>Report</title></head>
    <body>
        <h1>Report</h1>
        <p>Generated at: {datetime.utcnow().isoformat()}</p>
    </body>
    </html>
    """
    return html.encode('utf-8')


async def _generate_csv_report(data: Dict[str, Any]) -> bytes:
    """Generate CSV report."""
    # Implementation would use pandas
    # For now, return mock content
    csv_content = "column1,column2,column3\nvalue1,value2,value3\n"
    return csv_content.encode('utf-8')


async def _save_export_file(content: bytes, file_name: str) -> str:
    """Save export file and return download URL."""
    # Implementation would save to storage
    # For now, return mock URL
    return f"/api/v1/reports/download/{file_name}"


async def _cleanup_export_file(file_name: str, delay: int):
    """Clean up export file after delay."""
    # Implementation would delete file after delay
    import asyncio
    await asyncio.sleep(delay)
    # Delete file
    pass


# Import timedelta for expiration calculation
from datetime import timedelta