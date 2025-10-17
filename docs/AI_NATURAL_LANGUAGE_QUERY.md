# AI自然语言查询使用指南

## 概述

系统现在支持真正的AI驱动的自然语言查询！完整流程：

```
用户输入自然语言
    ↓
LM Studio (Qwen) 理解意图
    ↓
AI生成SQL或选择MCP工具
    ↓
执行查询
    ↓
AI生成自然语言报告
    ↓
返回结果
```

## 可用端点

### 1. `/api/v1/mcp/query/applications` - 完整AI增强查询（推荐）

**适用场景**: 任何自然语言查询

**示例请求**:
```bash
curl -X POST http://localhost:8000/api/v1/mcp/query/applications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-admin" \
  -d '{
    "query": "查看应用ID为123的详情"
  }'
```

**AI处理流程**:
1. ✅ 理解意图："用户想查看特定应用的详细信息"
2. ✅ 选择工具：`app_get`
3. ✅ 提取参数：`{"app_id": 123}`
4. ✅ 执行工具
5. ✅ 生成中文报告
6. ✅ 提供下一步建议

**响应示例**:
```json
{
  "success": true,
  "result": { /* 应用详情数据 */ },
  "query_interpretation": "AI解析: 用户想查看ID为123的应用详情\n执行工具: app_get\n参数: {\"app_id\": 123}",
  "ai_report": "根据查询结果，应用'测试应用'（ID: 123）当前状态为进行中...",
  "ai_suggestions": {
    "success": true,
    "suggestions": "建议检查子任务进度...",
    "reasoning": "该应用有2个延期的子任务"
  }
}
```

### 2. `/api/v1/mcp/query` - 智能SQL查询

**适用场景**: SQL查询或简单自然语言（自动识别）

**示例1 - SQL查询**:
```bash
curl -X POST http://localhost:8000/api/v1/mcp/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-admin" \
  -d '{
    "query": "SELECT * FROM applications WHERE id = 123"
  }'
```

**示例2 - 自然语言（AI转SQL）**:
```bash
curl -X POST http://localhost:8000/api/v1/mcp/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-admin" \
  -d '{
    "query": "列出所有延期的项目"
  }'
```

AI会自动生成：
```sql
SELECT * FROM applications
WHERE is_delayed = true
ORDER BY delay_days DESC
```

## 自然语言查询示例

### 查询特定应用
```
用户: "查看应用ID为123的详情"
AI: 选择 app_get 工具
结果: 返回应用123的完整信息
```

### 列表查询
```
用户: "显示所有进行中的应用"
AI: 生成 SELECT * FROM applications WHERE current_status = '进行中'
结果: 返回所有进行中的应用列表
```

### 统计查询
```
用户: "本月完成了多少个项目？"
AI: 选择 dashboard_stats 工具或生成聚合SQL
结果: 返回统计数据
```

### 复杂查询
```
用户: "哪些项目延期超过30天？"
AI: 生成 SELECT * FROM applications WHERE is_delayed = true AND delay_days > 30
结果: 返回符合条件的项目，并提供改进建议
```

## 前端集成

### TypeScript/JavaScript示例

```typescript
// 自然语言查询函数
async function naturalLanguageQuery(query: string) {
  const response = await fetch('/api/v1/mcp/query/applications', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ query })
  });

  const result = await response.json();

  return {
    data: result.result,
    report: result.ai_report,      // AI生成的中文报告
    suggestions: result.ai_suggestions,  // AI建议
    interpretation: result.query_interpretation  // AI如何理解查询
  };
}

// 使用示例
const result = await naturalLanguageQuery('查看应用ID为123的详情');
console.log(result.report);  // 显示AI生成的报告
console.log(result.suggestions);  // 显示AI建议
```

### React Hook示例

```typescript
import { useState } from 'react';

function useNaturalLanguageQuery() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [report, setReport] = useState('');

  const query = async (naturalLanguage: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/mcp/query/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ query: naturalLanguage })
      });

      const result = await response.json();
      setData(result.result);
      setReport(result.ai_report);

      return result;
    } finally {
      setLoading(false);
    }
  };

  return { query, loading, data, report };
}

// 组件中使用
function QueryPanel() {
  const { query, loading, data, report } = useNaturalLanguageQuery();

  const handleQuery = async () => {
    await query('显示所有延期的项目');
  };

  return (
    <div>
      {loading && <p>AI正在处理...</p>}
      {report && <div className="ai-report">{report}</div>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}
```

## AI解析能力

LM Studio的Qwen模型可以理解：

### 1. 中文查询
- ✅ "查看应用123的详情"
- ✅ "列出所有延期的项目"
- ✅ "统计本月完成的数量"
- ✅ "哪些团队效率最高？"

### 2. 英文查询
- ✅ "Show application 123"
- ✅ "List delayed projects"
- ✅ "Count completed this month"

### 3. 复杂查询
- ✅ "查询延期超过30天且开发团队为A的应用"
- ✅ "对比不同团队的项目完成率"
- ✅ "预测下月能完成的项目数量"

### 4. 聚合统计
- ✅ "每个团队有多少个项目？"
- ✅ "平均延期天数是多少？"
- ✅ "完成率最高的是哪个团队？"

## 配置要求

确保 `.env` 中配置：

```bash
# 启用AI功能
MCP_ENABLE_AI_TOOLS=True

# LM Studio配置
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=Qwen2.5-7B-Instruct-Q4_K_M
OPENAI_TIMEOUT=120
```

## 性能建议

### 响应时间
- **SQL查询**: < 1秒
- **AI解析**: 2-10秒（取决于LM Studio性能）
- **AI报告生成**: 5-15秒

### 优化建议
1. **使用较小的模型**: Qwen2.5-4B 比 7B 快一倍
2. **GPU加速**: 在LM Studio中启用GPU
3. **缓存常见查询**: 缓存AI解析结果
4. **异步处理**: 先返回数据，后台生成报告

## 故障排除

### AI未启用
```json
{
  "ai_report": "AI report generation is disabled"
}
```
**解决**: 检查 `.env` 中 `MCP_ENABLE_AI_TOOLS=True`

### 超时错误
```
TimeoutError: AI request timeout
```
**解决**: 增加 `OPENAI_TIMEOUT` 或使用更小的模型

### 解析失败
AI解析失败时会自动降级到关键字匹配模式，仍能返回结果。

## 高级功能

### 自定义AI Prompt

可以修改 `app/services/mcp_service.py` 中的prompt来调整AI行为：

```python
prompt = f"""你是一个数据库查询助手。
用户查询: {query}
数据库结构: {schema}

请分析用户意图并返回JSON...
"""
```

### 多轮对话

可以在前端维护对话历史，实现上下文查询：

```typescript
const conversationHistory = [];

async function queryWithContext(userQuery: string) {
  conversationHistory.push({ role: 'user', content: userQuery });

  const result = await naturalLanguageQuery(userQuery);

  conversationHistory.push({ role: 'assistant', content: result.report });

  return result;
}
```

---

**需要帮助？**
- 查看日志：`logs/app.log`
- LM Studio日志：LM Studio控制台
- 测试端点：`http://localhost:8000/api/v1/mcp/health`

*最后更新: 2025-10-16*
