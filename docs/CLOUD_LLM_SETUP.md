# 云端LLM推理配置指南

本指南帮助你将LLM推理从本地LM Studio迁移到云端GPU平台（矩池云、SiliconFlow等），获得更快的推理速度。

## 为什么使用云端LLM？

**本地LM Studio的问题：**
- 响应慢（CPU推理或GPU资源有限）
- 占用本机资源
- 模型加载时间长

**云端GPU平台的优势：**
- 专业GPU（RTX 4090/A100）推理速度快
- 按需付费，无需购买硬件
- 7x24小时稳定运行
- 支持多模型切换

---

## 方案一：矩池云（JizhuCloud）【推荐新手】

### 1.1 注册和配置

1. **注册账号**
   - 访问：https://www.jizhulab.com/
   - 注册并完成实名认证
   - 充值（建议先充值50-100元测试）

2. **选择GPU实例**
   - 进入控制台 → GPU实例
   - 选择配置：
     - GPU：RTX 4090（性价比高）或 A100（性能最强）
     - 镜像：选择支持vLLM的PyTorch镜像
     - 系统盘：50GB
     - 数据盘：根据模型大小（Qwen2.5-7B约15GB）

3. **部署vLLM推理服务**

在矩池云实例终端中执行：

```bash
# 安装vLLM（如果镜像未预装）
pip install vllm -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动vLLM服务器（OpenAI兼容API）
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --served-model-name Qwen2.5-7B \
  --host 0.0.0.0 \
  --port 8000 \
  --trust-remote-code

# 或使用后台运行
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --served-model-name Qwen2.5-7B \
  --host 0.0.0.0 \
  --port 8000 \
  --trust-remote-code > vllm.log 2>&1 &
```

4. **获取公网访问地址**

矩池云支持两种方式：

**方式A：使用frp内网穿透（矩池云自带）**
```bash
# 矩池云控制台 → 网络 → 端口映射
# 映射本地8000端口到公网
# 获得类似：http://xxx.jizhulab.com:12345
```

**方式B：使用矩池云的公网IP（如果有）**
```bash
# 获取公网IP
curl ifconfig.me

# 访问地址：http://你的公网IP:8000
```

5. **测试API连接**

在本地Windows PowerShell测试：

```powershell
# 替换为你的矩池云API地址
$API_URL = "http://xxx.jizhulab.com:12345/v1"

# 测试模型列表
curl "$API_URL/models"

# 测试生成
curl "$API_URL/chat/completions" `
  -H "Content-Type: application/json" `
  -d '{
    "model": "Qwen2.5-7B",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 50
  }'
```

### 1.2 配置后端

修改 `D:\Program Files\Repos\AKCNBackEnd\.env`：

```env
# 启用AI工具
MCP_ENABLE_AI_TOOLS=True

# 矩池云vLLM配置
OPENAI_API_KEY=not-required  # vLLM默认不需要API Key
OPENAI_BASE_URL=http://xxx.jizhulab.com:12345/v1  # 替换为你的矩池云地址
OPENAI_MODEL=Qwen2.5-7B  # vLLM服务的模型名称

# 超时设置（云端更快）
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3
```

---

## 方案二：SiliconFlow【最简单，即开即用】

SiliconFlow是国内提供Qwen等模型API的云平台，无需自己部署，直接调用API。

### 2.1 获取API密钥

1. 访问：https://cloud.siliconflow.cn/
2. 注册账号
3. 进入控制台 → API密钥 → 创建新密钥
4. 复制API Key（格式：`sk-xxxxx`）
5. 查看价格：通常很便宜，如Qwen2.5-7B约 ¥0.0007/1K tokens

### 2.2 配置后端

修改 `.env`：

```env
MCP_ENABLE_AI_TOOLS=True

# SiliconFlow配置
OPENAI_API_KEY=sk-your-siliconflow-api-key-here  # 替换为你的密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct  # 或其他模型

OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3
```

### 2.3 支持的模型

SiliconFlow支持多种开源模型：
- `Qwen/Qwen2.5-7B-Instruct` - 通用中文模型
- `Qwen/Qwen2.5-14B-Instruct` - 更强性能
- `Qwen/Qwen2.5-72B-Instruct` - 最强性能
- `deepseek-ai/DeepSeek-V3` - DeepSeek系列

---

## 方案三：阿里云百炼【企业级】

### 3.1 开通服务

1. 访问：https://www.aliyun.com/product/bailian
2. 开通阿里云百炼服务
3. 获取API密钥

### 3.2 配置后端

```env
MCP_ENABLE_AI_TOOLS=True

OPENAI_API_KEY=sk-your-aliyun-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus  # 或 qwen-turbo, qwen-max

OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3
```

---

## 方案四：其他平台

### 4.1 智谱AI（ChatGLM）

```env
OPENAI_API_KEY=your-zhipu-api-key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
OPENAI_MODEL=glm-4
```

### 4.2 OpenAI官方（国际）

```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 或代理地址
OPENAI_MODEL=gpt-4-turbo-preview
```

---

## 配置验证

### 第一步：测试后端连接

```bash
cd "D:\Program Files\Repos\AKCNBackEnd"

# 测试AI工具是否启用
python -c "
from app.mcp.ai_tools import ai_assistant
print('AI Enabled:', ai_assistant.enabled)
print('AI Provider:', ai_assistant.provider)
print('Base URL:', ai_assistant.base_url if hasattr(ai_assistant, 'base_url') else 'N/A')
"
```

### 第二步：测试实际推理

```bash
# 测试AI报告生成
python -c "
import asyncio
from app.mcp.ai_tools import ai_assistant

async def test():
    try:
        result = await ai_assistant.generate_report({
            'total_applications': 100,
            'completed': 45,
            'in_progress': 30,
            'delayed': 15
        })
        print('AI Report Success!')
        print(result)
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test())
"
```

### 第三步：启动后端并测试API

```bash
# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 在另一个终端测试
curl http://localhost:8000/api/v1/mcp/health
```

预期返回：
```json
{
  "status": "healthy",
  "integration": "direct_api",
  "tools_count": "8",
  "ai_enabled": "true",
  "ai_provider": "openai"
}
```

### 第四步：测试AI端点

```powershell
# Windows PowerShell
curl http://localhost:8000/api/v1/mcp/ai/report `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer test-token-admin" `
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

---

## 性能对比

| 平台 | 推理速度 | 成本 | 稳定性 | 适用场景 |
|------|---------|------|--------|---------|
| **本地LM Studio** | 慢（5-20s） | 免费 | 中等 | 开发测试 |
| **矩池云（自部署）** | 快（1-3s） | 中等 | 高 | 中小企业 |
| **SiliconFlow** | 很快（0.5-2s） | 低 | 很高 | 推荐入门 |
| **阿里云百炼** | 很快（0.5-2s） | 中等 | 极高 | 企业生产 |
| **OpenAI官方** | 极快（0.3-1s） | 高 | 极高 | 需要GPT-4 |

---

## 成本估算（示例）

### SiliconFlow（推荐）

假设每天处理：
- 100次AI报告生成（每次约500 tokens）
- 200次自然语言查询（每次约300 tokens）

**月成本计算：**
```
输入tokens：(100 * 400 + 200 * 200) * 30 = 2,400,000 tokens
输出tokens：(100 * 100 + 200 * 100) * 30 = 900,000 tokens

使用Qwen2.5-7B（¥0.0007/1K tokens）：
输入成本：2,400 * 0.0007 = ¥1.68
输出成本：900 * 0.0007 = ¥0.63
月总成本：约 ¥2.31
```

### 矩池云自部署

```
RTX 4090：约 ¥2-3/小时
如果7x24小时运行：约 ¥1,440-2,160/月
适合高频使用场景
```

---

## 常见问题

### Q1: 云端API响应超时

**检查：**
```bash
# 测试网络延迟
curl -w "\nTime: %{time_total}s\n" https://api.siliconflow.cn/v1/models
```

**解决：**
- 增加 `OPENAI_TIMEOUT` 到 120 或更高
- 检查网络代理设置
- 确认API地址正确

### Q2: 提示API密钥无效

**检查：**
- 确认 `OPENAI_API_KEY` 正确复制
- 检查密钥是否过期
- 查看平台账户余额是否充足

### Q3: 模型名称错误

**检查：**
```bash
# 查看可用模型列表
curl https://api.siliconflow.cn/v1/models \
  -H "Authorization: Bearer sk-your-key"
```

### Q4: 返回内容被截断

**解决：**
在 `app/mcp/ai_tools.py` 中增加 `max_tokens`：

```python
response = await self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    max_tokens=2000,  # 增加到2000
    temperature=0.7
)
```

---

## 推荐配置

### 开发测试环境
使用 **SiliconFlow**：
- 即开即用，无需部署
- 成本极低（每月几元）
- 稳定可靠

### 生产环境（低频使用）
使用 **SiliconFlow** 或 **阿里云百炼**：
- 按量付费
- 无需维护服务器

### 生产环境（高频使用）
使用 **矩池云自部署**：
- 一次性成本
- 完全掌控
- 数据私有

---

## 下一步

配置完成后：

1. ✅ 重启后端服务
2. ✅ 测试AI功能
3. ✅ 验证前端集成
4. ✅ 监控使用量和成本
5. ✅ 根据需求调整配置

---

## 技术支持

- **矩池云文档**：https://docs.jizhulab.com/
- **SiliconFlow文档**：https://docs.siliconflow.cn/
- **vLLM文档**：https://docs.vllm.ai/

*最后更新：2025-10-20*
