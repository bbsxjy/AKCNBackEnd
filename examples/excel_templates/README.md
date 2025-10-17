# Excel Template Examples

This directory contains example Excel templates for the AI-powered template filling feature.

## Available Templates

### 1. template_progress_report.xlsx (项目进度报表)
**Purpose**: Generate a comprehensive project progress report

**Template Structure**:
- **Title**: "AK/云原生转型项目进度报表" (with blue background)
- **Timestamp**: Auto-generated date/time
- **Columns**: L2 ID, 应用名称, 转型目标, 当前状态, 进度%, 开发团队, 负责人, 备注

**Use Case**: Monthly or weekly progress reporting for all transformation projects

**Example API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/excel/fill-template?limit=1000" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@template_progress_report.xlsx" \
     --output filled_progress_report.xlsx
```

**Expected Output**: Excel file with all applications filled in, preserving the blue header styling

---

### 2. template_delayed_projects.xlsx (延期项目分析)
**Purpose**: Analyze and track delayed projects

**Template Structure**:
- **Title**: "延期项目分析报表" (with red background for attention)
- **Columns**: 应用ID, 应用名称, 负责团队, 计划上线日期, 实际上线日期, 延期天数, 当前进度, 负责人, 延期原因

**Use Case**: Identify and analyze projects that are behind schedule

**Example API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/excel/fill-template?context=只显示延期项目" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@template_delayed_projects.xlsx" \
     --output delayed_analysis.xlsx
```

**Expected Output**: Excel file with only delayed projects, automatically filtered by AI based on context

---

### 3. template_team_statistics.xlsx (团队统计)
**Purpose**: Compare team performance and statistics

**Template Structure**:
- **Title**: "团队转型项目统计表" (with green background)
- **Columns**: 团队名称, 项目总数, 已完成, 进行中, 未开始, 平均进度, 延期项目数

**Use Case**: Department-level performance comparison and analysis

**Example API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/excel/fill-template?context=按团队统计项目情况" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@template_team_statistics.xlsx" \
     --output team_stats.xlsx
```

**Expected Output**: Excel file with aggregated statistics by team (may trigger AI to generate GROUP BY query)

---

### 4. template_simple_list.xlsx (简单应用列表)
**Purpose**: Basic application listing without heavy formatting

**Template Structure**:
- **Columns**: L2 ID, 应用名称, 状态, 进度, 团队

**Use Case**: Quick export for simple data requirements

**Example API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/excel/fill-template?limit=500" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@template_simple_list.xlsx" \
     --output simple_list.xlsx
```

**Expected Output**: Clean, simple Excel file with application data

---

## How It Works

1. **Upload Template**: Send the Excel template file to `/api/v1/excel/fill-template`
2. **AI Analysis**: The system analyzes column headers to understand what data you need
3. **Data Query**: Automatically queries the appropriate database tables
4. **Fill & Format**: Populates the template while preserving all formatting
5. **Download**: Returns the filled Excel file

## API Parameters

- `file` (required): The Excel template file
- `context` (optional): Additional text to help AI understand your intent
  - Example: "只显示2024年的项目"
  - Example: "延期超过30天的应用"
  - Example: "研发一部的项目进度"
- `limit` (optional): Maximum number of rows to fill (default: 1000, max: 10000)

## Creating Custom Templates

You can create your own templates following these guidelines:

### Template Requirements
1. Must be a valid Excel file (.xlsx)
2. Should have clear column headers (in row 1-10)
3. Can include:
   - Title rows with merged cells
   - Colored backgrounds
   - Custom fonts and borders
   - Column width settings
   - Cell alignment

### Supported Column Names
The AI recognizes common column headers:
- **Application IDs**: "L2 ID", "应用ID", "ID"
- **Names**: "应用名称", "名称", "app_name"
- **Progress**: "进度", "进度%", "progress"
- **Status**: "状态", "current_status"
- **Team**: "团队", "部门", "dev_team"
- **Owner**: "负责人", "owner"
- **Dates**: "计划日期", "实际日期", "上线日期"
- **Delay**: "延期天数", "delay_days"

### Best Practices
1. Use descriptive column headers
2. Keep templates clean and organized
3. Add title rows for context
4. Use formatting to highlight important sections
5. Provide `context` parameter if column names are ambiguous

## Regenerating Templates

If you need to regenerate these templates:

```bash
cd examples
python create_excel_templates.py
```

This will recreate all templates in the `excel_templates/` directory.

## Testing Templates

To test if a template works correctly:

1. Upload it to `/api/v1/excel/preview` to see what AI understands
2. Check the response to see detected columns and mappings
3. Use `/api/v1/excel/fill-template` to get the filled result
4. Verify the output has correct data and preserved formatting

## Troubleshooting

**Problem**: AI doesn't understand column mappings
**Solution**: Add `context` parameter with explanation, or use more standard column names

**Problem**: No data returned
**Solution**: Check if database has matching data, or relax filter conditions in `context`

**Problem**: Formatting lost
**Solution**: Ensure template uses supported Excel features (basic fonts, colors, borders)

## More Information

See full documentation: `docs/EXCEL_TEMPLATE_FILLING.md`
