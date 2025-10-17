"""
AI-Powered Data-Driven Report Generation Service

This service generates intelligent reports based on actual SQL query results,
providing deep insights rather than template-based summaries.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Analyzes SQL query results to extract key insights."""

    @staticmethod
    def analyze_query_results(
        query: str,
        results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze SQL query results to extract structured insights.

        Args:
            query: The SQL query that was executed
            results: Query execution results (columns, rows, row_count)
            context: Additional context (filters, user intent, etc.)

        Returns:
            Structured analysis with statistics, patterns, and anomalies
        """
        analysis = {
            "query_info": DataAnalyzer._analyze_query_intent(query),
            "data_summary": DataAnalyzer._get_data_summary(results),
            "statistics": {},
            "insights": [],
            "anomalies": [],
            "trends": []
        }

        # Extract columns and rows
        columns = results.get("columns", [])
        rows = results.get("rows", [])

        if not rows:
            analysis["insights"].append("查询未返回任何数据")
            return analysis

        # Analyze numeric columns for statistics
        numeric_stats = DataAnalyzer._analyze_numeric_columns(columns, rows)
        if numeric_stats:
            analysis["statistics"]["numeric"] = numeric_stats

        # Analyze categorical columns for distribution
        categorical_stats = DataAnalyzer._analyze_categorical_columns(columns, rows)
        if categorical_stats:
            analysis["statistics"]["categorical"] = categorical_stats

        # Detect anomalies (outliers, unusual patterns)
        anomalies = DataAnalyzer._detect_anomalies(columns, rows, numeric_stats)
        if anomalies:
            analysis["anomalies"] = anomalies

        # Generate insights based on data patterns
        insights = DataAnalyzer._generate_insights(
            columns, rows, numeric_stats, categorical_stats, context
        )
        analysis["insights"].extend(insights)

        return analysis

    @staticmethod
    def _analyze_query_intent(query: str) -> Dict[str, Any]:
        """Determine what the query is trying to find."""
        query_lower = query.lower()
        intent = {
            "type": "unknown",
            "focus": [],
            "filters": []
        }

        # Identify query type
        if "count" in query_lower:
            intent["type"] = "aggregation"
            intent["focus"].append("count")
        elif "avg" in query_lower or "average" in query_lower:
            intent["type"] = "aggregation"
            intent["focus"].append("average")
        elif "sum" in query_lower:
            intent["type"] = "aggregation"
            intent["focus"].append("sum")
        elif "group by" in query_lower:
            intent["type"] = "grouping"
        else:
            intent["type"] = "listing"

        # Identify key entities
        if "application" in query_lower:
            intent["focus"].append("applications")
        if "subtask" in query_lower or "sub_task" in query_lower:
            intent["focus"].append("subtasks")
        if "team" in query_lower:
            intent["focus"].append("team")
        if "delay" in query_lower:
            intent["focus"].append("delays")
        if "progress" in query_lower:
            intent["focus"].append("progress")
        if "status" in query_lower:
            intent["focus"].append("status")

        return intent

    @staticmethod
    def _get_data_summary(results: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic data summary."""
        return {
            "total_rows": results.get("row_count", 0),
            "total_columns": len(results.get("columns", [])),
            "columns": results.get("columns", [])
        }

    @staticmethod
    def _analyze_numeric_columns(
        columns: List[str],
        rows: List[List[Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze numeric columns for statistical insights."""
        numeric_stats = {}

        for col_idx, col_name in enumerate(columns):
            # Try to extract numeric values
            numeric_values = []
            for row in rows:
                try:
                    value = row[col_idx]
                    if value is not None:
                        # Try to convert to float
                        if isinstance(value, (int, float)):
                            numeric_values.append(float(value))
                        elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                            numeric_values.append(float(value))
                except (ValueError, IndexError):
                    continue

            # If we have enough numeric values, calculate statistics
            if len(numeric_values) >= 2:
                stats = {
                    "count": len(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": statistics.mean(numeric_values),
                    "median": statistics.median(numeric_values)
                }

                # Calculate std dev if we have enough data points
                if len(numeric_values) >= 3:
                    stats["std_dev"] = statistics.stdev(numeric_values)

                numeric_stats[col_name] = stats

        return numeric_stats

    @staticmethod
    def _analyze_categorical_columns(
        columns: List[str],
        rows: List[List[Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze categorical columns for distribution insights."""
        categorical_stats = {}

        for col_idx, col_name in enumerate(columns):
            # Count value frequencies
            value_counts = defaultdict(int)
            total_count = 0

            for row in rows:
                try:
                    value = row[col_idx]
                    if value is not None:
                        value_str = str(value)
                        value_counts[value_str] += 1
                        total_count += 1
                except IndexError:
                    continue

            # If we have categorical data (limited unique values)
            unique_count = len(value_counts)
            if unique_count > 0 and unique_count <= 20:  # Reasonable for categorical
                # Calculate percentages
                distribution = {}
                for value, count in value_counts.items():
                    distribution[value] = {
                        "count": count,
                        "percentage": round((count / total_count) * 100, 2)
                    }

                categorical_stats[col_name] = {
                    "unique_values": unique_count,
                    "total_count": total_count,
                    "distribution": distribution,
                    "most_common": max(value_counts.items(), key=lambda x: x[1])[0],
                    "least_common": min(value_counts.items(), key=lambda x: x[1])[0]
                }

        return categorical_stats

    @staticmethod
    def _detect_anomalies(
        columns: List[str],
        rows: List[List[Any]],
        numeric_stats: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in the data."""
        anomalies = []

        # Check for outliers in numeric columns
        for col_name, stats in numeric_stats.items():
            if "std_dev" in stats and stats["std_dev"] > 0:
                # Find values more than 2 standard deviations from mean
                col_idx = columns.index(col_name)
                threshold = stats["mean"] + (2 * stats["std_dev"])

                outliers = []
                for row in rows:
                    try:
                        value = float(row[col_idx])
                        if value > threshold:
                            outliers.append(value)
                    except (ValueError, TypeError, IndexError):
                        continue

                if outliers:
                    anomalies.append({
                        "type": "outlier",
                        "column": col_name,
                        "description": f"{col_name}列发现{len(outliers)}个异常值(超过2倍标准差)",
                        "values": outliers[:5]  # Show first 5
                    })

        return anomalies

    @staticmethod
    def _generate_insights(
        columns: List[str],
        rows: List[List[Any]],
        numeric_stats: Dict[str, Dict[str, float]],
        categorical_stats: Dict[str, Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate human-readable insights from statistical analysis."""
        insights = []

        # Data volume insights
        total_rows = len(rows)
        if total_rows == 0:
            insights.append("查询未返回任何数据")
        elif total_rows == 1:
            insights.append("查询返回单条记录")
        else:
            insights.append(f"查询返回{total_rows}条记录")

        # Numeric column insights
        for col_name, stats in numeric_stats.items():
            # Interpret specific columns based on name
            if "progress" in col_name.lower() or "percentage" in col_name.lower():
                insights.append(
                    f"{col_name}平均值为{stats['mean']:.1f}%, "
                    f"中位数为{stats['median']:.1f}%, "
                    f"范围从{stats['min']:.1f}%到{stats['max']:.1f}%"
                )
            elif "delay" in col_name.lower() and "days" in col_name.lower():
                insights.append(
                    f"{col_name}平均为{stats['mean']:.1f}天, "
                    f"最长延期{stats['max']:.0f}天"
                )
            elif "count" in col_name.lower():
                insights.append(
                    f"{col_name}总计{stats['mean']:.1f}个(平均), "
                    f"最多{stats['max']:.0f}个"
                )
            else:
                # Generic numeric insight
                insights.append(
                    f"{col_name}平均值{stats['mean']:.2f}, 范围{stats['min']:.2f}-{stats['max']:.2f}"
                )

        # Categorical distribution insights
        for col_name, stats in categorical_stats.items():
            distribution = stats["distribution"]
            most_common = stats["most_common"]
            most_common_pct = distribution[most_common]["percentage"]

            if "status" in col_name.lower():
                insights.append(
                    f"{col_name}分布: {most_common}占比最高({most_common_pct}%), "
                    f"共{stats['unique_values']}种状态"
                )
            elif "team" in col_name.lower():
                insights.append(
                    f"涉及{stats['unique_values']}个团队, "
                    f"{most_common}团队项目最多({most_common_pct}%)"
                )
            else:
                # Generic categorical insight
                top_3 = sorted(
                    distribution.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:3]
                top_values = ", ".join(
                    f"{v}({d['percentage']:.1f}%)" for v, d in top_3
                )
                insights.append(f"{col_name}前三位: {top_values}")

        return insights


class AIReportService:
    """AI-powered report generation service based on actual data analysis."""

    @staticmethod
    async def generate_data_driven_report(
        query: str,
        results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Generate intelligent report from SQL query results.

        Args:
            query: SQL query that was executed
            results: Query execution results
            context: Additional context (user intent, filters, etc.)
            use_ai: Whether to use AI for natural language generation

        Returns:
            Comprehensive report with analysis and insights
        """
        # Step 1: Analyze the data
        analysis = DataAnalyzer.analyze_query_results(query, results, context)

        # Step 2: Build structured report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "data_summary": analysis["data_summary"],
            "statistics": analysis["statistics"],
            "insights": analysis["insights"],
            "anomalies": analysis["anomalies"],
            "trends": analysis["trends"]
        }

        # Step 3: Generate natural language summary using AI (if enabled)
        if use_ai:
            from app.mcp.ai_tools import ai_assistant

            if ai_assistant.enabled:
                try:
                    nl_summary = await AIReportService._generate_ai_narrative(
                        analysis, results
                    )
                    report["ai_narrative"] = nl_summary
                except Exception as e:
                    logger.warning(f"AI narrative generation failed: {e}")
                    report["ai_narrative"] = AIReportService._generate_fallback_narrative(analysis)
            else:
                report["ai_narrative"] = AIReportService._generate_fallback_narrative(analysis)
        else:
            report["ai_narrative"] = AIReportService._generate_fallback_narrative(analysis)

        return report

    @staticmethod
    async def _generate_ai_narrative(
        analysis: Dict[str, Any],
        results: Dict[str, Any]
    ) -> str:
        """Generate AI-powered natural language narrative."""
        from app.mcp.ai_tools import ai_assistant

        # Build a data-rich prompt for AI
        prompt = f"""
你是一个AK/云原生转型项目管理系统的数据分析专家。请基于以下实际的SQL查询分析结果，生成一份专业的项目报告。

## 查询分析
- 查询意图: {analysis['query_info']['type']}
- 关注焦点: {', '.join(analysis['query_info']['focus'])}

## 数据概览
- 总记录数: {analysis['data_summary']['total_rows']}条
- 数据列: {', '.join(analysis['data_summary']['columns'])}

## 统计数据
{AIReportService._format_statistics_for_prompt(analysis['statistics'])}

## 关键洞察
{chr(10).join(f'- {insight}' for insight in analysis['insights'])}

## 异常数据
{AIReportService._format_anomalies_for_prompt(analysis['anomalies'])}

请生成一份包含以下内容的报告:
1. **执行摘要**: 用2-3句话概括最重要的发现
2. **详细分析**: 基于实际数据深入解读当前项目状态，包括:
   - 进度情况(如果有进度数据)
   - 团队表现(如果有团队数据)
   - 延期问题(如果有延期数据)
   - 异常情况(如果有异常数据)
3. **趋势判断**: 基于数据指标判断整体趋势(积极/需要关注/警示)
4. **行动建议**: 提供3-5条具体的、可执行的改进建议

要求:
- 必须基于实际数据，不要臆测
- 引用具体数字和百分比
- 语言专业、简洁、客观
- 用中文回答
"""

        # Call AI to generate narrative
        narrative = await ai_assistant._call_llm(prompt)
        return narrative

    @staticmethod
    def _format_statistics_for_prompt(statistics: Dict[str, Any]) -> str:
        """Format statistics for AI prompt."""
        lines = []

        # Numeric statistics
        if "numeric" in statistics:
            lines.append("### 数值统计")
            for col_name, stats in statistics["numeric"].items():
                lines.append(
                    f"- {col_name}: 平均{stats['mean']:.2f}, "
                    f"中位数{stats['median']:.2f}, "
                    f"范围{stats['min']:.2f}-{stats['max']:.2f}"
                )

        # Categorical statistics
        if "categorical" in statistics:
            lines.append("\n### 分类统计")
            for col_name, stats in statistics["categorical"].items():
                lines.append(f"- {col_name}: {stats['unique_values']}个不同值")
                # Show top 3 distributions
                top_3 = sorted(
                    stats["distribution"].items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:3]
                for value, data in top_3:
                    lines.append(f"  - {value}: {data['count']}个 ({data['percentage']:.1f}%)")

        return "\n".join(lines) if lines else "无统计数据"

    @staticmethod
    def _format_anomalies_for_prompt(anomalies: List[Dict[str, Any]]) -> str:
        """Format anomalies for AI prompt."""
        if not anomalies:
            return "无异常数据"

        lines = []
        for anomaly in anomalies:
            lines.append(f"- {anomaly['description']}")
            if "values" in anomaly:
                lines.append(f"  异常值示例: {', '.join(str(v) for v in anomaly['values'][:3])}")

        return "\n".join(lines)

    @staticmethod
    def _generate_fallback_narrative(analysis: Dict[str, Any]) -> str:
        """Generate basic narrative without AI."""
        lines = []

        lines.append("## 数据分析报告\n")

        # Summary
        lines.append("### 数据概览")
        lines.append(f"- 查询返回 {analysis['data_summary']['total_rows']} 条记录")
        lines.append(f"- 包含 {analysis['data_summary']['total_columns']} 个字段\n")

        # Insights
        if analysis['insights']:
            lines.append("### 关键发现")
            for insight in analysis['insights']:
                lines.append(f"- {insight}")
            lines.append("")

        # Anomalies
        if analysis['anomalies']:
            lines.append("### 异常数据")
            for anomaly in analysis['anomalies']:
                lines.append(f"- {anomaly['description']}")
            lines.append("")

        # Statistics summary
        if analysis['statistics']:
            lines.append("### 统计摘要")
            if "numeric" in analysis['statistics']:
                for col, stats in analysis['statistics']['numeric'].items():
                    lines.append(
                        f"- {col}: 平均 {stats['mean']:.2f}, "
                        f"范围 {stats['min']:.2f} - {stats['max']:.2f}"
                    )

        return "\n".join(lines)


# Convenience function for easy import
async def generate_intelligent_report(
    query: str,
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate an intelligent data-driven report.

    Example usage:
        ```python
        query = "SELECT team, AVG(progress) FROM applications GROUP BY team"
        results = await execute_query(query)
        report = await generate_intelligent_report(query, results)
        print(report["ai_narrative"])
        ```
    """
    return await AIReportService.generate_data_driven_report(query, results, context)
