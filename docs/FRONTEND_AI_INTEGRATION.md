# 前端AI增强集成指南

本文档说明如何在前端集成MCP AI增强功能。

## 目录
1. [基础API调用](#基础api调用)
2. [TypeScript类型定义](#typescript类型定义)
3. [React集成示例](#react集成示例)
4. [Vue集成示例](#vue集成示例)
5. [实际应用场景](#实际应用场景)

---

## 基础API调用

### 1. 自然语言查询（带AI增强）

```typescript
// POST /api/v1/mcp/query/applications
const response = await fetch('/api/v1/mcp/query/applications', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: '显示所有延期的项目'
  })
});

const result = await response.json();
/*
{
  "success": true,
  "result": { ... },  // 查询结果
  "query_interpretation": "执行工具: app_list, 参数: ...",
  "ai_report": "根据查询结果，当前有15个项目处于延期状态...",  // AI生成报告
  "ai_suggestions": {  // AI建议
    "success": true,
    "suggestions": "建议优先处理...",
    "reasoning": "..."
  }
}
*/
```

### 2. AI报告生成

```typescript
// POST /api/v1/mcp/ai/report
const response = await fetch('/api/v1/mcp/ai/report', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    data: {
      total_applications: 100,
      completed: 45,
      in_progress: 30,
      delayed: 15
    },
    report_type: 'summary',
    language: 'zh'
  })
});

const result = await response.json();
/*
{
  "success": true,
  "report": "项目管理概况报告：\n目前共有100个应用项目...",
  "metadata": {
    "report_type": "summary",
    "language": "zh",
    "generated_at": "2024-12-10T10:30:00",
    "provider": "openai"
  }
}
*/
```

### 3. AI智能建议

```typescript
// POST /api/v1/mcp/ai/suggest
const response = await fetch('/api/v1/mcp/ai/suggest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    context: {
      project_status: 'behind_schedule',
      delayed_tasks: 15,
      team_capacity: '80%'
    },
    focus: 'deadline'
  })
});

const result = await response.json();
/*
{
  "success": true,
  "suggestions": [...],
  "priority_actions": [
    "优先处理延期最严重的3个项目",
    "增加资源到关键路径任务"
  ],
  "reasoning": "基于当前项目进度和团队负载分析..."
}
*/
```

### 4. SQL查询AI分析

```typescript
// POST /api/v1/mcp/ai/analyze
const response = await fetch('/api/v1/mcp/ai/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: 'SELECT * FROM applications WHERE status = "DELAYED"',
    analyze_performance: true,
    analyze_security: true
  })
});

const result = await response.json();
/*
{
  "success": true,
  "analysis": {
    "original_query": "...",
    "analysis_text": "查询分析：该查询会扫描全表..."
  },
  "recommendations": [
    "建议在status字段添加索引",
    "考虑限制返回结果数量"
  ],
  "warnings": []
}
*/
```

---

## TypeScript类型定义

创建 `src/types/mcp.ts`：

```typescript
// MCP基础类型
export interface MCPExecuteRequest {
  tool_name: string;
  arguments: Record<string, any>;
}

export interface MCPExecuteResponse<T = any> {
  success: boolean;
  result: T | null;
  execution_time?: number;
  error?: string;
}

// 自然语言查询
export interface MCPQueryRequest {
  query: string;
}

export interface MCPQueryResponse<T = any> {
  success: boolean;
  result: T;
  query_interpretation?: string;
  ai_report?: string;  // AI生成的报告
  ai_suggestions?: AISuggestions;  // AI建议
}

// AI增强类型
export interface AIReportRequest {
  data: Record<string, any>;
  report_type?: 'summary' | 'detailed' | 'executive';
  language?: 'zh' | 'en';
}

export interface AIReportResponse {
  success: boolean;
  report?: string;
  metadata?: {
    report_type: string;
    language: string;
    generated_at: string;
    provider: string;
  };
  error?: string;
}

export interface AISuggestionRequest {
  context: Record<string, any>;
  focus?: 'performance' | 'quality' | 'deadline';
}

export interface AISuggestions {
  success: boolean;
  suggestions: Array<{
    action: string;
    priority: 'high' | 'medium' | 'low';
    impact: string;
    tool?: string;
  }>;
  priority_actions: string[];
  reasoning?: string;
  error?: string;
}

export interface AIAnalysisRequest {
  query: string;
  analyze_performance?: boolean;
  analyze_security?: boolean;
}

export interface AIAnalysisResponse {
  success: boolean;
  analysis?: {
    original_query: string;
    analysis_text: string;
  };
  recommendations: string[];
  warnings: string[];
  error?: string;
}
```

---

## React集成示例

### 1. AI增强Hook

创建 `src/hooks/useAIEnhanced.ts`：

```typescript
import { useState, useCallback } from 'react';
import { api } from '@/api';
import type { MCPQueryResponse, AIReportResponse, AISuggestions } from '@/types/mcp';

export function useAIEnhanced(authToken: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 自然语言查询（带AI增强）
  const queryWithAI = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/mcp/query/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ query })
      });

      const data: MCPQueryResponse = await response.json();

      if (!data.success) {
        throw new Error(data.query_interpretation || 'Query failed');
      }

      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // 生成AI报告
  const generateReport = useCallback(async (
    data: Record<string, any>,
    options?: { reportType?: string; language?: string }
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/mcp/ai/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          data,
          report_type: options?.reportType || 'summary',
          language: options?.language || 'zh'
        })
      });

      const result: AIReportResponse = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Report generation failed');
      }

      return result;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // 获取AI建议
  const getSuggestions = useCallback(async (
    context: Record<string, any>,
    focus?: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/mcp/ai/suggest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ context, focus })
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Suggestion generation failed');
      }

      return result;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  return {
    loading,
    error,
    queryWithAI,
    generateReport,
    getSuggestions
  };
}
```

### 2. AI增强Dashboard组件

```typescript
import React, { useEffect, useState } from 'react';
import { useAIEnhanced } from '@/hooks/useAIEnhanced';
import { Card, Button, Alert, Spin, Typography } from 'antd';

const { Title, Paragraph } = Typography;

interface DashboardStats {
  total_applications: number;
  completed: number;
  in_progress: number;
  delayed: number;
}

export function AIDashboard() {
  const { loading, error, generateReport, getSuggestions } = useAIEnhanced(
    localStorage.getItem('token') || ''
  );

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [aiReport, setAiReport] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<any>(null);

  // 加载统计数据
  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    // 调用普通API获取统计数据
    const response = await fetch('/api/v1/mcp/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        tool_name: 'dashboard_stats',
        arguments: { stat_type: 'summary' }
      })
    });

    const result = await response.json();
    if (result.success) {
      setStats(result.result);
    }
  };

  // 生成AI报告
  const handleGenerateReport = async () => {
    if (!stats) return;

    try {
      const result = await generateReport(stats);
      setAiReport(result.report || null);
    } catch (err) {
      console.error('Failed to generate report:', err);
    }
  };

  // 获取AI建议
  const handleGetSuggestions = async () => {
    if (!stats) return;

    try {
      const result = await getSuggestions({
        stats,
        delayed_count: stats.delayed
      }, 'deadline');
      setSuggestions(result);
    } catch (err) {
      console.error('Failed to get suggestions:', err);
    }
  };

  return (
    <div className="ai-dashboard">
      <Title level={2}>AI增强仪表盘</Title>

      {error && <Alert type="error" message={error} closable />}

      {/* 统计数据 */}
      {stats && (
        <Card title="项目概况">
          <div className="stats-grid">
            <div>总项目数: {stats.total_applications}</div>
            <div>已完成: {stats.completed}</div>
            <div>进行中: {stats.in_progress}</div>
            <div>延期: {stats.delayed}</div>
          </div>

          <div className="action-buttons">
            <Button
              type="primary"
              onClick={handleGenerateReport}
              loading={loading}
            >
              生成AI报告
            </Button>
            <Button
              onClick={handleGetSuggestions}
              loading={loading}
            >
              获取AI建议
            </Button>
          </div>
        </Card>
      )}

      {/* AI报告 */}
      {aiReport && (
        <Card title="AI分析报告" className="mt-4">
          <Paragraph>{aiReport}</Paragraph>
        </Card>
      )}

      {/* AI建议 */}
      {suggestions && (
        <Card title="AI智能建议" className="mt-4">
          {suggestions.priority_actions?.map((action: string, index: number) => (
            <Alert
              key={index}
              type="info"
              message={action}
              className="mb-2"
            />
          ))}
          {suggestions.reasoning && (
            <Paragraph className="mt-4">
              <strong>分析说明：</strong>
              {suggestions.reasoning}
            </Paragraph>
          )}
        </Card>
      )}
    </div>
  );
}
```

### 3. AI聊天查询组件

```typescript
import React, { useState } from 'react';
import { Input, Button, Card, List, Tag } from 'antd';
import { useAIEnhanced } from '@/hooks/useAIEnhanced';

export function AIQueryChat() {
  const { loading, queryWithAI } = useAIEnhanced(
    localStorage.getItem('token') || ''
  );

  const [query, setQuery] = useState('');
  const [history, setHistory] = useState<any[]>([]);

  const handleQuery = async () => {
    if (!query.trim()) return;

    try {
      const result = await queryWithAI(query);

      setHistory([
        ...history,
        {
          query,
          result: result.result,
          interpretation: result.query_interpretation,
          aiReport: result.ai_report,
          aiSuggestions: result.ai_suggestions,
          timestamp: new Date()
        }
      ]);

      setQuery('');
    } catch (err) {
      console.error('Query failed:', err);
    }
  };

  return (
    <div className="ai-query-chat">
      <Card title="AI智能查询">
        {/* 输入框 */}
        <Input.Search
          placeholder="用自然语言描述您的查询，如：显示所有延期的项目"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onSearch={handleQuery}
          loading={loading}
          enterButton="查询"
          size="large"
        />

        {/* 查询历史 */}
        <List
          className="mt-4"
          dataSource={history}
          renderItem={(item) => (
            <List.Item>
              <Card className="w-full">
                <div className="query-item">
                  <Tag color="blue">查询</Tag>
                  <span>{item.query}</span>
                </div>

                {/* 查询结果 */}
                <div className="mt-2">
                  <Tag>结果数量</Tag>
                  {item.result?.count || 0} 条
                </div>

                {/* AI报告 */}
                {item.aiReport && (
                  <div className="mt-3 p-3 bg-blue-50 rounded">
                    <strong>AI分析:</strong>
                    <p className="mt-2">{item.aiReport}</p>
                  </div>
                )}

                {/* AI建议 */}
                {item.aiSuggestions?.reasoning && (
                  <div className="mt-3 p-3 bg-green-50 rounded">
                    <strong>AI建议:</strong>
                    <p className="mt-2">{item.aiSuggestions.reasoning}</p>
                  </div>
                )}
              </Card>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}
```

---

## Vue集成示例

### 1. Composable

创建 `src/composables/useAIEnhanced.ts`：

```typescript
import { ref, computed } from 'vue';
import type { Ref } from 'vue';

export function useAIEnhanced() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  const queryWithAI = async (query: string) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/v1/mcp/query/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ query })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.query_interpretation || 'Query failed');
      }

      return data;
    } catch (err: any) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const generateReport = async (
    data: Record<string, any>,
    options?: { reportType?: string; language?: string }
  ) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/v1/mcp/ai/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          data,
          report_type: options?.reportType || 'summary',
          language: options?.language || 'zh'
        })
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Report generation failed');
      }

      return result;
    } catch (err: any) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    queryWithAI,
    generateReport
  };
}
```

### 2. Vue组件示例

```vue
<template>
  <div class="ai-dashboard">
    <h2>AI增强仪表盘</h2>

    <!-- 统计数据 -->
    <el-card v-if="stats">
      <template #header>
        <div class="card-header">
          <span>项目概况</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总项目数" :value="stats.total_applications" />
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

      <div class="action-buttons mt-4">
        <el-button type="primary" @click="handleGenerateReport" :loading="loading">
          生成AI报告
        </el-button>
        <el-button @click="handleGetSuggestions" :loading="loading">
          获取AI建议
        </el-button>
      </div>
    </el-card>

    <!-- AI报告 -->
    <el-card v-if="aiReport" class="mt-4">
      <template #header>AI分析报告</template>
      <p>{{ aiReport }}</p>
    </el-card>

    <!-- AI建议 -->
    <el-card v-if="suggestions" class="mt-4">
      <template #header>AI智能建议</template>
      <el-alert
        v-for="(action, index) in suggestions.priority_actions"
        :key="index"
        :title="action"
        type="info"
        :closable="false"
        class="mb-2"
      />
      <p v-if="suggestions.reasoning" class="mt-4">
        <strong>分析说明：</strong>{{ suggestions.reasoning }}
      </p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAIEnhanced } from '@/composables/useAIEnhanced';

const { loading, error, generateReport } = useAIEnhanced();

const stats = ref(null);
const aiReport = ref<string | null>(null);
const suggestions = ref(null);

onMounted(() => {
  fetchDashboardStats();
});

const fetchDashboardStats = async () => {
  // 实现获取统计数据的逻辑
};

const handleGenerateReport = async () => {
  if (!stats.value) return;

  try {
    const result = await generateReport(stats.value);
    aiReport.value = result.report;
  } catch (err) {
    console.error('Failed to generate report:', err);
  }
};

const handleGetSuggestions = async () => {
  // 实现获取建议的逻辑
};
</script>
```

---

## 实际应用场景

### 场景1：项目延期智能分析

```typescript
// 1. 查询延期项目
const result = await queryWithAI('显示所有延期超过30天的项目');

// 2. 生成详细报告
const report = await generateReport(result.result, {
  reportType: 'detailed',
  language: 'zh'
});

// 3. 获取改进建议
const suggestions = await getSuggestions({
  delayed_projects: result.result,
  threshold: 30
}, 'deadline');
```

### 场景2：团队绩效分析

```typescript
// 查询团队数据
const teamStats = await queryWithAI('显示开发团队A的项目完成情况');

// 生成团队报告
const teamReport = await generateReport({
  team_name: '开发团队A',
  ...teamStats.result
}, {
  reportType: 'executive',
  language: 'zh'
});
```

### 场景3：智能查询助手

```typescript
// 用户可以用自然语言查询
const queries = [
  '哪些项目需要立即关注？',
  '本月完成了多少项目？',
  '哪个团队效率最高？',
  '云原生改造进度如何？'
];

for (const query of queries) {
  const result = await queryWithAI(query);
  console.log(result.ai_report); // AI自动生成的分析
}
```

---

## 注意事项

1. **API Key配置**：确保后端已正确配置AI服务（.env中的MCP_ENABLE_AI_TOOLS=True）
2. **错误处理**：AI服务可能失败，应有降级方案（返回基础数据）
3. **性能考虑**：AI调用较慢，建议：
   - 使用loading状态
   - 可选启用/禁用AI
   - 缓存AI结果
4. **成本控制**：
   - 监控API调用次数
   - 为高频用户考虑本地模型
   - 实现调用频率限制

---

*最后更新：2024-12-10*
