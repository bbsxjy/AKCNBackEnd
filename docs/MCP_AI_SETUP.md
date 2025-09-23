# MCP Agent AI配置指南

## 概述

MCP Agent有两种AI集成方式：

1. **作为服务器被AI调用**（默认模式）
   - MCP Agent作为服务器，被Claude Desktop、ChatGPT等AI客户端调用
   - **不需要配置API Key**
   - AI客户端通过MCP协议连接到你的后端

2. **主动调用其他AI服务**（可选功能）
   - MCP Agent可以调用OpenAI、Claude API等服务
   - 用于智能查询分析、报告生成等增强功能
   - **需要配置相应的API Key**

## 配置方式

### 方式1：被AI客户端调用（推荐）

这是MCP的主要使用方式，你的MCP server被AI助手调用：

#### Claude Desktop配置

1. 找到Claude Desktop配置文件位置：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. 添加MCP服务器配置：

```json
{
  "mcpServers": {
    "akcn-backend": {
      "command": "python",
      "args": ["-m", "app.mcp.run_server"],
      "cwd": "D:\\Program Files (x86)\\CodeRepos\\AKCNProjectManagement\\AKCNBackEnd",
      "env": {
        "PYTHONPATH": ".",
        "DATABASE_URL": "postgresql+asyncpg://akcn_user:akcn_password@localhost:5432/akcn_dev_db"
      }
    }
  }
}
```

3. 重启Claude Desktop，MCP服务器会自动启动

#### 其他AI客户端配置

如果使用ChatGPT、Cursor等其他支持MCP的AI工具：

```python
# 使用MCP客户端连接
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# 连接到你的MCP服务器
server_params = StdioServerParameters(
    command="python",
    args=["-m", "app.mcp.run_server"],
    env={"DATABASE_URL": "your_database_url"}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # AI可以调用你的工具
        result = await session.call_tool("app_list", {"limit": 10})
```

### 方式2：MCP主动调用AI服务（可选）

如果你想让MCP Agent具备AI能力，可以配置以下服务之一：

#### 配置OpenAI

在`.env`文件中添加：

```bash
# OpenAI官方API
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# 或者使用代理/中转服务
OPENAI_API_KEY=your-proxy-api-key
OPENAI_BASE_URL=https://api.your-proxy.com/v1
OPENAI_MODEL=gpt-4-turbo-preview

# 启用AI工具
MCP_ENABLE_AI_TOOLS=True
```

#### 配置Anthropic Claude

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# 启用AI工具
MCP_ENABLE_AI_TOOLS=True
```

#### 配置Azure OpenAI

```bash
# Azure OpenAI Service
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 启用AI工具
MCP_ENABLE_AI_TOOLS=True
```

#### 配置本地大模型（Ollama）

```bash
# 首先安装并运行Ollama
# https://ollama.ai/download

# 下载模型
ollama pull llama2
# 或
ollama pull qwen:7b
# 或
ollama pull deepseek-coder:7b

# 在.env中配置
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2  # 或其他已下载的模型

# 启用AI工具
MCP_ENABLE_AI_TOOLS=True
```

## AI增强功能

当启用AI工具后（`MCP_ENABLE_AI_TOOLS=True`），MCP Agent将具备：

### 1. 智能查询分析
```python
# MCP会使用AI分析SQL查询
result = await client.call_tool(
    "db_query",
    {
        "query": "SELECT * FROM applications WHERE status = 'DELAYED'",
        "analyze": True  # AI将分析查询性能
    }
)
```

### 2. 自然语言报告生成
```python
# AI将数据转换为自然语言报告
result = await client.call_tool(
    "dashboard_export",
    {
        "format": "natural_language",
        "stat_type": "summary"
    }
)
```

### 3. 智能操作建议
```python
# AI基于当前状态建议下一步操作
result = await client.call_tool(
    "suggest_actions",
    {"context": "current_project_state"}
)
```

## 费用说明

### 免费选项
1. **被AI调用**：完全免费，不需要任何API Key
2. **本地模型**：使用Ollama等本地模型，只需要计算资源

### 付费选项
1. **OpenAI API**：按token计费，约$0.01-0.03/1000 tokens
2. **Claude API**：按token计费，约$0.015-0.075/1000 tokens
3. **Azure OpenAI**：按token计费，价格与OpenAI类似

## 常见问题

### Q1: 我必须配置API Key吗？
**不需要**。如果你只是想让Claude Desktop或其他AI工具访问你的后端，不需要任何API Key。

### Q2: 什么时候需要配置API Key？
只有当你想让MCP Agent主动调用AI服务来增强功能时才需要。

### Q3: 如何选择AI服务？
- **速度优先**：使用本地模型（Ollama）
- **质量优先**：使用GPT-4或Claude-3
- **成本优先**：使用GPT-3.5或本地模型
- **合规要求**：使用Azure OpenAI或私有部署

### Q4: 可以同时配置多个AI服务吗？
MCP会按优先级选择：OpenAI > Anthropic > Azure > Local。只会使用第一个配置的服务。

### Q5: 如何测试AI功能？
```bash
# 测试AI分析功能
python -c "
import asyncio
from app.mcp.ai_tools import ai_assistant

async def test():
    result = await ai_assistant.analyze_query(
        'SELECT * FROM applications WHERE status = DELAYED'
    )
    print(result)

asyncio.run(test())
"
```

## 安全建议

1. **API Key安全**
   - 永远不要将API Key提交到Git
   - 使用环境变量或密钥管理服务
   - 定期轮换API Key

2. **访问控制**
   - MCP服务器应该只在本地或内网运行
   - 不要将MCP服务器暴露到公网

3. **数据隐私**
   - 如果使用外部AI服务，注意数据隐私
   - 考虑使用本地模型处理敏感数据
   - 可以配置数据脱敏规则

---

*最后更新：2024年12月*