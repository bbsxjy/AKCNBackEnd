# 流式响应使用指南

## 概述

系统现在支持流式响应（Streaming Response），AI的回答会逐字显示，就像ChatGPT一样！

**优势**:
- ✅ 即时反馈 - 用户立即看到响应开始
- ✅ 更好的用户体验 - 感觉更快、更自然
- ✅ 进度透明 - 实时看到AI生成过程
- ✅ 降低感知延迟 - 不需要等待完整响应

## API端点

### 1. 流式自然语言查询

**端点**: `POST /api/v1/mcp/query/applications/stream`

**响应格式**: Server-Sent Events (SSE / text/event-stream)

**事件类型**:
- `status`: 状态更新
- `data`: 查询结果数据
- `ai_chunk`: AI响应文本片段（逐字输出）
- `done`: 完成信号
- `error`: 错误信息

## 前端实现示例

### JavaScript / TypeScript (原生)

```javascript
/**
 * 流式查询函数 - 使用EventSource API
 */
async function streamingQuery(query, token, callbacks) {
    const response = await fetch('/api/v1/mcp/query/applications/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
            if (line.startswith('event: ')) {
                const eventType = line.substring(7);
                continue;
            }
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.substring(6));

                // 根据事件类型调用相应的回调
                if (data.phase === 'parsing') {
                    callbacks.onParsing?.(data);
                } else if (data.phase === 'executing') {
                    callbacks.onExecuting?.(data);
                } else if (data.phase === 'generating') {
                    callbacks.onGenerating?.(data);
                } else if (data.content) {
                    // AI响应片段
                    callbacks.onChunk?.(data.content);
                } else if (data.result) {
                    // 查询结果
                    callbacks.onData?.(data.result);
                } else if (data.success !== undefined) {
                    // 完成
                    callbacks.onDone?.(data);
                } else if (data.error) {
                    // 错误
                    callbacks.onError?.(data.error);
                }
            }
        }
    }
}

/**
 * 使用示例
 */
const aiResponseDiv = document.getElementById('ai-response');
let fullResponse = '';

streamingQuery(
    '查询应用ID为CI123456的详情',
    'your-jwt-token',
    {
        onParsing: (data) => {
            console.log('正在解析:', data.message);
            statusDiv.textContent = data.message;
        },
        onExecuting: (data) => {
            console.log('正在执行:', data.message);
            statusDiv.textContent = data.message;
        },
        onGenerating: (data) => {
            console.log('正在生成报告...');
            statusDiv.textContent = data.message;
        },
        onData: (result) => {
            console.log('查询结果:', result);
            // 显示查询结果
            dataDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        },
        onChunk: (content) => {
            // 逐字显示AI响应
            fullResponse += content;
            aiResponseDiv.textContent = fullResponse;

            // 自动滚动到底部
            aiResponseDiv.scrollTop = aiResponseDiv.scrollHeight;
        },
        onDone: (data) => {
            console.log('完成:', data);
            statusDiv.textContent = '查询完成';
        },
        onError: (error) => {
            console.error('错误:', error);
            errorDiv.textContent = error;
        }
    }
);
```

### React Hook 示例

```typescript
import { useState, useEffect } from 'react';

interface StreamingCallbacks {
    onParsing?: (data: any) => void;
    onExecuting?: (data: any) => void;
    onGenerating?: (data: any) => void;
    onData?: (result: any) => void;
    onChunk?: (content: string) => void;
    onDone?: (data: any) => void;
    onError?: (error: string) => void;
}

function useStreamingQuery() {
    const [status, setStatus] = useState('');
    const [result, setResult] = useState(null);
    const [aiResponse, setAiResponse] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const query = async (queryText: string, token: string) => {
        setLoading(true);
        setAiResponse('');
        setError('');
        let fullResponse = '';

        try {
            const response = await fetch('/api/v1/mcp/query/applications/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ query: queryText })
            });

            const reader = response.body!.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.substring(6));

                        if (data.phase) {
                            setStatus(data.message || data.phase);
                        } else if (data.content) {
                            fullResponse += data.content;
                            setAiResponse(fullResponse);
                        } else if (data.result) {
                            setResult(data.result);
                        } else if (data.success !== undefined) {
                            setStatus(data.success ? '完成' : '失败');
                            setLoading(false);
                        } else if (data.error) {
                            setError(data.error);
                            setLoading(false);
                        }
                    }
                }
            }
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    return { query, status, result, aiResponse, loading, error };
}

// 组件使用示例
function AIQueryComponent() {
    const { query, status, result, aiResponse, loading, error } = useStreamingQuery();
    const [queryText, setQueryText] = useState('');

    const handleSubmit = () => {
        const token = localStorage.getItem('token');
        query(queryText, token);
    };

    return (
        <div className="ai-query-panel">
            <div className="input-section">
                <textarea
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    placeholder="输入查询，例如：查询应用ID为CI123456的详情"
                />
                <button onClick={handleSubmit} disabled={loading}>
                    {loading ? '查询中...' : '查询'}
                </button>
            </div>

            {status && <div className="status">{status}</div>}

            {result && (
                <div className="result">
                    <h3>查询结果</h3>
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
            )}

            {aiResponse && (
                <div className="ai-response">
                    <h3>AI分析</h3>
                    <div className="response-text">{aiResponse}</div>
                </div>
            )}

            {error && <div className="error">{error}</div>}
        </div>
    );
}
```

### Vue 3 示例

```vue
<template>
  <div class="ai-query-panel">
    <div class="input-section">
      <textarea
        v-model="queryText"
        placeholder="输入查询，例如：查询应用ID为CI123456的详情"
      ></textarea>
      <button @click="handleQuery" :disabled="loading">
        {{ loading ? '查询中...' : '查询' }}
      </button>
    </div>

    <div v-if="status" class="status">{{ status }}</div>

    <div v-if="result" class="result">
      <h3>查询结果</h3>
      <pre>{{ JSON.stringify(result, null, 2) }}</pre>
    </div>

    <div v-if="aiResponse" class="ai-response">
      <h3>AI分析</h3>
      <div class="response-text">{{ aiResponse }}</div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const queryText = ref('');
const status = ref('');
const result = ref(null);
const aiResponse = ref('');
const loading = ref(false);
const error = ref('');

const handleQuery = async () => {
    loading.value = true;
    aiResponse.value = '';
    error.value = '';
    let fullResponse = '';

    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/v1/mcp/query/applications/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ query: queryText.value })
        });

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));

                    if (data.phase) {
                        status.value = data.message || data.phase;
                    } else if (data.content) {
                        fullResponse += data.content;
                        aiResponse.value = fullResponse;
                    } else if (data.result) {
                        result.value = data.result;
                    } else if (data.success !== undefined) {
                        status.value = data.success ? '完成' : '失败';
                        loading.value = false;
                    } else if (data.error) {
                        error.value = data.error;
                        loading.value = false;
                    }
                }
            }
        }
    } catch (err) {
        error.value = err.message;
        loading.value = false;
    }
};
</script>

<style scoped>
.ai-query-panel {
    padding: 20px;
}

.input-section textarea {
    width: 100%;
    height: 100px;
    margin-bottom: 10px;
}

.status {
    color: #666;
    margin: 10px 0;
}

.ai-response {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 8px;
    white-space: pre-wrap;
    line-height: 1.6;
}

.error {
    color: red;
    padding: 10px;
    background: #ffebee;
    border-radius: 4px;
}
</style>
```

## 样式建议

### CSS动画 - 打字机效果

```css
.ai-response {
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 光标闪烁效果（当AI正在生成时） */
.ai-response.generating::after {
    content: '|';
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
```

## 测试命令

### curl测试

```bash
# 基本测试
curl -N -H "Authorization: Bearer token_1_admin_full_access_test_2024" \
     -H "Content-Type: application/json" \
     -d '{"query":"查询应用ID为CI123456的详情"}' \
     http://localhost:8000/api/v1/mcp/query/applications/stream

# 查看所有事件
curl -N -H "Authorization: Bearer token_1_admin_full_access_test_2024" \
     -H "Content-Type: application/json" \
     -d '{"query":"列出所有延期的应用"}' \
     http://localhost:8000/api/v1/mcp/query/applications/stream
```

## 性能考虑

### 1. 连接管理
- SSE连接是长连接，注意控制并发数
- 建议每个用户同时最多1-2个SSE连接

### 2. 缓冲控制
- 确保nginx配置中禁用缓冲：
```nginx
location /api/v1/mcp/ {
    proxy_pass http://backend;
    proxy_buffering off;  # 重要！
    proxy_cache off;
    proxy_set_header X-Accel-Buffering no;
}
```

### 3. 超时设置
- 默认超时：120秒
- 可在nginx中调整：
```nginx
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
```

## 故障排除

### 问题1: 响应不流畅，卡顿

**原因**: 可能是nginx或其他代理在缓冲响应

**解决**:
```nginx
# 在nginx配置中添加
proxy_buffering off;
proxy_cache off;
proxy_set_header X-Accel-Buffering no;
```

### 问题2: 连接突然断开

**原因**: 超时设置太短

**解决**:
```python
# 在streaming endpoint中添加定期心跳
async def event_generator():
    last_ping = time.time()
    async for chunk in ai_assistant._call_llm_stream(prompt):
        yield f"event: ai_chunk\ndata: {json.dumps({'content': chunk})}\n\n"

        # 每30秒发送心跳
        if time.time() - last_ping > 30:
            yield f": ping\n\n"
            last_ping = time.time()
```

### 问题3: 中文显示乱码

**原因**: 字符编码问题

**解决**:
- 确保使用 `ensure_ascii=False` 在JSON序列化时
- 设置正确的Content-Type header

## 对比：流式 vs 非流式

| 特性 | 非流式响应 | 流式响应 |
|------|-----------|----------|
| 首字节时间 | 等待完整生成 (10-30秒) | 立即开始 (<1秒) |
| 用户体验 | 长时间等待 | 实时看到进度 |
| 感知速度 | 慢 | 快 |
| 实现复杂度 | 简单 | 中等 |
| 服务器压力 | 相同 | 相同 |
| 带宽使用 | 相同 | 相同 |

## 最佳实践

1. **始终显示状态** - 让用户知道正在发生什么
2. **优雅降级** - 如果SSE不可用，回退到普通请求
3. **错误处理** - 处理网络中断、超时等情况
4. **自动重连** - 连接断开时自动重试
5. **用户反馈** - 提供停止按钮让用户可以中断

## 示例项目

完整的示例项目位于：
- React: `examples/react-streaming-query/`
- Vue: `examples/vue-streaming-query/`
- Vanilla JS: `examples/vanilla-streaming-query/`

---

**维护者**: AKCN项目管理系统开发团队
**最后更新**: 2025-10-16
