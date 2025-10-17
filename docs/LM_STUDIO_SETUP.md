# LM Studio + Qwen3-4B 集成指南

## 架构概览

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│  Frontend   │ HTTP │  Backend API │ HTTP │  LM Studio  │ Tool │  MCP Tools   │
│  (Vue/React)│─────>│  (FastAPI)   │─────>│  (Qwen3-4B) │─────>│  (Database)  │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
```

## 第一步：安装和配置LM Studio

### 1.1 下载LM Studio
1. 访问 https://lmstudio.ai/
2. 下载Windows版本
3. 安装到本地（默认路径即可）

### 1.2 下载Qwen3-4B模型
1. 打开LM Studio
2. 点击左侧的 **"Search"** 图标（搜索模型）
3. 在搜索框输入：`Qwen2.5-7B` 或 `Qwen-2.5-4B`
4. 推荐选择以下模型之一：
   - `Qwen/Qwen2.5-7B-Instruct-GGUF` (7B版本，更智能)
   - `Qwen/Qwen2.5-4B-Instruct-GGUF` (4B版本，更快)
5. 点击 **Download** 下载模型
   - 选择 `Q4_K_M.gguf` 版本（平衡质量和速度）
6. 等待下载完成（大约2-5GB）

### 1.3 启动本地服务器（开发者模式）
1. 在LM Studio中，点击左侧的 **"Local Server"** 图标
2. 在顶部选择刚下载的Qwen模型
3. 配置服务器设置：
   ```
   Port: 1234 (默认，可以改)
   CORS: 启用 (Enable CORS)
   ```
4. 点击 **"Start Server"** 启动服务器
5. 确认看到提示：`Server started on http://localhost:1234`

### 1.4 测试LM Studio API
打开浏览器或使用PowerShell测试：

```powershell
# PowerShell测试命令
curl http://localhost:1234/v1/models
```

或者在浏览器访问：`http://localhost:1234/v1/models`

应该返回类似：
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen2.5-7B-Instruct-Q4_K_M",
      "object": "model",
      "created": 1234567890,
      "owned_by": "LM Studio"
    }
  ]
}
```

---

## 第二步：配置后端连接LM Studio

### 2.1 修改.env文件

打开 `D:\Program Files\Repos\AKCNBackEnd\.env`，添加或修改以下配置：

```bash
# ========================================
# LM Studio本地模型配置
# ========================================

# 启用AI工具
MCP_ENABLE_AI_TOOLS=True

# OpenAI兼容API配置（LM Studio）
OPENAI_API_KEY=lm-studio  # LM Studio不需要真实API Key，随便填
OPENAI_BASE_URL=http://localhost:1234/v1  # LM Studio的本地地址
OPENAI_MODEL=Qwen2.5-7B-Instruct-Q4_K_M  # 你下载的模型名称

# 可选：调整超时和重试
OPENAI_TIMEOUT=120  # 本地模型响应较慢，增加超时
OPENAI_MAX_RETRIES=3
```

### 2.2 验证后端配置

在后端目录运行测试：

```bash
cd "D:\Program Files\Repos\AKCNBackEnd"

# 测试AI工具是否启用
python -c "
from app.mcp.ai_tools import ai_assistant
print('AI Enabled:', ai_assistant.enabled)
print('AI Provider:', ai_assistant.provider)
"
```

应该输出：
```
AI Enabled: True
AI Provider: openai
```

### 2.3 测试AI功能

```bash
# 测试AI报告生成
python -c "
import asyncio
from app.mcp.ai_tools import ai_assistant

async def test():
    result = await ai_assistant.generate_report({
        'total_applications': 100,
        'completed': 45,
        'in_progress': 30,
        'delayed': 15
    })
    print('AI Report:', result)

asyncio.run(test())
"
```

如果配置正确，你会看到Qwen模型生成的中文报告。

---

## 第三步：启动后端服务

### 3.1 确保数据库运行

```bash
# 检查PostgreSQL是否运行
psql -h localhost -U akcn_user -d akcn_dev_db -c "SELECT 1"
```

### 3.2 启动FastAPI后端

```bash
cd "D:\Program Files\Repos\AKCNBackEnd"

# 启动后端服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.3 验证后端AI端点

打开浏览器访问：http://localhost:8000/api/v1/mcp/health

应该返回：
```json
{
  "status": "healthy",
  "integration": "direct_api",
  "tools_count": "6",
  "ai_enabled": "true",
  "ai_provider": "openai"
}
```

---

## 第四步：前端集成

### 4.1 前端环境变量配置

在前端项目中，创建或修改 `.env.development`：

```bash
# 后端API地址
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 启用AI功能
VITE_ENABLE_AI_FEATURES=true
```

### 4.2 创建AI服务模块

在前端创建 `src/services/ai.service.ts`：

```typescript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface AIReportRequest {
  data: Record<string, any>;
  report_type?: 'summary' | 'detailed' | 'executive';
  language?: 'zh' | 'en';
}

export interface AISuggestionRequest {
  context: Record<string, any>;
  focus?: 'performance' | 'quality' | 'deadline';
}

export class AIService {
  private static getHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  // 生成AI报告
  static async generateReport(request: AIReportRequest) {
    const response = await axios.post(
      `${API_BASE}/mcp/ai/report`,
      request,
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  // 获取AI建议
  static async getSuggestions(request: AISuggestionRequest) {
    const response = await axios.post(
      `${API_BASE}/mcp/ai/suggest`,
      request,
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  // 自然语言查询（带AI增强）
  static async queryWithAI(query: string) {
    const response = await axios.post(
      `${API_BASE}/mcp/query/applications`,
      { query },
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  // SQL查询分析
  static async analyzeQuery(query: string) {
    const response = await axios.post(
      `${API_BASE}/mcp/ai/analyze`,
      {
        query,
        analyze_performance: true,
        analyze_security: true
      },
      { headers: this.getHeaders() }
    );
    return response.data;
  }
}
```

### 4.3 创建AI增强组件

在前端创建 `src/components/AIDashboard.vue`（Vue示例）：

```vue
<template>
  <div class="ai-dashboard">
    <el-card>
      <template #header>
        <div class="header">
          <span>AI智能分析</span>
          <el-tag type="success" v-if="aiEnabled">AI已启用</el-tag>
        </div>
      </template>

      <!-- 统计数据 -->
      <el-row :gutter="20" v-if="stats">
        <el-col :span="6">
          <el-statistic title="总项目" :value="stats.total_applications" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已完成" :value="stats.completed" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="进行中" :value="stats.in_progress" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="延期" :value="stats.delayed" />
        </el-col>
      </el-row>

      <!-- 操作按钮 -->
      <div class="actions mt-4">
        <el-button
          type="primary"
          @click="generateAIReport"
          :loading="loading"
        >
          生成AI报告
        </el-button>
        <el-button
          @click="getAISuggestions"
          :loading="loading"
        >
          获取AI建议
        </el-button>
      </div>

      <!-- AI报告 -->
      <el-alert
        v-if="aiReport"
        title="AI分析报告"
        type="info"
        :description="aiReport"
        class="mt-4"
        :closable="false"
      />

      <!-- AI建议 -->
      <div v-if="suggestions" class="mt-4">
        <h4>AI智能建议</h4>
        <el-alert
          v-for="(action, index) in suggestions.priority_actions"
          :key="index"
          :title="action"
          type="warning"
          class="mb-2"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { AIService } from '@/services/ai.service';

const aiEnabled = ref(true);
const loading = ref(false);
const stats = ref<any>(null);
const aiReport = ref<string>('');
const suggestions = ref<any>(null);

onMounted(async () => {
  await loadStats();
});

const loadStats = async () => {
  // 从API获取统计数据
  stats.value = {
    total_applications: 100,
    completed: 45,
    in_progress: 30,
    delayed: 15
  };
};

const generateAIReport = async () => {
  loading.value = true;
  try {
    const result = await AIService.generateReport({
      data: stats.value,
      report_type: 'summary',
      language: 'zh'
    });

    if (result.success) {
      aiReport.value = result.report;
    }
  } catch (error) {
    console.error('生成报告失败:', error);
  } finally {
    loading.value = false;
  }
};

const getAISuggestions = async () => {
  loading.value = true;
  try {
    const result = await AIService.getSuggestions({
      context: {
        stats: stats.value,
        delayed_count: stats.value.delayed
      },
      focus: 'deadline'
    });

    if (result.success) {
      suggestions.value = result;
    }
  } catch (error) {
    console.error('获取建议失败:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.ai-dashboard {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 10px;
}
</style>
```

---

## 第五步：测试完整流程

### 5.1 检查清单

确保以下服务都在运行：

- [ ] LM Studio服务器运行在 http://localhost:1234
- [ ] Qwen模型已加载
- [ ] PostgreSQL数据库运行
- [ ] 后端FastAPI运行在 http://localhost:8000
- [ ] 前端开发服务器运行（通常是 http://localhost:3000）

### 5.2 测试AI功能

1. **测试后端AI健康检查**
   ```bash
   curl http://localhost:8000/api/v1/mcp/health
   ```

2. **测试AI报告生成**
   打开Postman或使用curl：
   ```bash
   curl -X POST http://localhost:8000/api/v1/mcp/ai/report \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer test-token-admin" \
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

3. **测试前端集成**
   - 登录前端应用
   - 打开AI仪表盘
   - 点击"生成AI报告"按钮
   - 应该能看到Qwen生成的中文报告

---

## 常见问题排查

### Q1: LM Studio返回连接错误

**检查：**
```bash
# 测试LM Studio是否运行
curl http://localhost:1234/v1/models
```

**解决：**
- 确保LM Studio的Local Server已启动
- 检查端口1234是否被占用
- 在LM Studio中重启服务器

### Q2: 后端显示AI未启用

**检查：**
```bash
python -c "from app.mcp.ai_tools import ai_assistant; print(ai_assistant.enabled)"
```

**解决：**
- 确保.env中 `MCP_ENABLE_AI_TOOLS=True`
- 确保 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 配置正确
- 重启后端服务

### Q3: AI响应很慢

**优化：**
1. 在LM Studio中降低模型大小（使用4B而不是7B）
2. 调整.env中的超时设置：`OPENAI_TIMEOUT=180`
3. 在LM Studio设置中调整：
   - GPU Offload: 增加到最大
   - Context Length: 降低到2048

### Q4: 前端无法连接后端

**检查：**
- 后端CORS配置：`.env` 中的 `ALLOWED_ORIGINS`
- 前端API地址：`.env.development` 中的 `VITE_API_BASE_URL`
- 浏览器控制台是否有CORS错误

---

## 性能优化建议

### LM Studio优化
1. **GPU加速**：在LM Studio设置中启用GPU
2. **模型量化**：使用Q4_K_M版本（平衡速度和质量）
3. **上下文长度**：设置为2048（除非需要更长）

### 后端优化
1. **异步处理**：AI调用已经是异步的
2. **缓存结果**：可以缓存常见查询的AI报告
3. **超时控制**：设置合理的超时时间

### 前端优化
1. **Loading状态**：显示加载提示
2. **降级方案**：AI失败时显示基础数据
3. **可选启用**：允许用户禁用AI功能

---

## 成本和资源

### 免费方案（LM Studio本地）
- **成本**: 完全免费
- **资源需求**:
  - RAM: 至少8GB（推荐16GB）
  - GPU: NVIDIA显卡（推荐，非必需）
  - 存储: 5-10GB（模型文件）

### 升级选项
如果本地性能不够，可以升级到：
1. **Ollama**: 另一个本地模型服务器
2. **OpenAI API**: 付费但更快更智能
3. **Azure OpenAI**: 企业级方案

---

## 下一步

配置完成后，你可以：

1. ✅ 在前端使用自然语言查询数据
2. ✅ 生成AI驱动的项目报告
3. ✅ 获取智能化的管理建议
4. ✅ AI辅助的SQL查询分析

---

**需要帮助?**
- 查看日志：后端 `logs/app.log`
- LM Studio日志：在LM Studio界面的Console标签
- 前端控制台：浏览器F12开发者工具

*最后更新: 2025-10-16*
