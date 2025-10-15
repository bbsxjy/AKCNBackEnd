"""
CMDB System Catalog API Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.schemas.cmdb import (
    CMDBL2ApplicationResponse,
    CMDBL2ApplicationSearch,
    CMDBL1System156Response,
    CMDBL1System156Search,
    CMDBL1System87Response,
    CMDBL1System87Search,
    CMDBImportRequest,
    CMDBImportResponse,
    CMDBStatistics,
    CMDBL2WithL1Response
)
from app.services.cmdb_query_service import CMDBQueryService
from app.services.cmdb_import_service import CMDBImportService
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/l2/search", response_model=List[CMDBL2ApplicationResponse])
async def search_l2_applications(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    status: Optional[str] = Query(None, description="Filter by status"),
    management_level: Optional[str] = Query(None, description="Filter by management level"),
    belongs_to_156l1: Optional[str] = Query(None, description="Filter by 156L1 system"),
    belongs_to_87l1: Optional[str] = Query(None, description="Filter by 87L1 system"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search L2 applications in CMDB system catalog

    - **keyword**: Search in short_name, other_names, config_id, description
    - **status**: Filter by application status
    - **management_level**: Filter by management level
    - **belongs_to_156l1**: Filter by 156L1 system
    - **belongs_to_87l1**: Filter by 87L1 system
    """
    apps = await CMDBQueryService.search_l2_applications(
        db,
        keyword=keyword,
        status=status,
        management_level=management_level,
        belongs_to_156l1=belongs_to_156l1,
        belongs_to_87l1=belongs_to_87l1,
        limit=limit,
        offset=offset
    )
    return apps


@router.get("/l2/{config_id}", response_model=CMDBL2ApplicationResponse)
async def get_l2_application(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get L2 application by config_id"""
    app = await CMDBQueryService.get_l2_application_by_config_id(db, config_id)
    if not app:
        raise HTTPException(status_code=404, detail="L2 application not found")
    return app


@router.get("/l2/with-l1/{keyword}", response_model=CMDBL2WithL1Response)
async def get_l2_with_l1_info(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get L2 application with related L1 system information

    满足需求场景3: XX应用的管理级别是多少？其所属156L1系统是什么？
    """
    result = await CMDBQueryService.get_l2_application_with_l1_info(db, keyword)
    return result


@router.get("/156l1/search", response_model=List[CMDBL1System156Response])
async def search_156l1_systems(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    layer: Optional[str] = Query(None, description="Filter by layer"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search 156L1 systems (current L1 classification)

    - **keyword**: Search in short_name, config_id
    - **domain**: Filter by domain (所属域)
    - **layer**: Filter by layer (所属层)
    """
    systems = await CMDBQueryService.search_l1_156_systems(
        db, keyword=keyword, domain=domain, layer=layer, limit=limit
    )
    return systems


@router.get("/87l1/search", response_model=List[CMDBL1System87Response])
async def search_87l1_systems(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    layer: Optional[str] = Query(None, description="Filter by layer"),
    is_critical: Optional[str] = Query(None, description="Filter by critical system"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search 87L1 systems (future L1 classification)

    - **keyword**: Search in short_name, config_id, description
    - **domain**: Filter by domain (所属域)
    - **layer**: Filter by layer (所属层)
    - **is_critical**: Filter by critical system (是否为关键系统)
    """
    systems = await CMDBQueryService.search_l1_87_systems(
        db,
        keyword=keyword,
        domain=domain,
        layer=layer,
        is_critical=is_critical,
        limit=limit
    )
    return systems


@router.get("/l1/{l1_type}/{l1_system_name}/applications", response_model=List[CMDBL2ApplicationResponse])
async def get_l2_by_l1_system(
    l1_type: str,
    l1_system_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get L2 applications that belong to a specific L1 system

    - **l1_type**: L1 system type ("156" or "87")
    - **l1_system_name**: L1 system name
    """
    if l1_type not in ["156", "87"]:
        raise HTTPException(status_code=400, detail="l1_type must be '156' or '87'")

    apps = await CMDBQueryService.get_l2_applications_by_l1_system(
        db, l1_system_name, l1_type
    )
    return apps


@router.get("/statistics", response_model=CMDBStatistics)
async def get_cmdb_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get CMDB system catalog statistics"""
    stats = await CMDBQueryService.get_statistics(db)

    return CMDBStatistics(
        l2_applications_total=stats["l2_applications"]["total"],
        l1_156_systems_total=stats["l1_156_systems"]["total"],
        l1_87_systems_total=stats["l1_87_systems"]["total"],
        l2_by_status=stats["l2_applications"]["by_status"],
        l2_by_management_level=stats["l2_applications"]["by_management_level"]
    )


@router.post("/import", response_model=CMDBImportResponse)
async def import_cmdb_data(
    request: CMDBImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import CMDB data from Excel file

    - **file_path**: Path to the Excel file
    - **replace_existing**: Whether to replace existing data (default: False)

    Note: Only admin users can import data
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin users can import CMDB data")

    try:
        result = await CMDBImportService.import_from_excel(
            db, request.file_path, request.replace_existing
        )

        return CMDBImportResponse(
            success=True,
            l2_applications_imported=result["l2_applications"]["imported"],
            l1_156_systems_imported=result["l1_156_systems"]["imported"],
            l1_87_systems_imported=result["l1_87_systems"]["imported"],
            total_rows_processed=result["total_rows"],
            duration_seconds=result["duration_seconds"],
            errors=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
