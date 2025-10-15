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

### 列字段

| 列名 | 说明 | 数据来源 |
|------|------|----------|
| 序 | 行号，从1开始 | 自动生成 |
| L2应用编号 | 应用的L2标识 | `application.l2_id` |
| L2应用名称（全称） | 应用名称 | `application.app_name` |
| 计划改造完成 | 计划验收年份 | `application.ak_supervision_acceptance_year` |
| 实施进度 | 百分比 | `application.progress_percentage` |
| 详细进展及进展 | 子任务状态汇总 | 从subtasks汇总 |
| 当前实施阶段 | 当前状态 | `application.current_status` |
| 计划需求完成 | 计划需求完成日期 | `application.planned_requirement_date` |
| 实际需求完成 | 实际需求完成日期 | `application.actual_requirement_date` |
| 计划发版完成 | 计划发版完成日期 | `application.planned_release_date` |
| 实际发版完成 | 实际发版完成日期 | `application.actual_release_date` |
| 计划技术上线 | 计划技术上线日期 | `application.planned_tech_online_date` |
| 实际技术上线 | 实际技术上线日期 | `application.actual_tech_online_date` |
| 计划业务上线 | 计划业务上线日期 | `application.planned_biz_online_date` |
| 实际业务上线 | 实际业务上线日期 | `application.actual_biz_online_date` |
| 备注 | 备注信息 | `application.notes` |

## Sample2格式说明（详细追踪表）

### 文件结构
- **Sheet 1**: "Sheet1" - 包含所有应用的详细追踪数据

### 列字段

| 列名 | 说明 | 数据来源 |
|------|------|----------|
| 归属单位 | 所属部门/团队 | `application.dev_team` |
| 年 | 年份 | `application.ak_supervision_acceptance_year` |
| AK标签 | AK/云原生 | `application.overall_transformation_target` |
| 应用ID | 应用ID | `application.l2_id` |
| 应用名称 | 应用名称 | `application.app_name` |
| 所属L1 | 所属L1 | `application.belonging_l1_name` |
| 负责单位 | 负责团队 | `application.dev_team` |
| 负责单位联系人 | 负责人 | `application.dev_owner` |
| 开发单位 | 开发团队 | `application.dev_team` |
| 开发单位联系人 | 开发负责人 | `application.dev_owner` |
| 开发模式 | 开发模式 | `application.dev_mode` |
| 涉及项目 | 所属项目 | `application.belonging_projects` |
| 是否云原生 | 是/否 | 基于`overall_transformation_target`计算 |
| 前期实施计划概况/进度备注 | 子任务状态汇总 | 从subtasks汇总 |
| 3月实施状态 | 3月实施状态 | 从subtasks按月汇总 |
| 3月实施阶段 | 3月实施阶段 | 从subtasks按月汇总 |
| 3月完成日期 | 3月完成日期 | 从subtasks按月汇总 |
| 4月实施状态 | 4月实施状态 | 从subtasks按月汇总 |
| 4月实施阶段 | 4月实施阶段 | 从subtasks按月汇总 |
| 4月完成日期 | 4月完成日期 | 从subtasks按月汇总 |
| 5月实施状态 | 5月实施状态 | 从subtasks按月汇总 |
| 5月实施阶段 | 5月实施阶段 | 从subtasks按月汇总 |
| 5月完成日期 | 5月完成日期 | 从subtasks按月汇总 |
| 6月实施状态 | 6月实施状态 | 从subtasks按月汇总 |
| 6月实施阶段 | 6月实施阶段 | 从subtasks按月汇总 |
| 6月完成日期 | 6月完成日期 | 从subtasks按月汇总 |
| 计划改造完成 | 计划改造完成年份 | `application.ak_supervision_acceptance_year` |

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
