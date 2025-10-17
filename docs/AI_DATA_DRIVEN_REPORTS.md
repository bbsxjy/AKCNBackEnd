# AI数据驱动的智能报告生成

## 概述

本系统现在支持**基于实际SQL查询数据的智能报告生成**,而不是简单的模板化报告。AI会深入分析查询结果,提取关键统计信息、识别异常模式,并生成专业的数据解读报告。

## 核心特性

### 1. 数据驱动分析
- ✅ **自动统计分析**: 对数值列计算平均值、中位数、标准差等
- ✅ **分类数据分布**: 分析状态、团队等分类字段的分布情况
- ✅ **异常检测**: 自动识别超过2倍标准差的异常值
- ✅ **智能洞察**: 基于实际数据生成可读性强的关键发现

### 2. 上下文感知
- 识别SQL查询意图(聚合/分组/列表查询等)
- 根据字段名称智能解读数据(进度/延期/团队等)
- 结合业务场景生成专业建议

### 3. AI增强报告
- 使用LLM生成自然语言叙述
- 包含执行摘要、详细分析、趋势判断、行动建议
- 支持中文专业报告

## 使用方法

### 方法1: 自然语言查询 (推荐)

**端点**: `POST /api/v1/mcp/query/applications`

```python
import httpx

# 使用自然语言查询,系统会自动生成SQL并分析数据
async def get_team_performance_report():
    response = await httpx.post(
        "http://localhost:8000/api/v1/mcp/query/applications",
        json={"query": "各个团队的平均进度和延期情况"},
        headers={"Authorization": f"Bearer {token}"}
    )

    result = response.json()

    # 获取AI生成的报告
    print("=== AI智能报告 ===")
    print(result["ai_report"])

    # 获取数据洞察
    print("\n=== 查询解析 ===")
    print(result["query_interpretation"])

    # 获取原始数据
    print("\n=== 原始数据 ===")
    print(result["result"])
```

**示例输出**:
```
=== AI智能报告 ===
## 执行摘要
本次查询分析了5个开发团队的转型项目进展情况。数据显示团队A表现最佳,平均进度达85%,而团队C存在较多延期项目,需要重点关注。

## 详细分析
### 进度情况
- 团队A: 平均进度85.2%,共12个项目,全部按计划推进
- 团队B: 平均进度72.5%,共8个项目,2个轻微延期(3-5天)
- 团队C: 平均进度58.3%,共15个项目,5个严重延期(超过30天)
- 团队D: 平均进度79.1%,共10个项目,1个中等延期(15天)
- 团队E: 平均进度67.8%,共7个项目,3个轻微延期(5-8天)

### 异常情况
发现3个项目延期超过60天,均在团队C,需要紧急协调资源。

## 趋势判断
整体进度良好(平均72.6%),但团队间差异较大。团队C的延期问题需要管理层重点介入。

## 行动建议
1. 立即组织团队C的延期项目评审会议,识别根本原因
2. 从团队A抽调1-2名骨干支援团队C的关键项目
3. 建立每周进度审查机制,重点关注延期超过7天的项目
4. 分享团队A的最佳实践到其他团队
5. 评估团队C的资源配置是否合理,考虑增加人力或调整项目优先级

=== 关键洞察 ===
- 查询返回5条记录
- progress_percentage平均值为72.6%, 中位数为72.5%, 范围从58.3%到85.2%
- delayed_count总计11个(平均), 最多5个
- dev_team分布: 团队C占比最高(28.8%), 共5种状态
```

### 方法2: 直接使用报告服务

```python
from app.services.ai_report_service import generate_intelligent_report

# 执行SQL查询
query = """
SELECT dev_team,
       AVG(progress_percentage) as avg_progress,
       COUNT(*) as total_apps,
       SUM(CASE WHEN is_delayed THEN 1 ELSE 0 END) as delayed_count
FROM applications
WHERE ak_supervision_acceptance_year = 2024
GROUP BY dev_team
ORDER BY avg_progress DESC
"""

results = await execute_sql_query(query)

# 生成智能报告
report = await generate_intelligent_report(
    query=query,
    results=results,
    context={
        "user_intent": "团队绩效分析",
        "time_period": "2024年"
    }
)

# 获取报告内容
print("数据摘要:", report["data_summary"])
print("统计信息:", report["statistics"])
print("关键洞察:", report["insights"])
print("异常数据:", report["anomalies"])
print("AI报告:", report["ai_narrative"])
```

### 方法3: 流式报告生成 (实时输出)

**端点**: `POST /api/v1/mcp/query/applications/stream`

```python
import httpx

async def stream_intelligent_report():
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/mcp/query/applications/stream",
            json={"query": "分析本月延期项目的原因"},
            headers={"Authorization": f"Bearer {token}"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    data = json.loads(data_str)

                    # 实时打印AI生成的内容
                    if "content" in data:
                        print(data["content"], end="", flush=True)
```

## 报告结构

### 1. 数据摘要 (data_summary)
```json
{
    "total_rows": 25,
    "total_columns": 5,
    "columns": ["dev_team", "avg_progress", "total_apps", "delayed_count", "completion_rate"]
}
```

### 2. 统计信息 (statistics)

**数值统计**:
```json
{
    "numeric": {
        "avg_progress": {
            "count": 5,
            "min": 58.3,
            "max": 85.2,
            "mean": 72.58,
            "median": 72.5,
            "std_dev": 10.2
        },
        "delayed_count": {
            "count": 5,
            "min": 0,
            "max": 5,
            "mean": 2.2,
            "median": 2.0
        }
    }
}
```

**分类统计**:
```json
{
    "categorical": {
        "dev_team": {
            "unique_values": 5,
            "total_count": 52,
            "distribution": {
                "团队A": {"count": 12, "percentage": 23.1},
                "团队B": {"count": 8, "percentage": 15.4},
                "团队C": {"count": 15, "percentage": 28.8}
            },
            "most_common": "团队C",
            "least_common": "团队E"
        }
    }
}
```

### 3. 关键洞察 (insights)
```json
[
    "查询返回5条记录",
    "progress_percentage平均值为72.6%, 中位数为72.5%, 范围从58.3%到85.2%",
    "delayed_count平均为2.2天, 最长延期5天",
    "涉及5个团队, 团队C团队项目最多(28.8%)"
]
```

### 4. 异常数据 (anomalies)
```json
[
    {
        "type": "outlier",
        "column": "delayed_count",
        "description": "delayed_count列发现1个异常值(超过2倍标准差)",
        "values": [5]
    }
]
```

### 5. AI叙述报告 (ai_narrative)
完整的中文专业报告,包含:
- **执行摘要**: 2-3句话的核心发现
- **详细分析**: 基于实际数据的深度解读
- **趋势判断**: 积极/需要关注/警示
- **行动建议**: 3-5条具体、可执行的改进措施

## 实际应用场景

### 场景1: 项目进度分析

**查询**: "分析各团队的项目进度分布"

**生成的报告会包含**:
- 各团队平均进度对比
- 进度区间分布(0-25%, 26-50%, 51-75%, 76-100%)
- 识别进度滞后的团队
- 提供针对性的改进建议

### 场景2: 延期问题诊断

**查询**: "查找延期超过30天的项目并分析原因"

**生成的报告会包含**:
- 延期项目数量和严重程度分类
- 团队延期分布情况
- 常见延期阶段(需求、开发、测试、上线)
- 被阻塞的子任务分析
- 资源协调建议

### 场景3: 团队绩效对比

**查询**: "对比各团队的完成率和质量指标"

**生成的报告会包含**:
- 团队排名(基于综合得分)
- 完成率、平均进度、延期率对比
- 最佳实践团队的经验分享建议
- 需要支持的团队识别

### 场景4: 转型目标达成分析

**查询**: "AK和云原生转型的完成情况统计"

**生成的报告会包含**:
- AK转型完成率
- 云原生转型完成率
- 双转型完成的应用数量
- 各转型目标的进度分布
- 未来几个月的预期完成情况

## 对比:传统报告 vs 数据驱动报告

### 传统模板化报告
```
根据查询结果,共有25条记录。主要字段包括dev_team, avg_progress等。
数据显示存在一定的进度差异。建议关注进度较低的项目。
```
**问题**: 太泛泛,没有具体数字,缺乏深度分析

### 数据驱动智能报告
```
## 执行摘要
本次查询分析了5个开发团队共52个转型项目。整体平均进度72.6%,
团队间差异显著(最高85.2% vs 最低58.3%)。发现11个延期项目,
其中5个集中在团队C,需要紧急干预。

## 详细分析
### 团队进度分布
- 高绩效团队(≥80%): 团队A(85.2%, 12个项目)
- 中等绩效团队(65-80%): 团队B(72.5%), 团队D(79.1%)
- 需要关注团队(<65%): 团队C(58.3%, 15个项目, 5个严重延期)

### 异常识别
团队C的延期数量(5个)超过平均值2.2的2倍标准差,属于统计异常。
深入分析发现:
- 延期项目中3个卡在测试阶段
- 2个因资源冲突未开始

### 趋势判断
整体趋势:谨慎乐观(72.6%进度符合预期)
风险点:团队C的资源瓶颈可能影响Q4目标达成

## 行动建议
1. 【紧急】召开团队C延期项目专项会议(本周内)
2. 【资源】从团队A借调2名测试工程师支援团队C
3. 【流程】建立每周进度审查机制,延期>7天的项目需要汇报
4. 【分享】组织团队A的敏捷实践分享会
5. 【评估】重新评估团队C的Q4项目优先级,考虑延期部分需求
```

**优势**: 具体、数据支撑、可执行

## 最佳实践

### 1. 编写有效的查询
```sql
-- ✅ 好的查询:明确的业务含义,包含关键维度
SELECT
    dev_team,
    current_status,
    AVG(progress_percentage) as avg_progress,
    COUNT(*) as total_count,
    SUM(CASE WHEN is_delayed THEN 1 ELSE 0 END) as delayed_count
FROM applications
GROUP BY dev_team, current_status
ORDER BY dev_team, current_status;

-- ❌ 差的查询:只有ID,AI无法生成有意义的报告
SELECT id FROM applications;
```

### 2. 提供上下文
```python
# 提供丰富的上下文帮助AI理解查询意图
report = await generate_intelligent_report(
    query=sql_query,
    results=results,
    context={
        "user_intent": "Q4绩效评估",
        "time_period": "2024年Q3",
        "focus_areas": ["延期", "资源"],
        "stakeholders": ["技术总监", "项目经理"]
    }
)
```

### 3. 选择合适的字段
- 包含进度指标:`progress_percentage`, `completion_rate`
- 包含时间维度:`planned_date`, `actual_date`, `delay_days`
- 包含分类维度:`dev_team`, `current_status`, `transformation_target`
- 包含计数聚合:`COUNT(*)`, `SUM(...)`, `AVG(...)`

### 4. 适当的数据量
- ✅ 推荐:10-100条聚合数据
- ⚠️ 可用:100-1000条详细数据(AI会自动摘要)
- ❌ 避免:超过1000条原始数据(性能问题,建议先聚合)

## 性能考虑

- **SQL执行**: 由数据库优化器负责,建议添加适当索引
- **数据分析**: Python内存计算,1000行数据<0.1秒
- **AI生成**: 取决于LLM服务,通常2-10秒
- **总体响应**: 建议使用流式端点获得更好的用户体验

## 故障处理

### AI服务不可用
```python
# 系统会自动降级到基础报告
report = await generate_intelligent_report(
    query=query,
    results=results,
    use_ai=False  # 禁用AI,只返回统计分析
)

# 基础报告仍然包含:
# - 数据摘要
# - 统计分析
# - 关键洞察
# - 异常检测
# 只是没有AI生成的自然语言叙述
```

### 数据质量问题
```python
# 系统会自动处理:
# - NULL值:自动跳过
# - 类型错误:尝试类型转换
# - 空结果:返回"无数据"提示
# - 单条记录:降级为详情展示
```

## 配置选项

### 环境变量
```bash
# 启用AI功能
MCP_ENABLE_AI_TOOLS=True

# 配置LLM服务
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=qwen2.5-coder-7b-instruct

# 或使用本地LLM
LOCAL_LLM_BASE_URL=http://localhost:11434  # Ollama
LOCAL_LLM_MODEL=qwen2.5:latest
```

### 代码配置
```python
from app.services.ai_report_service import AIReportService

# 自定义异常检测阈值(默认2倍标准差)
report = await AIReportService.generate_data_driven_report(
    query=query,
    results=results,
    context={
        "anomaly_threshold": 3  # 更严格的异常检测
    }
)
```

## 总结

新的数据驱动报告生成系统彻底改变了项目报告的方式:

- **从模板化到数据驱动**: 每份报告都基于实际查询结果
- **从泛泛而谈到精准分析**: 引用具体数字和百分比
- **从静态报告到智能洞察**: AI识别模式、异常和趋势
- **从单一视角到多维分析**: 统计+分类+异常+趋势

**关键价值**:
1. ⏱️ 节省时间:自动生成专业报告,无需手动分析
2. 📊 数据准确:直接基于SQL查询,避免人工错误
3. 🔍 深度洞察:AI识别人类容易忽略的模式
4. 💡 可执行建议:提供具体的、数据支撑的行动方案

开始使用数据驱动报告,让数据真正说话!
