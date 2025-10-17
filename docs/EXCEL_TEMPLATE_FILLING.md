# AI-Powered Excel Template Filling

## 概述

本功能允许用户上传自定义的Excel模板文件,系统会自动:
1. 解析模板结构(表头、格式、样式)
2. 使用AI理解模板需要什么数据
3. 从数据库查询相应数据
4. 按原模板格式填充数据
5. 返回填充后的Excel文件

**核心特性**:
- ✅ **保留原格式**: 完全保留模板的样式、颜色、合并单元格等
- ✅ **AI理解**: 智能理解模板列名含义,自动匹配数据库字段
- ✅ **灵活查询**: 支持简单查询和AI生成的复杂SQL
- ✅ **上下文感知**: 可提供额外说明帮助AI更准确理解模板意图

## API接口文档

### Endpoint

```
POST /api/v1/excel/fill-template
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | File | ✅ | - | Excel模板文件 (.xlsx) |
| `context` | String | ❌ | null | 上下文说明 (帮助AI理解) |
| `limit` | Integer | ❌ | 1000 | 最大填充行数 (1-10000) |

### 请求示例

#### cURL
```bash
curl -X POST "http://localhost:8000/api/v1/excel/fill-template?context=本月项目进度报告&limit=500" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@/path/to/template.xlsx" \
     --output filled_template.xlsx
```

#### Python
```python
import requests

url = "http://localhost:8000/api/v1/excel/fill-template"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

files = {"file": open("template.xlsx", "rb")}
params = {
    "context": "延期项目分析报告",
    "limit": 500
}

response = requests.post(url, headers=headers, files=files, params=params)

if response.status_code == 200:
    with open("filled_template.xlsx", "wb") as f:
        f.write(response.content)
    print("模板填充成功!")
else:
    print(f"错误: {response.text}")
```

#### JavaScript (Fetch)
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
    'http://localhost:8000/api/v1/excel/fill-template?context=项目统计&limit=1000',
    {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    }
);

if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'filled_template.xlsx';
    a.click();
}
```

### 响应

**成功响应 (200)**:
- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Body**: Excel文件二进制流
- **Headers**:
  ```
  Content-Disposition: attachment; filename="filled_template_20241217_143052.xlsx"
  X-Rows-Filled: 245
  X-Data-Source: applications
  X-Processing-Time-Ms: 3456
  X-Template-Title: 项目进度报表
  X-AI-Reasoning: 基于列名识别为应用转型项目数据...
  ```

**错误响应**:

| 状态码 | 说明 | 错误示例 |
|--------|------|----------|
| 400 | 请求参数错误 | 非Excel文件、文件过大 |
| 401 | 未授权 | Token无效或过期 |
| 403 | 权限不足 | 需要ADMIN/MANAGER/EDITOR角色 |
| 500 | 服务器错误 | 模板解析失败、数据库错误 |

```json
{
    "detail": "Invalid template: Unable to find header row"
}
```

## 前端集成指南

### React示例

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function ExcelTemplateFiller() {
    const [file, setFile] = useState(null);
    const [context, setContext] = useState('');
    const [loading, setLoading] = useState(false);
    const [metadata, setMetadata] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await axios.post(
                `/api/v1/excel/fill-template?context=${encodeURIComponent(context)}&limit=1000`,
                formData,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'multipart/form-data'
                    },
                    responseType: 'blob'
                }
            );

            // 提取元数据
            const rowsFilled = response.headers['x-rows-filled'];
            const dataSource = response.headers['x-data-source'];
            const processingTime = response.headers['x-processing-time-ms'];

            setMetadata({
                rowsFilled,
                dataSource,
                processingTime
            });

            // 下载文件
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `filled_template_${Date.now()}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();

            alert(`成功! 填充了${rowsFilled}行数据，耗时${processingTime}ms`);
        } catch (error) {
            console.error('Error:', error);
            alert(`填充失败: ${error.response?.data?.detail || error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2>Excel模板填充</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>上传模板文件:</label>
                    <input
                        type="file"
                        accept=".xlsx,.xls"
                        onChange={handleFileChange}
                        required
                    />
                </div>
                <div>
                    <label>说明 (可选):</label>
                    <input
                        type="text"
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        placeholder="例如: 本月延期项目报告"
                    />
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? '处理中...' : '填充模板'}
                </button>
            </form>

            {metadata && (
                <div className="metadata">
                    <h3>填充结果</h3>
                    <p>填充行数: {metadata.rowsFilled}</p>
                    <p>数据来源: {metadata.dataSource}</p>
                    <p>处理时间: {metadata.processingTime}ms</p>
                </div>
            )}
        </div>
    );
}

export default ExcelTemplateFiller;
```

### Vue示例

```vue
<template>
  <div class="excel-template-filler">
    <h2>Excel模板填充</h2>

    <el-upload
      ref="upload"
      :auto-upload="false"
      :on-change="handleFileChange"
      :limit="1"
      accept=".xlsx,.xls"
      drag
    >
      <i class="el-icon-upload"></i>
      <div class="el-upload__text">
        拖拽文件到这里或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">只支持xlsx/xls格式,最大50MB</div>
      </template>
    </el-upload>

    <el-form :model="form" style="margin-top: 20px;">
      <el-form-item label="说明(可选)">
        <el-input
          v-model="form.context"
          placeholder="例如: 本月延期项目分析"
        ></el-input>
      </el-form-item>

      <el-form-item label="最大行数">
        <el-input-number
          v-model="form.limit"
          :min="1"
          :max="10000"
          :step="100"
        ></el-input-number>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="loading"
          :disabled="!file"
        >
          填充模板
        </el-button>
      </el-form-item>
    </el-form>

    <el-alert
      v-if="result"
      :title="`成功填充${result.rows}行数据`"
      type="success"
      :description="`数据来源: ${result.source}, 耗时: ${result.time}ms`"
      show-icon
      :closable="false"
    ></el-alert>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ExcelTemplateFiller',
  data() {
    return {
      file: null,
      form: {
        context: '',
        limit: 1000
      },
      loading: false,
      result: null
    };
  },
  methods: {
    handleFileChange(file) {
      this.file = file.raw;
    },

    async handleSubmit() {
      if (!this.file) {
        this.$message.warning('请先上传模板文件');
        return;
      }

      this.loading = true;

      try {
        const formData = new FormData();
        formData.append('file', this.file);

        const response = await axios.post(
          '/api/v1/excel/fill-template',
          formData,
          {
            params: {
              context: this.form.context,
              limit: this.form.limit
            },
            headers: {
              'Authorization': `Bearer ${this.$store.state.token}`
            },
            responseType: 'blob'
          }
        );

        // 提取元数据
        this.result = {
          rows: response.headers['x-rows-filled'],
          source: response.headers['x-data-source'],
          time: response.headers['x-processing-time-ms']
        };

        // 下载文件
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `filled_${Date.now()}.xlsx`);
        document.body.appendChild(link);
        link.click();
        link.remove();

        this.$message.success('模板填充成功!');
      } catch (error) {
        console.error('Error:', error);
        this.$message.error(
          error.response?.data?.detail || '填充失败,请重试'
        );
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## 模板创建指南

### 模板要求

1. **必须包含表头行**
   - 表头应该是清晰的文本(不是数字或日期)
   - 至少有2列表头
   - 通常在文件前10行内

2. **列名建议**
   - 使用清晰的中文或英文列名
   - 常见列名AI会自动识别:
     - L2 ID / 应用ID / ID
     - 应用名称 / 名称 / app_name
     - 进度 / 进度% / progress
     - 状态 / current_status
     - 团队 / 开发团队 / dev_team
     - 负责人 / owner
     - 转型目标 / target
     - 计划日期 / 实际日期 / date
     - 延期天数 / delay

3. **格式支持**
   - ✅ 标题行 (合并单元格)
   - ✅ 彩色表头
   - ✅ 单元格边框
   - ✅ 背景颜色
   - ✅ 字体样式
   - ✅ 列宽设置
   - ✅ 单元格对齐方式

### 示例模板1: 项目进度报表

```
Row 1:  [合并A1:H1]  AK/云原生转型项目进度报表  (标题,蓝色背景)
Row 2:  [合并A2:H2]  生成时间: {自动填充当前时间}
Row 3:  [表头行,浅蓝色背景]
        L2 ID | 应用名称 | 转型目标 | 当前状态 | 进度% | 开发团队 | 负责人 | 备注
Row 4+: [数据行,自动填充]
```

**创建步骤**:
1. 在Excel中创建上述结构
2. 设置标题和表头的颜色、字体
3. 调整列宽
4. 保存为template_progress.xlsx
5. 上传到API

**AI理解结果**:
```json
{
  "data_source": "applications",
  "column_mappings": [
    {"excel_column": "L2 ID", "db_field": "l2_id"},
    {"excel_column": "应用名称", "db_field": "app_name"},
    {"excel_column": "转型目标", "db_field": "overall_transformation_target"},
    {"excel_column": "当前状态", "db_field": "current_status"},
    {"excel_column": "进度%", "db_field": "progress_percentage"},
    {"excel_column": "开发团队", "db_field": "dev_team"},
    {"excel_column": "负责人", "db_field": "dev_owner"}
  ]
}
```

### 示例模板2: 延期项目分析

```
Row 1:  [合并A1:I1]  延期项目分析报表  (红色背景)
Row 2:  统计时间: {当前时间}
Row 3:  [表头行]
        应用ID | 应用名称 | 负责团队 | 计划上线日期 | 实际上线日期 | 延期天数 | 当前进度 | 负责人 | 延期原因
Row 4+: [数据行,延期项目]
```

**上传时提供context**:
```
context="只显示延期项目"
```

**AI会自动添加过滤条件**:
```json
{
  "filters": {
    "is_delayed": true
  }
}
```

### 示例模板3: 团队统计

```
Row 1:  团队转型项目统计表
Row 2:  [表头]
        团队名称 | 项目总数 | 已完成 | 进行中 | 未开始 | 平均进度 | 延期项目数
Row 3+: [按团队汇总的数据]
```

**AI可能生成GROUP BY查询**:
```sql
SELECT
    dev_team,
    COUNT(*) as total,
    SUM(CASE WHEN progress_percentage = 100 THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN progress_percentage > 0 AND progress_percentage < 100 THEN 1 ELSE 0 END) as in_progress,
    SUM(CASE WHEN progress_percentage = 0 THEN 1 ELSE 0 END) as not_started,
    AVG(progress_percentage) as avg_progress,
    SUM(CASE WHEN is_delayed THEN 1 ELSE 0 END) as delayed
FROM applications
GROUP BY dev_team
ORDER BY dev_team
```

## 高级用法

### 使用context提示

`context`参数可以帮助AI更准确理解模板意图:

```bash
# 明确指定筛选条件
context="只显示2024年的项目"

# 指定团队
context="只显示研发一部的项目"

# 指定状态
context="只显示进行中的项目"

# 组合条件
context="2024年延期超过30天的项目"
```

### 自定义SQL (高级)

如果AI无法正确理解,可以在模板的备注单元格中提供SQL提示:

在模板的某个隐藏单元格(如Z1)中写入:
```
SQL_HINT: SELECT * FROM applications WHERE ak_supervision_acceptance_year = 2024 AND is_delayed = true
```

### 处理大数据量

对于大量数据,建议:

1. 使用`limit`参数分批处理:
   ```
   limit=1000  # 第一批
   limit=10000 # 如果需要更多
   ```

2. 在`context`中指定筛选条件:
   ```
   context="2024年Q1的项目"
   ```

3. 模板中使用更精确的列名,帮助AI理解

## 性能指标

| 场景 | 模板大小 | 数据行数 | 处理时间 | 文件大小 |
|------|---------|---------|---------|---------|
| 简单列表 | 10KB | 100行 | ~1s | 15KB |
| 中等复杂 | 50KB | 500行 | ~3s | 80KB |
| 复杂报表 | 100KB | 1000行 | ~5s | 200KB |
| 大批量 | 100KB | 5000行 | ~15s | 800KB |

**优化建议**:
- 减少不必要的列
- 使用`limit`参数限制行数
- 避免过度复杂的格式

## 故障排查

### 常见问题

**1. 模板无法识别表头**
- **原因**: 表头行不明显或在太靠后的位置
- **解决**: 确保表头在前10行,且包含清晰的文本

**2. 列映射错误**
- **原因**: 列名不够清晰,AI无法理解
- **解决**: 使用标准列名,或在`context`中说明

**3. 数据为空**
- **原因**: 筛选条件过于严格,或数据库没有匹配数据
- **解决**: 检查`context`,放宽筛选条件

**4. 格式丢失**
- **原因**: 某些复杂格式可能不完全支持
- **解决**: 使用基础格式(颜色、边框、字体)

**5. 处理时间过长**
- **原因**: 数据量过大或SQL查询复杂
- **解决**: 减少`limit`,简化模板

### 调试模式

查看详细的处理信息:

```bash
# 检查响应头
curl -I -X POST "..." -F "file=@template.xlsx"

# 输出:
X-Rows-Filled: 245
X-Data-Source: applications
X-AI-Reasoning: 基于列名'L2 ID','应用名称'识别为应用表...
```

### 日志查询

管理员可以查看服务器日志:

```bash
# 查找模板填充相关日志
grep "Filling template" /var/log/akcn/app.log

# 输出示例:
[2024-12-17 14:30:52] Filling template for user admin: template_progress.xlsx
[2024-12-17 14:30:53] Parsing Excel template...
[2024-12-17 14:30:53] Understanding template with AI...
[2024-12-17 14:30:54] AI template understanding: 基于规则的列名匹配
[2024-12-17 14:30:54] Querying database: applications
[2024-12-17 14:30:55] Filling template with 245 rows...
[2024-12-17 14:30:56] Template filled successfully: 245 rows, 3456ms
```

## 安全考虑

### 权限控制
- ✅ 需要ADMIN/MANAGER/EDITOR角色
- ✅ 每个用户的请求都有认证和授权检查
- ✅ 审计日志记录所有操作

### 数据安全
- ✅ 只能查询当前用户有权限访问的数据
- ✅ SQL注入防护(参数化查询)
- ✅ 文件大小限制(50MB)
- ✅ 行数限制(最多10000行)

### 最佳实践
1. 不要在模板中包含敏感信息
2. 定期审查下载的文件
3. 使用HTTPS传输
4. 及时清理下载的文件

## 示例场景

### 场景1: 月度进度汇报

**需求**: 生成包含所有项目进度的月度报告

**步骤**:
1. 创建模板:
   - 标题: "2024年12月项目进度月报"
   - 列: 应用ID、应用名称、状态、进度、团队、负责人、备注

2. 上传模板:
   ```bash
   curl -X POST ".../fill-template" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@monthly_template.xlsx"
   ```

3. 获得填充后的报告,可直接发送给领导

### 场景2: 延期项目专项报告

**需求**: 只显示延期超过14天的项目

**步骤**:
1. 创建模板(包含延期相关列)

2. 上传时提供context:
   ```bash
   curl -X POST ".../fill-template?context=延期超过14天的项目" \
        -F "file=@delay_template.xlsx"
   ```

3. AI会自动筛选延期项目

### 场景3: 团队对比分析

**需求**: 对比各团队的转型进度

**步骤**:
1. 创建汇总模板(列为: 团队、项目数、完成数、平均进度等)

2. 在context中说明:
   ```
   context="按团队统计项目完成情况"
   ```

3. AI会生成GROUP BY查询,返回汇总数据

## 总结

**核心优势**:
1. 🎨 **完全自定义**: 用户控制模板样式和结构
2. 🤖 **AI驱动**: 智能理解模板意图,无需手动配置映射
3. ⚡ **高效**: 几秒钟完成数百行数据填充
4. 🔒 **安全**: 权限控制、审计日志、参数化查询

**适用场景**:
- 定期报告自动化
- 临时数据导出
- 定制化数据展示
- 批量数据处理

**开始使用**:
1. 准备一个Excel模板
2. 调用API上传模板
3. 下载填充好的文件
4. 根据需要调整模板和context参数

更多帮助,请查阅API文档或联系技术支持!
