# AI增强功能快速启动指南

本指南帮助您快速启用MCP系统的AI增强功能。

## 目录
1. [选择AI服务](#选择ai服务)
2. [免费方案：本地模型](#免费方案本地模型-ollama)
3. [付费方案：OpenAI](#付费方案openai)
4. [付费方案：Claude](#付费方案claude)
5. [企业方案：Azure OpenAI](#企业方案azure-openai)
6. [验证配置](#验证配置)
7. [故障排查](#故障排查)

---

## 选择AI服务

| 方案 | 成本 | 速度 | 质量 | 适用场景 |
|------|------|------|------|----------|
| **本地模型 (Ollama)** | 免费 | 快 | 中 | 开发测试、数据隐私要求高 |
| **OpenAI** | $0.01-0.03/1K tokens | 中 | 高 | 生产环境、英文为主 |
| **Claude** | $0.015-0.075/1K tokens | 中 | 极高 | 复杂分析、中英文混合 |
| **Azure OpenAI** | 同OpenAI | 中 | 高 | 企业级、合规要求 |

### 推荐选择：

- **开发阶段** → 本地模型（免费）
- **小团队** → OpenAI GPT-3.5（便宜）
- **大企业** → Azure OpenAI（合规）
- **最佳质量** → Claude 3 Opus

---

## 免费方案：本地模型 (Ollama)

### 步骤1：安装Ollama

**Windows:**
```bash
# 下载并安装
https://ollama.ai/download/windows

# 或使用 winget
winget install Ollama.Ollama
```

**macOS:**
```bash
# 使用 Homebrew
brew install ollama

# 或下载安装包
https://ollama.ai/download/mac
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 步骤2：下载模型

```bash
# 推荐模型：Qwen 7B（中文效果好，7GB）
ollama pull qwen:7b

# 或者：DeepSeek Coder（代码分析强，7GB）
ollama pull deepseek-coder:7b

# 轻量级选择：Qwen 4B（性能一般，4GB）
ollama pull qwen:4b

# 高质量选择：Qwen 14B（需要16GB+内存）
ollama pull qwen:14b
```

### 步骤3：启动Ollama服务

```bash
# Ollama会自动启动为后台服务
# 验证服务运行
curl http://localhost:11434/api/generate -d '{
  "model": "qwen:7b",
  "prompt": "Hello",
  "stream": false
}'
```

### 步骤4：配置后端

编辑 `.env` 文件：

```bash
# 启用AI功能
MCP_ENABLE_AI_TOOLS=True

# 本地模型配置
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=qwen:7b
```

### 步骤5：重启后端

```bash
# 停止现有服务
# Windows
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*"

# Linux/Mac
pkill -f uvicorn

# 重新启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **完成！** 现在可以使用免费的AI功能了。

---

## 付费方案：OpenAI

### 步骤1：获取API Key

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账号
3. 进入 API Keys 页面：https://platform.openai.com/api-keys
4. 点击 "Create new secret key"
5. 复制生成的 key（sk-...）

**国内用户注意：**
- 需要科学上网
- 或使用国内中转服务（搜索"OpenAI中转API"）

### 步骤2：配置后端

编辑 `.env` 文件：

```bash
# 启用AI功能
MCP_ENABLE_AI_TOOLS=True

# OpenAI官方配置
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4-turbo-preview  # 或 gpt-3.5-turbo（更便宜）
OPENAI_BASE_URL=https://api.openai.com/v1

# 或使用中转服务
# OPENAI_API_KEY=你的中转key
# OPENAI_BASE_URL=https://api.your-proxy.com/v1
# OPENAI_MODEL=gpt-4-turbo-preview
```

### 模型选择建议：

```bash
# 最便宜（~$0.0015/1K tokens）
OPENAI_MODEL=gpt-3.5-turbo

# 平衡性价比（~$0.01/1K tokens）
OPENAI_MODEL=gpt-4-turbo-preview

# 最强性能（~$0.03/1K tokens）
OPENAI_MODEL=gpt-4
```

### 步骤3：重启后端并测试

```bash
# 重启服务
uvicorn app.main:app --reload

# 测试API
curl -X POST http://localhost:8000/api/v1/mcp/ai/report \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"test": "data"},
    "report_type": "summary"
  }'
```

---

## 付费方案：Claude

### 步骤1：获取API Key

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录
3. 进入 API Keys：https://console.anthropic.com/account/keys
4. 创建新的API Key
5. 复制key（sk-ant-...）

### 步骤2：配置后端

编辑 `.env` 文件：

```bash
# 启用AI功能
MCP_ENABLE_AI_TOOLS=True

# Anthropic配置
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229  # 最强模型

# 或使用更便宜的模型
# ANTHROPIC_MODEL=claude-3-sonnet-20240229  # 平衡
# ANTHROPIC_MODEL=claude-3-haiku-20240307   # 最便宜
```

### 模型选择：

```bash
# 最强分析能力（~$0.015/1K input, $0.075/1K output）
ANTHROPIC_MODEL=claude-3-opus-20240229

# 平衡选择（~$0.003/1K input, $0.015/1K output）
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# 最快最便宜（~$0.00025/1K input, $0.00125/1K output）
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

---

## 企业方案：Azure OpenAI

### 步骤1：创建Azure OpenAI资源

1. 登录 [Azure Portal](https://portal.azure.com/)
2. 搜索 "Azure OpenAI"
3. 创建新资源
4. 记录以下信息：
   - 终结点（Endpoint）
   - API密钥（Key）
   - 部署名称（Deployment Name）

### 步骤2：配置后端

编辑 `.env` 文件：

```bash
# 启用AI功能
MCP_ENABLE_AI_TOOLS=True

# Azure OpenAI配置
AZURE_OPENAI_API_KEY=your-azure-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## 验证配置

### 方法1：检查健康状态

```bash
curl http://localhost:8000/api/v1/mcp/health
```

期望输出：
```json
{
  "status": "healthy",
  "integration": "direct_api",
  "tools_count": "15",
  "ai_enabled": "True",
  "ai_provider": "openai"  // 或 "anthropic", "azure", "local"
}
```

### 方法2：测试AI报告生成

```bash
curl -X POST http://localhost:8000/api/v1/mcp/ai/report \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "total_applications": 100,
      "completed": 45,
      "in_progress": 30,
      "delayed": 15
    },
    "report_type": "summary",
    "language": "zh"
  }'
```

成功响应：
```json
{
  "success": true,
  "report": "项目管理概况报告：目前共有100个应用项目，其中45个已完成...",
  "metadata": {
    "report_type": "summary",
    "language": "zh",
    "generated_at": "2024-12-10T...",
    "provider": "openai"
  }
}
```

### 方法3：测试自然语言查询

```bash
curl -X POST http://localhost:8000/api/v1/mcp/query/applications \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "显示所有延期的项目"}'
```

---

## 故障排查

### 问题1：AI功能未启用

**症状：** API返回 "AI功能未启用"

**解决：**
```bash
# 检查.env文件
cat .env | grep MCP_ENABLE_AI_TOOLS

# 确保设置为True
MCP_ENABLE_AI_TOOLS=True

# 重启服务
```

### 问题2：本地模型连接失败

**症状：** "Connection refused to localhost:11434"

**解决：**
```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 如果没有响应，启动Ollama
# Windows: 在开始菜单运行 Ollama
# Linux/Mac:
ollama serve

# 验证模型已下载
ollama list
```

### 问题3：OpenAI API密钥无效

**症状：** "Invalid API key"

**解决：**
```bash
# 验证API key格式（应该以sk-开头）
echo $OPENAI_API_KEY

# 测试API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 如果使用中转，确保BASE_URL正确
OPENAI_BASE_URL=https://api.your-proxy.com/v1
```

### 问题4：Anthropic API限流

**症状：** "Rate limit exceeded"

**解决：**
1. 检查账户配额：https://console.anthropic.com/settings/limits
2. 降低调用频率
3. 升级账户等级

### 问题5：Azure配置错误

**症状：** "Resource not found"

**解决：**
```bash
# 检查配置
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_DEPLOYMENT

# 确保endpoint格式正确
# 正确: https://your-resource.openai.azure.com
# 错误: https://your-resource.openai.azure.com/

# 验证部署名称
# 在Azure Portal中查看实际的部署名称
```

### 问题6：pydantic导入错误

**症状：** "BaseSettings has been moved to pydantic-settings"

**解决：**
```bash
# 安装pydantic-settings
pip install pydantic-settings

# 或更新requirements.txt
echo "pydantic-settings>=2.0.0" >> requirements.txt
pip install -r requirements.txt
```

---

## 性能优化建议

### 1. 缓存AI响应

```python
# 在前端实现缓存
const cacheKey = `ai_report_${JSON.stringify(data)}`;
const cached = localStorage.getItem(cacheKey);
if (cached) {
  return JSON.parse(cached);
}

const result = await generateReport(data);
localStorage.setItem(cacheKey, JSON.stringify(result));
```

### 2. 异步处理

对于耗时的AI操作，使用后台任务：

```python
# 使用Celery处理AI请求
@celery.task
def generate_ai_report_async(data):
    return ai_assistant.generate_report(data)
```

### 3. 限流策略

```python
# 在endpoints中添加限流
from fastapi_limiter.depends import RateLimiter

@router.post("/ai/report", dependencies=[Depends(RateLimiter(times=10, minutes=1))])
async def generate_ai_report(...):
    ...
```

### 4. 模型选择策略

```python
# 根据请求复杂度选择模型
if query_complexity == "simple":
    model = "gpt-3.5-turbo"  # 便宜快速
elif query_complexity == "complex":
    model = "gpt-4"  # 高质量
```

---

## 成本预估

### OpenAI费用示例

| 使用场景 | 每日调用 | 月度费用（USD） |
|---------|---------|----------------|
| 小团队测试 | 100次 | ~$3 |
| 中等规模使用 | 1000次 | ~$30 |
| 生产环境 | 10000次 | ~$300 |

### 节省成本技巧

1. **使用GPT-3.5代替GPT-4** → 节省80%费用
2. **本地模型处理简单查询** → 免费
3. **缓存常见查询结果** → 减少API调用
4. **批量处理请求** → 减少请求次数
5. **使用Azure预留实例** → 折扣30-50%

---

## 下一步

配置完成后，查看以下文档：

- [前端集成指南](./FRONTEND_AI_INTEGRATION.md)
- [MCP Agent文档](./MCP_AGENT.md)
- [API文档](http://localhost:8000/docs)

---

## 获取帮助

遇到问题？

1. 检查日志：`tail -f logs/app.log`
2. 查看文档：`docs/`目录
3. 测试health端点：`/api/v1/mcp/health`

---

*最后更新：2024-12-10*
*版本：1.0.0*
