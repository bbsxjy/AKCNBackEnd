# 双周报Excel导出API文档

## API端点

**POST** `/api/v1/reports/export/bi-weekly`

## 功能说明

该API用于导出双周报数据为Excel文件，支持两种模板格式：
- **sample1**: 双追踪表格式（两个Sheet：AK和云原生）
- **sample2**: 详细追踪表格式（单个Sheet，包含月度跟踪）

## 权限要求

需要以下任一角色：
- ADMIN
- MANAGER
- EDITOR

## 请求格式

### Headers
```
Content-Type: application/json
Authorization: Bearer <your-jwt-token>
```

### Request Body

```json
{
  "template_type": "sample1",  // 或 "sample2"
  "report_data": {
    "report_date": "2025年10月15日",
    "total_applications": 258,
    "status_stats": [
      {
        "label": "需求阶段",
        "count": 0,
        "type": "requirement"
      },
      {
        "label": "研发阶段",
        "count": 83,
        "type": "development"
      },
      {
        "label": "已完成",
        "count": 69,
        "type": "completed"
      },
      {
        "label": "上线阶段",
        "count": 23,
        "type": "online"
      },
      {
        "label": "业务下线",
        "count": 6,
        "type": "offline"
      },
      {
        "label": "未启动",
        "count": 63,
        "type": "not-started"
      },
      {
        "label": "阻塞",
        "count": 2,
        "type": "blocked",
        "detail": "（技术原因-Python版本不兼容）"
      }
    ],
    "key_indicators": [
      {
        "name": "2025年AK验收目标（仅含云原生）",
        "percentage": 31,
        "completed": 19,
        "total": 61
      },
      {
        "name": "2025年技术条线OKR",
        "percentage": 91,
        "completed": 32,
        "total": 35
      },
      {
        "name": "2024&2025年项目目标进度",
        "percentage": 61,
        "completed": 69,
        "total": 114
      }
    ],
    "delayed_apps": [
      {
        "id": "xxx",
        "appName": "统一密钥管理应用",
        "team": "未填写",
        "plannedDate": "2025-05-31",
        "delayMonths": 1,
        "delayReason": "未填写",
        "expectedDate": "2025-06-30"
      }
    ],
    "potential_risk_apps": []
  },
  "export_format": "excel"
}
```

## 响应格式

### 成功响应

- **Status Code**: 200 OK
- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Headers**:
  - `Content-Disposition: attachment; filename=bi_weekly_report_sample1_20251015_120000.xlsx`
  - `Access-Control-Expose-Headers: Content-Disposition`

响应体为Excel文件的二进制数据（Blob）。

### 错误响应

#### 400 Bad Request
```json
{
  "detail": "Invalid template_type: xxx. Must be 'sample1' or 'sample2'."
}
```

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to export bi-weekly report: <error message>"
}
```

## Sample1格式说明（双追踪表）

### 文件结构
- **Sheet 1**: "AK" - 包含AK改造的应用数据
- **Sheet 2**: "云原生" - 包含云原生改造的应用数据
- **总列数**: 28列（部分列为空列，用于格式占位）

### 列字段

| 列序号 | 列名 | 说明 | 数据来源 | 状态映射 |
|--------|------|------|----------|----------|
| A (1) | 序号 | 行号，从1开始 | 自动生成 | - |
| B (2) | L2应用编号 | 应用的L2标识 | `application.l2_id` | - |
| C (3) | L2应用中文名称(收集) | 应用名称 | `application.app_name` | - |
| D (4) | 计划调整情况 | 计划验收年份 | `application.ak_supervision_acceptance_year` + '年' | - |
| E (5) | (空列) | - | - | - |
| F (6) | (空列) | - | - | - |
| G (7) | 实施情况 | 里程碑节点状态 | `application.current_status` | **使用状态映射** (见下方) |
| H (8) | 详细工作安排及进展 | 详细进展阶段 | `application.current_status` | **使用状态映射** (见下方) |
| I-AA (9-27) | (空列) | 预留列 | - | - |
| AB (28) | 备注\n（难点或问题） | 备注信息 | `application.notes` | - |

### Sample1状态映射规则

基于 `mappings.xlsx` 的映射关系：

**G列（实施情况）映射:**
- `未开始` → `AK改造：未启动` / `云原生：未启动`
- `需求进行中` → `AK改造：研发需求提交阶段` / `云原生：研发需求提交阶段`
- `研发进行中` → `AK改造：研发测试阶段` / `云原生：研发测试阶段`
- `部署进行中` → `AK改造：技术上线阶段` / `云原生：技术上线阶段`
- `业务上线中` → `AK改造：技术上线阶段` / `云原生：技术上线阶段`
- `全部完成` → `AK改造：完成业务上线` / `云原生：完成业务上线`
- `中止` → `计划下线：未启动` / `计划下线：未启动`

**H列（详细工作安排及进展）映射:**
- `未开始` → `AK改造：未启动` / `云原生：未启动`
- `需求进行中` → `AK改造：已完成采购` / `云原生：已完成采购`
- `研发进行中` → `AK改造：已提交研发需求` / `云原生：已提交研发需求`
- `部署进行中` → `AK改造：已完成研发测试` / `云原生：已完成研发测试`
- `业务上线中` → `AK改造：已技术上线` / `云原生：已技术上线`
- `全部完成` → `AK改造：已业务上线` / `云原生：已业务上线`
- `中止` → `计划下线：确认应用要下线` / `计划下线：确认应用要下线`

## Sample2格式说明（详细追踪表）

### 文件结构
- **Sheet 1**: "Sheet1" - 包含所有应用的详细追踪数据
- **总列数**: 75列（包含大量月度跟踪预留列）

### 列字段

| 列序号 | 列名 | 说明 | 数据来源 | 状态映射 |
|--------|------|------|----------|----------|
| A (1) | 编号位 | 编号位置 | (空) | - |
| B (2) | 序号 | 行号，从1开始 | 自动生成 | - |
| C (3) | AK类别 | AK/云原生 | `application.overall_transformation_target` | - |
| D (4) | 信创类别 | 信创分类 | (空) | - |
| E (5) | 应用ID | 应用的L2标识 | `application.l2_id` | - |
| F (6) | 应用名称 | 应用名称 | `application.app_name` | - |
| G (7) | 是否为监管报送 | 是否监管 | (空) | - |
| H (8) | 所属L1 | 所属L1 | `application.belonging_l1_name` | - |
| I (9) | 主管单位 | 主管团队 | `application.dev_team` | - |
| J (10) | 主管单位联系人 | 主管负责人 | `application.dev_owner` | - |
| K (11) | 开发单位 | 开发团队 | `application.dev_team` | - |
| L (12) | 开发单位联系人 | 开发负责人 | `application.dev_owner` | - |
| M (13) | 开发模式 | 开发模式 | `application.dev_mode` | - |
| N (14) | 涉及项目 | 所属项目 | `application.belonging_projects` | - |
| O (15) | 是否云原生 | 是/否 | 基于`overall_transformation_target`计算 | - |
| P (16) | 跟进人 | 跟进负责人 | (空) | - |
| Q (17) | 最新计划情况 | 计划状态 | `application.current_status` | **使用状态映射 (BF)** |
| R (18) | 前期实施计划（状态/里程碑） | 实施里程碑 | `application.current_status` | **使用状态映射 (BG)** |
| S (19) | 月度进展跟踪 | 月度跟踪 | 同Q列 | **使用状态映射 (BF)** |
| T-BW (20-75) | (月度详细跟踪列) | 预留月度跟踪数据 | (空) | - |

### Sample2状态映射规则

基于 `mappings.xlsx` 的映射关系：

**Q列、S列（最新计划情况、月度进展跟踪）- BF映射:**
- `未开始` → `AK改造`
- `需求进行中` → `AK改造`
- `研发进行中` → `AK改造`
- `部署进行中` → `AK改造`
- `业务上线中` → `AK改造`
- `全部完成` → `AK改造`
- `中止` → `计划下线`

**R列（前期实施计划（状态/里程碑））- BG映射:**
- `未开始` → `未启动`
- `需求进行中` → `研发需求提交阶段`
- `研发进行中` → `研发测试阶段`
- `部署进行中` → `技术上线阶段`
- `业务上线中` → `业务上线阶段`
- `全部完成` → `已完成`
- `中止` → `未启动`

## 前端调用示例

### JavaScript/TypeScript

```typescript
import axios from 'axios';

// 导出sample1格式
async function exportBiWeeklySample1(reportData: any) {
  try {
    const response = await axios.post(
      '/api/v1/reports/export/bi-weekly',
      {
        template_type: 'sample1',
        report_data: reportData,
        export_format: 'excel'
      },
      {
        responseType: 'blob',
        headers: {
          'Authorization': `Bearer ${yourAuthToken}`,
          'Content-Type': 'application/json'
        }
      }
    );

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition'];
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1]
      : 'bi_weekly_report.xlsx';

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    return { success: true };
  } catch (error) {
    console.error('Failed to export bi-weekly report:', error);
    return { success: false, error };
  }
}

// 导出sample2格式
async function exportBiWeeklySample2(reportData: any) {
  // 类似上面的实现，只需将 template_type 改为 'sample2'
}
```

### Python

```python
import requests

def export_bi_weekly_report(template_type: str, report_data: dict, token: str):
    """Export bi-weekly report"""
    url = "http://localhost:8000/api/v1/reports/export/bi-weekly"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "template_type": template_type,
        "report_data": report_data,
        "export_format": "excel"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        # 保存Excel文件
        filename = f"bi_weekly_report_{template_type}.xlsx"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Report saved to {filename}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

# 使用示例
report_data = {
    "report_date": "2025年10月15日",
    "total_applications": 258,
    "status_stats": [...],
    "key_indicators": [...],
    "delayed_apps": [],
    "potential_risk_apps": []
}

export_bi_weekly_report("sample1", report_data, "your-auth-token")
```

## 注意事项

1. **日期格式**: Excel中的日期使用标准格式（YYYY-MM-DD）
2. **中文列名**: 所有列名都使用中文，与示例文件保持一致
3. **Sheet名称**:
   - Sample1: "AK" 和 "云原生"
   - Sample2: "Sheet1"
4. **数据完整性**: 确保所有必填字段都有值，空值显示为空字符串
5. **性能优化**: 对于大量数据（>1000条应用），导出可能需要几秒钟时间
6. **错误处理**: 前端应捕获错误并向用户显示清晰的错误信息

## 实现细节

### 数据汇总

**子任务进度汇总** (`_aggregate_subtask_progress`):
- 统计每个应用下的子任务状态分布
- 格式：`状态1:X个; 状态2:Y个`
- 示例：`研发进行中:3个; 已完成:2个; 未开始:1个`

**月度进度计算** (`_calculate_monthly_progress`):
- 根据子任务的`actual_biz_online_date`确定完成月份
- 为3月、4月、5月、6月生成进度数据
- 每个月包含3列：实施状态、实施阶段、完成日期

### Excel样式

- 标题行：蓝色背景（#4F81BD），白色粗体文字
- 自动调整列宽（最小8，最大50）
- 所有单元格添加边框
- 日期格式：YYYY-MM-DD

## 测试建议

1. **测试sample1格式导出**
   - 验证两个Sheet是否正确生成
   - 验证AK和云原生应用是否正确分组
   - 验证列名和数据映射是否正确

2. **测试sample2格式导出**
   - 验证单个Sheet包含所有应用
   - 验证月度进展列是否正确生成
   - 验证子任务数据汇总是否正确

3. **测试错误场景**
   - 无效的template_type
   - 缺少认证token
   - 权限不足

## 相关文件

- `app/schemas/report.py` - Pydantic schemas定义
- `app/services/excel_service.py` - Excel生成服务
- `app/api/v1/endpoints/reports.py` - API endpoint定义

## 更新日志

- **2025-10-15**: 初始版本，实现sample1和sample2格式导出
