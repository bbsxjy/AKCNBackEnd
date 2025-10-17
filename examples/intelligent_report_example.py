"""
AI Data-Driven Report Generation Example

This example demonstrates how to use the new intelligent report generation
system to create data-driven insights from SQL queries.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.ai_report_service import generate_intelligent_report, DataAnalyzer


async def example_1_team_performance_analysis():
    """Example 1: Analyze team performance with SQL query."""
    print("=" * 80)
    print("Example 1: Team Performance Analysis")
    print("=" * 80)

    # Simulated SQL query
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

    # Simulated query results (normally from database)
    results = {
        "success": True,
        "columns": ["dev_team", "avg_progress", "total_apps", "delayed_count"],
        "rows": [
            ["团队A", 85.2, 12, 0],
            ["团队D", 79.1, 10, 1],
            ["团队B", 72.5, 8, 2],
            ["团队E", 67.8, 7, 3],
            ["团队C", 58.3, 15, 5],
        ],
        "row_count": 5
    }

    # Generate intelligent report
    report = await generate_intelligent_report(
        query=query,
        results=results,
        context={
            "user_intent": "团队绩效分析",
            "time_period": "2024年"
        }
    )

    # Display results
    print(f"\n📊 数据摘要:")
    print(f"- 总记录数: {report['data_summary']['total_rows']}")
    print(f"- 数据列: {', '.join(report['data_summary']['columns'])}")

    print(f"\n📈 统计信息:")
    if "numeric" in report["statistics"]:
        for col_name, stats in report["statistics"]["numeric"].items():
            print(f"\n{col_name}:")
            print(f"  - 平均值: {stats['mean']:.2f}")
            print(f"  - 中位数: {stats['median']:.2f}")
            print(f"  - 范围: {stats['min']:.2f} - {stats['max']:.2f}")

    print(f"\n💡 关键洞察:")
    for insight in report["insights"]:
        print(f"- {insight}")

    if report["anomalies"]:
        print(f"\n⚠️  异常数据:")
        for anomaly in report["anomalies"]:
            print(f"- {anomaly['description']}")

    print(f"\n📝 AI智能报告:")
    print(report["ai_narrative"])
    print()


async def example_2_delay_analysis():
    """Example 2: Analyze delayed projects."""
    print("=" * 80)
    print("Example 2: Delayed Projects Analysis")
    print("=" * 80)

    query = """
    SELECT app_name,
           dev_team,
           delay_days,
           current_status,
           progress_percentage
    FROM applications
    WHERE is_delayed = true
    ORDER BY delay_days DESC
    LIMIT 10
    """

    results = {
        "success": True,
        "columns": ["app_name", "dev_team", "delay_days", "current_status", "progress_percentage"],
        "rows": [
            ["应用A", "团队C", 45, "TESTING", 75],
            ["应用B", "团队C", 38, "DEV_IN_PROGRESS", 60],
            ["应用C", "团队E", 25, "TESTING", 80],
            ["应用D", "团队B", 12, "BIZ_ONLINE", 95],
            ["应用E", "团队C", 10, "DEV_IN_PROGRESS", 50],
            ["应用F", "团队E", 8, "TESTING", 70],
            ["应用G", "团队D", 5, "TECH_ONLINE", 90],
            ["应用H", "团队B", 3, "BIZ_ONLINE", 98],
        ],
        "row_count": 8
    }

    report = await generate_intelligent_report(
        query=query,
        results=results,
        context={"user_intent": "延期项目分析"}
    )

    print(f"\n📊 数据摘要:")
    print(f"- 延期项目数: {report['data_summary']['total_rows']}")

    print(f"\n📈 延期统计:")
    if "numeric" in report["statistics"]:
        delay_stats = report["statistics"]["numeric"].get("delay_days", {})
        if delay_stats:
            print(f"- 平均延期: {delay_stats['mean']:.1f}天")
            print(f"- 最长延期: {delay_stats['max']:.0f}天")
            print(f"- 最短延期: {delay_stats['min']:.0f}天")

    print(f"\n💡 关键洞察:")
    for insight in report["insights"]:
        print(f"- {insight}")

    if report["anomalies"]:
        print(f"\n⚠️  异常数据:")
        for anomaly in report["anomalies"]:
            print(f"- {anomaly['description']}")

    print(f"\n📝 AI智能报告:")
    print(report["ai_narrative"])
    print()


async def example_3_data_analyzer_only():
    """Example 3: Use DataAnalyzer directly without AI."""
    print("=" * 80)
    print("Example 3: Data Analysis Without AI")
    print("=" * 80)

    query = "SELECT status, COUNT(*) as count FROM applications GROUP BY status"

    results = {
        "columns": ["status", "count"],
        "rows": [
            ["COMPLETED", 45],
            ["BIZ_ONLINE", 30],
            ["DEV_IN_PROGRESS", 25],
            ["TESTING", 15],
            ["NOT_STARTED", 10],
        ],
        "row_count": 5
    }

    # Analyze data without AI
    analysis = DataAnalyzer.analyze_query_results(query, results)

    print(f"\n📊 查询意图分析:")
    print(f"- 类型: {analysis['query_info']['type']}")
    print(f"- 关注点: {', '.join(analysis['query_info']['focus'])}")

    print(f"\n📈 数据概览:")
    print(f"- 总行数: {analysis['data_summary']['total_rows']}")
    print(f"- 总列数: {analysis['data_summary']['total_columns']}")

    print(f"\n💡 数据洞察:")
    for insight in analysis["insights"]:
        print(f"- {insight}")

    if "categorical" in analysis["statistics"]:
        print(f"\n📊 分类数据分布:")
        for col_name, stats in analysis["statistics"]["categorical"].items():
            print(f"\n{col_name} (共{stats['unique_values']}种):")
            # Show top 5
            top_items = sorted(
                stats["distribution"].items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5]
            for value, data in top_items:
                print(f"  - {value}: {data['count']}个 ({data['percentage']:.1f}%)")

    print()


async def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print(" AI Data-Driven Report Generation Examples")
    print("=" * 80)
    print()

    try:
        # Run examples
        await example_1_team_performance_analysis()
        await asyncio.sleep(1)

        await example_2_delay_analysis()
        await asyncio.sleep(1)

        await example_3_data_analyzer_only()

        print("=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
