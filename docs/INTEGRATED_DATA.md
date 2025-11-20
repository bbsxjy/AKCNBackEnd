# 跨表关联查询功能实现文档

## 功能概述

实现了通过 `l2_id` 将 CMDB 静态信息、转型项目动态信息和子任务数据关联起来的完整查询功能。

## 数据关联关系

```
CMDB静态信息（cmdb_l2_applications表）
    ↓
    config_id (VARCHAR, 如CI000088398)
    ↓ 匹配
    ↓
转型项目动态信息（applications表）
    ↓
    l2_id (VARCHAR, 如CI000088398)
    ↓
    id (INTEGER主键)
    ↓ 外键关联
    ↓
子任务详情（sub_tasks表）
    ↓
    l2_id (INTEGER外键 → applications.id)
```

### 关键点

1. **cmdb_l2_applications.config_id** (VARCHAR) = **applications.l2_id** (VARCHAR)
   - 例如：CI000088398

2. **applications.id** (INTEGER) = **sub_tasks.l2_id** (INTEGER)
   - **注意**：sub_tasks.l2_id 是外键，指向 applications.id（主键），不是 applications.l2_id！

3. **数据同步流程**：
   - CMDB中的静态配置信息（开发单位、接口人等）→ 通过平台同步 → applications表
   - 用户在平台中维护转型项目的动态进度（转型阶段、是否延期等）
   - 子任务通过外键关联到具体的转型项目应用

## 实现的功能

### 1. 跨表关联查询服务

**文件**: `app/services/cmdb_query_service.py`

#### 方法1: `get_integrated_application_data()`

获取单个应用的完整关联数据。

```python
async def get_integrated_application_data(
    db: AsyncSession,
    l2_id_or_config_id: str
) -> Dict[str, Any]
```

**返回数据结构**:
```json
{
    "l2_id": "CI000088398",
    "cmdb_info": {
        "config_id": "CI000088398",
        "short_name": "应用名称",
        "management_level": "管理级别",
        "dev_unit": "开发单位",
        "belongs_to_156l1": "所属156L1系统",
        "belongs_to_87l1": "所属87L1系统",
        ...
    },
    "transformation_info": {
        "id": 123,
        "l2_id": "CI000088398",
        "app_name": "应用名称",
        "current_status": "当前状态",
        "is_ak_completed": false,
        "is_delayed": true,
        "delay_days": 15,
        ...
    },
    "subtasks": [
        {
            "id": 456,
            "sub_target": "子任务目标",
            "task_status": "任务状态",
            "progress_percentage": 80,
            "is_blocked": false,
            ...
        }
    ],
    "l1_systems": {
        "l1_156": {...},
        "l1_87": {...}
    },
    "data_sources": ["cmdb", "transformation", "subtasks"],
    "integration_status": "完整",
    "relationships": {
        "has_cmdb_record": true,
        "has_transformation_project": true,
        "has_subtasks": true,
        "subtask_count": 3
    }
}
```

#### 方法2: `batch_get_integrated_data()`

批量获取多个应用的完整关联数据（用于Excel填充和数据分析）。

```python
async def batch_get_integrated_data(
    db: AsyncSession,
    l2_ids: List[str],
    include_subtasks: bool = True
) -> List[Dict[str, Any]]
```

### 2. MCP工具注册

**文件**: `app/services/mcp_service.py`

添加了新的MCP工具：`get_integrated_data`

```python
{
    "name": "get_integrated_data",
    "description": "获取应用的完整关联数据（CMDB静态信息 + 转型项目动态信息 + 子任务）",
    "category": "data_integration",
    "parameters": {
        "l2_id": "L2业务ID/配置项ID（如CI000088398）",
        "include_subtasks": "是否包含子任务详情（默认true）"
    }
}
```

### 3. Handler实现

**文件**: `app/mcp/handlers.py`

在 `handle_cmdb_operation()` 函数中添加了对 `get_integrated_data` 工具的处理：

```python
elif tool_name == "get_integrated_data":
    l2_id = arguments.get("l2_id")
    include_subtasks = arguments.get("include_subtasks", True)

    integrated_data = await CMDBQueryService.get_integrated_application_data(
        db, l2_id
    )

    return {"success": True, "data": integrated_data}
```

### 4. API路由注册

**文件**: `app/api/v1/endpoints/mcp.py`

将 `get_integrated_data` 工具添加到CMDB工具列表中：

```python
elif tool_name in ["cmdb_search_l2", ..., "get_integrated_data"]:
    result = await handlers.handle_cmdb_operation(tool_name, arguments)
```

### 5. AI提示词增强

**文件**: `app/services/mcp_service.py`

在AI提示词中添加了：

1. **完整的数据关联关系说明**（第937-970行）
   - 三个数据源的说明
   - 关联链条图示
   - 数据同步流程
   - 使用场景指导

2. **新工具的描述和使用指南**（第934行）

3. **示例12**（第1117-1118行）：展示如何使用 `get_integrated_data` 工具

## 使用示例

### 通过MCP API调用

```bash
curl -X POST "http://localhost:8000/api/v1/mcp/execute" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_integrated_data",
    "arguments": {
      "l2_id": "CI000088398",
      "include_subtasks": true
    }
  }'
```

### 通过自然语言查询

```bash
curl -X POST "http://localhost:8000/api/v1/mcp/query/applications" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询CI000088398的完整信息，包括CMDB配置、转型进度和子任务"
  }'
```

AI会自动识别并调用 `get_integrated_data` 工具。

### 在代码中直接调用

```python
from app.services.cmdb_query_service import CMDBQueryService

async def example():
    async with db_session() as db:
        # 单个查询
        result = await CMDBQueryService.get_integrated_application_data(
            db, "CI000088398"
        )

        # 批量查询
        results = await CMDBQueryService.batch_get_integrated_data(
            db,
            ["CI000088398", "CI000088399"],
            include_subtasks=False
        )
```

## 测试

运行测试脚本：

```bash
python test_integrated_data.py
```

**注意**: 在运行测试前，请修改 `test_integrated_data.py` 中的 L2 ID为实际存在的数据。

## 应用场景

### 1. Excel模板填充

当用户上传Excel模板需要填充数据时，可以使用 `get_integrated_data` 一次性获取：
- CMDB的静态配置信息（开发单位、接口人等）
- 转型项目的动态进度（当前状态、是否延期等）
- 所有子任务的详细信息

### 2. 智能数据分析

AI助手可以理解这些关联关系，提供更智能的数据分析：
- "分析CI000088398的转型进度，考虑其在CMDB中的管理级别"
- "查看哪些高管理级别的应用转型延期了"
- "列出所属核心银行系统的所有转型项目及其子任务"

### 3. 完整信息展示

前端可以调用这个API一次性获取应用的所有相关信息，减少多次请求：
- 左侧：CMDB静态信息
- 中间：转型项目进度
- 右侧：子任务列表
- 底部：关联的L1系统信息

## 性能考虑

1. **批量查询优化**: 使用 `batch_get_integrated_data()` 可选择不包含子任务详情，提高性能
2. **缓存机制**: 可以考虑对CMDB静态信息添加缓存
3. **分页支持**: 对于大量数据，可以添加分页参数

## 后续扩展

1. **添加缓存层**: 对CMDB静态信息进行缓存
2. **支持更多关联**: 可以关联更多表（如audit_logs、task_assignments等）
3. **导出功能**: 将完整关联数据导出为Excel或PDF报告
4. **关联分析**: 基于这些关联数据进行更深入的分析和报表

## 文件清单

以下文件已修改或创建：

1. **app/services/cmdb_query_service.py** - 添加了两个新方法
2. **app/services/mcp_service.py** - 添加工具定义和AI提示词增强
3. **app/mcp/handlers.py** - 添加工具处理逻辑
4. **app/api/v1/endpoints/mcp.py** - 注册工具到API路由
5. **test_integrated_data.py** - 测试脚本（新建）
6. **docs/INTEGRATED_DATA.md** - 本文档（新建）

---

**实现完成时间**: 2025-01-20
**版本**: 1.0.0
