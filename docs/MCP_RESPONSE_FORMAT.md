# MCP工具返回格式标准化文档

## 概述

本文档说明了MCP工具返回数据格式的标准化改进，旨在让前端能够更智能地渲染不同类型的数据。

## 改进方案

采用**方案2（添加metadata）+ 方案3部分（规范化响应结构）**的混合方案：

1. 创建标准化的响应工具函数
2. 在所有MCP工具返回中添加metadata字段
3. 保持向后兼容性（仍包含success、data等字段）

## 标准化响应格式

### 基础格式

所有成功的响应都遵循以下格式：

```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "renderType": "application_list",
    "title": "查询到 10 个转型应用",
    "count": 10,
    "primaryKey": "l2_id"
  }
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": "错误信息"
}
```

## 支持的渲染类型 (renderType)

### 1. 列表类型

#### application_list - 转型应用列表
```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "renderType": "application_list",
    "title": "查询到 10 个转型应用",
    "count": 10,
    "total": 100,
    "primaryKey": "l2_id"
  },
  "count": 10,
  "total": 100
}
```

**适用工具**: `app_list`

**前端渲染建议**:
- 使用专门的应用列表卡片组件
- 高亮显示状态字段（current_status）
- 显示进度条
- 支持按状态筛选

#### subtask_list - 子任务列表
```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "renderType": "subtask_list",
    "title": "查询到 15 个子任务",
    "count": 15,
    "primaryKey": "id"
  }
}
```

**适用工具**: `task_list`

**前端渲染建议**:
- 使用任务列表组件
- 显示任务状态标签
- 支持进度跟踪

#### cmdb_l2_list - CMDB L2应用列表
```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "renderType": "cmdb_l2_list",
    "title": "查询到 20 个CMDB应用",
    "count": 20,
    "primaryKey": "config_id"
  }
}
```

**适用工具**: `cmdb_search_l2`

#### cmdb_l1_list - CMDB L1系统列表
```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "renderType": "cmdb_l1_list",
    "title": "查询到 8 个156L1系统",
    "count": 8,
    "primaryKey": "config_id"
  }
}
```

**适用工具**: `cmdb_search_156l1`, `cmdb_search_87l1`

### 2. 详情类型

#### application_detail - 应用详情
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "renderType": "application_detail",
    "title": "CI000088398 - 应用详情"
  }
}
```

**适用工具**: `app_get`

**前端渲染建议**:
- 使用详情页布局
- 分组显示不同类别的字段
- 突出显示关键指标

#### integrated_detail - 完整关联数据
```json
{
  "success": true,
  "data": {
    "l2_id": "CI000088398",
    "cmdb_info": { ... },
    "transformation_info": { ... },
    "l1_systems": { ... },
    "subtasks": [...],
    "relationships": { ... }
  },
  "metadata": {
    "renderType": "integrated_detail",
    "title": "CI000088398 - 完整关联数据",
    "hasSubtasks": true
  }
}
```

**适用工具**: `get_integrated_data`

**前端渲染建议**:
- 使用多标签页布局
- Tab 1: CMDB静态信息
- Tab 2: 转型项目动态信息
- Tab 3: L1系统关系
- Tab 4: 子任务列表
- 显示数据关联关系图

### 3. 统计类型

#### statistics - 统计分析结果
```json
{
  "success": true,
  "data": {
    "total_applications": 100,
    "completed_count": 45,
    "in_progress_count": 30,
    "delayed_count": 15,
    "completion_rate": 45.0
  },
  "metadata": {
    "renderType": "statistics",
    "title": "转型项目汇总统计"
  }
}
```

**适用工具**: `dashboard_stats`, `calc_delays`, `cmdb_get_stats`

**前端渲染建议**:
- 使用仪表盘卡片组件
- 显示关键指标（大数字）
- 使用图表可视化（饼图、柱状图）
- 突出显示统计字段（紫色背景）

#### progress_trend - 进度趋势
```json
{
  "success": true,
  "data": {
    "trend_data": [
      { "date": "2025-01", "completed": 10, "in_progress": 20 },
      { "date": "2025-02", "completed": 15, "in_progress": 18 }
    ]
  },
  "metadata": {
    "renderType": "progress_trend",
    "title": "进度趋势分析"
  }
}
```

**适用工具**: `dashboard_stats` (stat_type=progress_trend)

**前端渲染建议**:
- 使用折线图或面积图
- 显示时间轴
- 支持时间范围筛选

### 4. SQL查询结果

#### sql_result - SQL查询结果
```json
{
  "success": true,
  "data": {
    "columns": ["l2_id", "app_name", "current_status"],
    "rows": [
      ["CI001", "应用A", "进行中"],
      ["CI002", "应用B", "已完成"]
    ],
    "row_count": 2
  },
  "metadata": {
    "renderType": "sql_result",
    "title": "SQL查询结果 (2行)",
    "columns": ["l2_id", "app_name", "current_status"],
    "rowCount": 2
  }
}
```

**适用工具**: `db_query`

**前端渲染建议**:
- 使用表格组件
- 支持列排序
- 支持导出功能

### 5. 操作结果类型

#### operation_result - 操作结果
```json
{
  "success": true,
  "data": {
    "updated_count": 5
  },
  "metadata": {
    "renderType": "operation_result",
    "title": "批量更新结果"
  },
  "updated_count": 5,
  "message": "Updated 5 subtasks successfully"
}
```

**适用工具**: `task_batch_update`, `calc_progress`, `audit_rollback`

**前端渲染建议**:
- 显示成功消息
- 显示影响的记录数
- 提供返回或继续操作按钮

### 6. 其他特殊类型

#### cmdb_l1_to_l2_mapping - L1到L2映射
```json
{
  "success": true,
  "data": {
    "l1_system_name": "核心银行系统",
    "l1_type": "156",
    "applications": [...]
  },
  "metadata": {
    "renderType": "cmdb_l1_to_l2_mapping",
    "title": "核心银行系统 关联的L2应用 (10个)",
    "count": 10
  }
}
```

#### audit_log_list - 审计日志列表
```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "renderType": "audit_log_list",
    "title": "审计日志 (50条)",
    "count": 50
  }
}
```

#### schema_detail / schema_list - 数据库架构
```json
{
  "success": true,
  "data": {
    "table": "applications",
    "columns": [...],
    "indexes": [...],
    "foreign_keys": [...]
  },
  "metadata": {
    "renderType": "schema_detail",
    "title": "表结构: applications"
  }
}
```

## 使用工具函数

后端提供了标准化的工具函数（在 `app/mcp/response_utils.py` 中）：

### 创建成功响应

```python
from app.mcp.response_utils import (
    application_list_response,
    application_detail_response,
    subtask_list_response,
    cmdb_l2_list_response,
    create_success_response,
    create_statistics_response
)

# 应用列表
apps = [...]
return application_list_response(apps, total=100)

# 应用详情
app = {...}
return application_detail_response(app)

# 统计数据
stats = {...}
return create_statistics_response(stats, title="延期项目统计")

# 自定义响应
return create_success_response(
    data={...},
    metadata={
        "renderType": "custom_type",
        "title": "自定义标题"
    }
)
```

### 创建错误响应

```python
from app.mcp.response_utils import create_error_response

return create_error_response("错误信息")
```

## 前端智能检测

如果后端没有提供metadata，前端可以使用 `detect_render_type()` 函数自动检测数据类型：

```javascript
// 前端示例代码
function detectRenderType(data) {
  if (!data) return { renderType: "empty" };

  // 检测应用列表
  if (Array.isArray(data) && data.length > 0) {
    const firstItem = data[0];

    // 转型应用列表
    if (firstItem.l2_id && firstItem.app_name && firstItem.current_status) {
      return {
        renderType: "application_list",
        title: `查询到 ${data.length} 个转型应用`,
        count: data.length
      };
    }

    // CMDB L2应用列表
    if (firstItem.config_id && firstItem.short_name && firstItem.management_level) {
      return {
        renderType: "cmdb_l2_list",
        title: `查询到 ${data.length} 个CMDB应用`,
        count: data.length
      };
    }

    // 子任务列表
    if (firstItem.sub_target && firstItem.task_status) {
      return {
        renderType: "subtask_list",
        title: `查询到 ${data.length} 个子任务`,
        count: data.length
      };
    }

    // 统计数据
    const keys = Object.keys(firstItem);
    const statKeywords = ['count', 'total', 'avg', 'sum', 'percentage'];
    if (keys.some(k => statKeywords.some(sk => k.toLowerCase().includes(sk)))) {
      return {
        renderType: "statistics",
        title: "统计分析结果"
      };
    }
  }

  // 检测详情对象
  if (typeof data === 'object' && !Array.isArray(data)) {
    // 完整关联数据
    if (data.cmdb_info && data.transformation_info) {
      return {
        renderType: "integrated_detail",
        title: `${data.l2_id || 'Unknown'} - 完整关联数据`
      };
    }

    // 应用详情
    if (data.l2_id && data.current_status && data.current_transformation_phase) {
      return {
        renderType: "application_detail",
        title: `${data.l2_id} - 应用详情`
      };
    }
  }

  return { renderType: "unknown" };
}

// 使用示例
function renderMCPResponse(response) {
  // 优先使用后端提供的metadata
  const metadata = response.metadata || detectRenderType(response.data);

  // 根据renderType选择渲染组件
  switch (metadata.renderType) {
    case "application_list":
      return <ApplicationListCard data={response.data} metadata={metadata} />;
    case "application_detail":
      return <ApplicationDetailView data={response.data} metadata={metadata} />;
    case "statistics":
      return <StatisticsCard data={response.data} metadata={metadata} />;
    case "sql_result":
      return <SQLResultTable data={response.data} metadata={metadata} />;
    default:
      return <GenericDataView data={response.data} metadata={metadata} />;
  }
}
```

## 字段命名规范

为了让前端更好地识别和渲染数据，建议遵循以下命名规范：

### 统计类字段（会被紫色高亮）
- `xxx_count` - 计数
- `xxx_total` - 总计
- `xxx_avg` - 平均值
- `xxx_sum` - 总和
- `xxx_percentage` - 百分比
- `xxx_rate` - 比率

### 日期类字段
- `planned_xxx_date` - 计划日期
- `actual_xxx_date` - 实际日期
- `created_at` - 创建时间
- `updated_at` - 更新时间

### 状态类字段
- `xxx_status` - 状态
- `is_xxx` - 布尔值
- `current_xxx` - 当前状态

### 主键字段
- `id` - 数据库主键
- `l2_id` - L2业务ID
- `config_id` - 配置项ID

## 兼容性说明

### 向后兼容
所有更新保持向后兼容：
- 仍然包含 `success`, `data`, `count` 等原有字段
- 只是新增了 `metadata` 字段
- 旧的前端代码仍然可以正常工作

### 逐步迁移
前端可以逐步迁移到新的渲染方式：
1. 首先使用 metadata 进行智能渲染
2. 逐步替换旧的硬编码渲染逻辑
3. 最终实现完全基于 metadata 的动态渲染

## 完整示例

### 后端示例
```python
# app/mcp/handlers.py

from app.mcp.response_utils import application_list_response

async def handle_application_operation(tool_name: str, arguments: Dict):
    if tool_name == "app_list":
        apps, total = await app_service.list_applications(db, limit=100)
        return application_list_response(apps, total=total)
```

### 前端示例
```javascript
// 调用MCP工具
const response = await fetch('/api/v1/mcp/execute', {
  method: 'POST',
  body: JSON.stringify({
    tool_name: 'app_list',
    arguments: { status: 'IN_PROGRESS' }
  })
});

const result = await response.json();

// 智能渲染
if (result.success) {
  const metadata = result.metadata;
  console.log(metadata.renderType);  // "application_list"
  console.log(metadata.title);       // "查询到 10 个转型应用"
  console.log(metadata.count);       // 10

  // 根据renderType选择合适的渲染组件
  renderApplicationList(result.data, metadata);
}
```

## 总结

这次优化带来的好处：

1. **前端智能渲染**：根据 metadata 自动选择合适的渲染组件
2. **类型安全**：明确的数据类型和结构
3. **更好的用户体验**：针对不同数据类型定制化的展示方式
4. **易于扩展**：新增渲染类型只需添加对应的 metadata
5. **向后兼容**：不影响现有功能

## 更新记录

- **2025-01-21**: 完成所有MCP工具的metadata标准化改造
  - 新增 `app/mcp/response_utils.py` 工具模块
  - 更新所有handler函数以使用标准化响应格式
  - 支持15+种不同的renderType
