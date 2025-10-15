"""
CMDB System Catalog Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# L2 Application Schemas
class CMDBL2ApplicationBase(BaseModel):
    config_id: str
    short_name: str
    status: Optional[str] = None
    management_level: Optional[str] = None


class CMDBL2ApplicationResponse(CMDBL2ApplicationBase):
    id: int
    english_name: Optional[str] = None
    description: Optional[str] = None
    business_supervisor_unit: Optional[str] = None
    contact_person: Optional[str] = None
    dev_unit: Optional[str] = None
    dev_contact: Optional[str] = None
    ops_unit: Optional[str] = None
    ops_contact: Optional[str] = None
    belongs_to_156l1: Optional[str] = None
    belongs_to_87l1: Optional[str] = None
    system_function: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CMDBL2ApplicationSearch(BaseModel):
    keyword: Optional[str] = Field(None, description="Search keyword for name/id")
    status: Optional[str] = Field(None, description="Filter by status")
    management_level: Optional[str] = Field(None, description="Filter by management level")
    belongs_to_156l1: Optional[str] = Field(None, description="Filter by 156L1 system")
    belongs_to_87l1: Optional[str] = Field(None, description="Filter by 87L1 system")
    limit: int = Field(100, ge=1, le=1000, description="Number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


# 156L1 System Schemas
class CMDBL1System156Base(BaseModel):
    config_id: str
    short_name: str
    management_level: Optional[str] = None


class CMDBL1System156Response(CMDBL1System156Base):
    id: int
    belongs_to_domain: Optional[str] = None
    belongs_to_layer: Optional[str] = None
    system_function: Optional[str] = None
    dev_unit: Optional[str] = None
    status: Optional[str] = None
    xinchuang_acceptance_year: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CMDBL1System156Search(BaseModel):
    keyword: Optional[str] = Field(None, description="Search keyword")
    domain: Optional[str] = Field(None, description="Filter by domain")
    layer: Optional[str] = Field(None, description="Filter by layer")
    limit: int = Field(100, ge=1, le=1000)


# 87L1 System Schemas
class CMDBL1System87Base(BaseModel):
    config_id: str
    short_name: str
    management_level: Optional[str] = None


class CMDBL1System87Response(CMDBL1System87Base):
    id: int
    description: Optional[str] = None
    status: Optional[str] = None
    deployment_architecture: Optional[str] = None
    deployment_region: Optional[str] = None
    belongs_to_domain: Optional[str] = None
    belongs_to_layer: Optional[str] = None
    is_critical_system: Optional[str] = None
    peak_tps: Optional[float] = None
    daily_business_volume: Optional[float] = None
    function_positioning: Optional[str] = None
    dev_unit: Optional[str] = None
    ops_unit: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CMDBL1System87Search(BaseModel):
    keyword: Optional[str] = Field(None, description="Search keyword")
    domain: Optional[str] = Field(None, description="Filter by domain")
    layer: Optional[str] = Field(None, description="Filter by layer")
    is_critical: Optional[str] = Field(None, description="Filter by critical system")
    limit: int = Field(100, ge=1, le=1000)


# Import Schema
class CMDBImportRequest(BaseModel):
    file_path: str = Field(..., description="Path to Excel file to import")
    replace_existing: bool = Field(False, description="Whether to replace existing data")


class CMDBImportResponse(BaseModel):
    success: bool
    l2_applications_imported: int
    l1_156_systems_imported: int
    l1_87_systems_imported: int
    total_rows_processed: int
    duration_seconds: float
    errors: Optional[List[str]] = None


# Statistics Schema
class CMDBStatistics(BaseModel):
    l2_applications_total: int
    l1_156_systems_total: int
    l1_87_systems_total: int
    l2_by_status: dict
    l2_by_management_level: dict


# L2 with L1 Info Schema
class CMDBL2WithL1Response(BaseModel):
    found: bool
    count: Optional[int] = None
    message: Optional[str] = None
    applications: Optional[List[dict]] = None
