# Frontend Update Requirements for Database Schema Changes

## Overview
The database schema has been updated to better match business requirements. This document outlines all the changes that need to be made on the frontend side.

## 1. Application Model Changes

### Renamed Fields (Update all references)
| Old Field Name | New Field Name | Type | Notes |
|---|---|---|---|
| `supervision_year` | `ak_supervision_acceptance_year` | integer | AK监管验收年 |
| `transformation_target` | `overall_transformation_target` | string | 整体转型目标 |
| `current_stage` | `current_transformation_phase` | string | 当前转型阶段 |
| `overall_status` | `current_status` | string | 当前状态 |

### Removed Fields (Remove from UI)
| Field Name | Replacement Strategy |
|---|---|
| `responsible_team` | Use `dev_team` or `ops_team` |
| `responsible_person` | Use `dev_owner` or `ops_owner` |
| `progress_percentage` | Calculated from subtasks (backend provides via API) |

### New Fields (Add to forms and displays)
| Field Name | Type | Label (Chinese) | Description |
|---|---|---|---|
| `app_tier` | integer | 应用层级 | Application tier level |
| `belonging_l1_name` | string | 所属L1名称 | Parent L1 application name |
| `belonging_projects` | string | 所属项目 | Associated projects |
| `is_domain_transformation_completed` | boolean | 领域转型完成 | Domain transformation status |
| `is_dbpm_transformation_completed` | boolean | DBPM转型完成 | DBPM transformation status |
| `dev_mode` | string | 开发模式 | Development mode |
| `ops_mode` | string | 运维模式 | Operations mode |
| `dev_owner` | string | 开发负责人 | Development owner |
| `dev_team` | string | 开发团队 | Development team |
| `ops_owner` | string | 运维负责人 | Operations owner |
| `ops_team` | string | 运维团队 | Operations team |
| `belonging_kpi` | string | 所属KPI | Related KPI |
| `acceptance_status` | string | 验收状态 | Acceptance status |

## 2. SubTask Model Changes

### Critical Change: Foreign Key Reference
| Old Field | New Field | Type | Notes |
|---|---|---|---|
| `application_id` | `l2_id` | integer | Now stores the application's ID directly |

### Removed Fields (Remove from UI)
| Field Name | Notes |
|---|---|
| `module_name` | No longer tracked |
| `requirements` | Combined into `notes` |
| `technical_notes` | Renamed to `notes` |
| `test_notes` | Combined into `notes` |
| `deployment_notes` | Combined into `notes` |
| `priority` | No longer tracked |
| `estimated_hours` | No longer tracked |
| `actual_hours` | No longer tracked |
| `assigned_to` | No longer tracked |
| `reviewer` | No longer tracked |

### Renamed Fields
| Old Field | New Field | Type | Notes |
|---|---|---|---|
| `technical_notes` | `notes` | text | General notes field |

### New Fields (Add to forms and displays)
| Field Name | Type | Label (Chinese) | Description |
|---|---|---|---|
| `resource_applied` | boolean | 资源已申请 | Resource application status |
| `ops_requirement_submitted` | timestamp | 运维需求提交时间 | Ops requirement submission time |
| `ops_testing_status` | string | 运维测试状态 | Operations testing status |
| `launch_check_status` | string | 上线检查状态 | Launch check status |

## 3. API Endpoint Updates

### Application Endpoints
All existing endpoints remain the same, but the response/request schemas need updating:

```typescript
interface Application {
  id: number;
  l2_id: string;
  app_name: string;

  // Renamed fields
  ak_supervision_acceptance_year?: number;  // was: supervision_year
  overall_transformation_target?: string;   // was: transformation_target
  current_transformation_phase?: string;    // was: current_stage
  current_status: string;                   // was: overall_status

  // New fields
  app_tier?: number;
  belonging_l1_name?: string;
  belonging_projects?: string;
  is_domain_transformation_completed: boolean;
  is_dbpm_transformation_completed: boolean;
  dev_mode?: string;
  ops_mode?: string;
  dev_owner?: string;
  dev_team?: string;
  ops_owner?: string;
  ops_team?: string;
  belonging_kpi?: string;
  acceptance_status?: string;

  // Existing fields (unchanged)
  is_ak_completed: boolean;
  is_cloud_native_completed: boolean;
  planned_requirement_date?: string;
  planned_release_date?: string;
  planned_tech_online_date?: string;
  planned_biz_online_date?: string;
  actual_requirement_date?: string;
  actual_release_date?: string;
  actual_tech_online_date?: string;
  actual_biz_online_date?: string;
  is_delayed: boolean;
  delay_days: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}
```

### SubTask Endpoints
```typescript
interface SubTask {
  id: number;
  l2_id: number;  // was: application_id

  // Core fields (unchanged)
  sub_target?: string;
  version_name?: string;
  task_status: string;
  progress_percentage: number;
  is_blocked: boolean;
  block_reason?: string;

  // Date fields (unchanged)
  planned_requirement_date?: string;
  planned_release_date?: string;
  planned_tech_online_date?: string;
  planned_biz_online_date?: string;
  actual_requirement_date?: string;
  actual_release_date?: string;
  actual_tech_online_date?: string;
  actual_biz_online_date?: string;

  // Changed fields
  notes?: string;  // was: technical_notes

  // New fields
  resource_applied: boolean;
  ops_requirement_submitted?: string;  // ISO timestamp
  ops_testing_status?: string;
  launch_check_status?: string;

  // Timestamps (unchanged)
  created_at: string;
  updated_at: string;
}
```

## 4. Excel Import/Export Updates

### Application Excel Columns
The following column headers are now supported:

**English Headers:**
- `l2_id` or `application_id`
- `app_name` or `application_name`
- `ak_supervision_acceptance_year` (was: `supervision_year`)
- `overall_transformation_target` (was: `transformation_target`)
- `current_transformation_phase` (was: `current_stage`)
- `current_status` (was: `status` or `overall_status`)
- `dev_team` (was: `responsible_team`)
- `dev_owner` (was: `responsible_person`)
- All new fields as listed above

**Chinese Headers (支持中文列名):**
- `L2 ID` or `L2ID` → `l2_id`
- `应用名称` → `app_name`
- `监管年` or `验收年度` → `ak_supervision_acceptance_year`
- `转型目标` or `整体转型目标` → `overall_transformation_target`
- `当前阶段` or `当前转型阶段` → `current_transformation_phase`
- `状态` or `当前状态` → `current_status`
- `开发团队` → `dev_team`
- `运维团队` → `ops_team`
- `开发负责人` → `dev_owner`
- `运维负责人` → `ops_owner`

### SubTask Excel Columns
**English Headers:**
- `l2_id` (was: `application_l2_id`)
- `notes` (was: `technical_notes`)
- All new fields as listed above

**Chinese Headers:**
- `L2ID` or `L2 ID` → `l2_id`
- `备注` → `notes`
- `资源已申请` → `resource_applied`
- `运维需求提交时间` → `ops_requirement_submitted`
- `运维测试状态` → `ops_testing_status`
- `上线检查状态` → `launch_check_status`

## 5. Form Validation Updates

### Application Forms
- Remove validation for `responsible_team` and `responsible_person`
- Add optional fields for all new columns
- Update field names in validation rules

### SubTask Forms
- Change foreign key reference from `application_id` to `l2_id`
- Remove fields: `module_name`, `priority`, `estimated_hours`, `assigned_to`, `reviewer`
- Add new fields with appropriate validation

## 6. Display Components Updates

### Application List/Table
- Update column headers to match new field names
- Add columns for new fields (consider using expandable rows or tabs for better UX)
- Remove `progress_percentage` input field (now calculated)

### SubTask List/Table
- Remove columns for deleted fields
- Add columns for new tracking fields
- Update relationship display to use `l2_id`

## 7. Filter and Search Updates

Update all filter options to use new field names:
- `ak_supervision_acceptance_year` for year filtering
- `current_status` for status filtering
- `dev_team` and `ops_team` for team filtering
- Add filters for new boolean fields

## 8. Migration Strategy

1. **Backend Compatibility**: The backend provides compatibility properties for old field names, so the frontend can be updated gradually.

2. **Phased Rollout**:
   - Phase 1: Update data models and API interfaces
   - Phase 2: Update forms and validation
   - Phase 3: Update display components
   - Phase 4: Update Excel import/export
   - Phase 5: Remove deprecated field references

3. **Testing Checklist**:
   - [ ] Application CRUD operations
   - [ ] SubTask CRUD operations
   - [ ] Excel import with new columns
   - [ ] Excel export with new columns
   - [ ] Filters and search
   - [ ] Dashboard statistics
   - [ ] Progress calculations

## 9. API Response Handling

The backend will continue to provide calculated fields:
- `progress_percentage` - Calculated from subtasks
- `responsible_team` - Returns `dev_team` or `ops_team`
- `responsible_person` - Returns `dev_owner` or `ops_owner`

These are read-only properties and should not be sent in POST/PUT requests.

## 10. Important Notes

1. **No Prefix Addition**: The backend no longer adds prefixes to imported data. L2 IDs and app names are stored exactly as provided.

2. **SubTask Foreign Key**: SubTasks now reference applications by their database ID in the `l2_id` field, not by the L2 ID string.

3. **Backward Compatibility**: The backend provides compatibility properties for old field names, but frontend should migrate to new names.

4. **Required Fields**: Only `l2_id` is required for applications, and only `l2_id` is required for subtasks. All other fields can be null/empty.

## Contact
For any questions or issues during implementation, please refer to the backend API documentation at `/docs` endpoint.