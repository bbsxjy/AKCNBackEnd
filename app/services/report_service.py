"""
Report Generation Service

Provides comprehensive reporting capabilities including progress summaries,
department comparisons, delayed project analysis, and trend visualization.
"""

import io
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User
from app.core.exceptions import ValidationError, BusinessLogicError


class ReportType:
    """Report type enumeration."""
    PROGRESS_SUMMARY = "progress_summary"
    DEPARTMENT_COMPARISON = "department_comparison"
    DELAYED_PROJECTS = "delayed_projects"
    TREND_ANALYSIS = "trend_analysis"
    CUSTOM_REPORT = "custom_report"
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    TEAM_PERFORMANCE = "team_performance"
    RISK_ASSESSMENT = "risk_assessment"


class ChartType:
    """Chart type enumeration."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    RADAR = "radar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class ReportService:
    """Service for generating various reports and analytics."""

    async def generate_progress_summary_report(
        self,
        db: AsyncSession,
        supervision_year: Optional[int] = None,
        dev_team: Optional[str] = None,
        transformation_target: Optional[str] = None,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Generate progress summary report for applications and subtasks."""

        # Build base query
        query = select(Application).options(selectinload(Application.sub_tasks))

        # Apply filters
        conditions = []
        if supervision_year:
            conditions.append(Application.ak_supervision_acceptance_year == supervision_year)
        if dev_team:
            conditions.append(Application.dev_team == dev_team)
        if transformation_target:
            conditions.append(Application.overall_transformation_target == transformation_target)

        if conditions:
            query = query.where(and_(*conditions))

        # Execute query
        result = await db.execute(query)
        applications = result.scalars().all()

        # Calculate statistics
        total_apps = len(applications)

        # Status distribution
        status_distribution = defaultdict(int)
        progress_ranges = {
            "0-25%": 0,
            "26-50%": 0,
            "51-75%": 0,
            "76-99%": 0,
            "100%": 0
        }

        # Team statistics
        team_stats = defaultdict(lambda: {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "not_started": 0,
            "average_progress": 0,
            "total_progress": 0
        })

        # Target statistics
        target_stats = {
            "AK": {"total": 0, "completed": 0, "average_progress": 0},
            "云原生": {"total": 0, "completed": 0, "average_progress": 0}
        }

        # Process applications
        completed_apps = 0
        total_progress = 0
        delayed_count = 0

        application_details = []

        for app in applications:
            # Status distribution
            status_distribution[app.current_status] += 1

            # Progress ranges
            progress = app.progress_percentage or 0
            total_progress += progress

            if progress == 0:
                progress_ranges["0-25%"] += 1
            elif progress <= 25:
                progress_ranges["0-25%"] += 1
            elif progress <= 50:
                progress_ranges["26-50%"] += 1
            elif progress <= 75:
                progress_ranges["51-75%"] += 1
            elif progress < 100:
                progress_ranges["76-99%"] += 1
            else:
                progress_ranges["100%"] += 1
                completed_apps += 1

            # Team statistics
            team = app.dev_team if app.dev_team else "未分配"
            team_stats[team]["total"] += 1
            team_stats[team]["total_progress"] += progress

            if app.current_status == ApplicationStatus.COMPLETED:
                team_stats[team]["completed"] += 1
            elif app.current_status == ApplicationStatus.NOT_STARTED:
                team_stats[team]["not_started"] += 1
            else:
                team_stats[team]["in_progress"] += 1

            # Target statistics
            target = app.transformation_target
            if target in target_stats:
                target_stats[target]["total"] += 1
                if app.current_status == ApplicationStatus.COMPLETED:
                    target_stats[target]["completed"] += 1

            # Check for delays
            today = date.today()
            if app.planned_biz_online_date and app.planned_biz_online_date < today:
                if not app.actual_biz_online_date or app.actual_biz_online_date > app.planned_biz_online_date:
                    delayed_count += 1

            # Collect application details
            if include_details:
                subtask_summary = self._calculate_subtask_summary(app.sub_tasks)

                application_details.append({
                    "l2_id": app.l2_id,
                    "app_name": app.app_name,
                    "dev_team": app.dev_team,
                    "dev_owner": app.dev_owner,
                    "overall_status": app.current_status,
                    "progress_percentage": progress,
                    "subtask_total": subtask_summary["total"],
                    "subtask_completed": subtask_summary["completed"],
                    "subtask_blocked": subtask_summary["blocked"],
                    "is_delayed": self._check_if_delayed(app)
                })

        # Calculate team averages
        for team, stats in team_stats.items():
            if stats["total"] > 0:
                stats["average_progress"] = round(stats["total_progress"] / stats["total"], 2)
            del stats["total_progress"]  # Remove temporary field

        # Calculate target averages
        for target, stats in target_stats.items():
            if stats["total"] > 0:
                stats["average_progress"] = round(
                    sum(1 for app in applications
                        if app.transformation_target == target) * 100 / stats["total"],
                    2
                )

        # Overall statistics
        average_progress = round(total_progress / total_apps, 2) if total_apps > 0 else 0
        completion_rate = round((completed_apps / total_apps) * 100, 2) if total_apps > 0 else 0

        # Generate report
        report = {
            "report_type": ReportType.PROGRESS_SUMMARY,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "supervision_year": supervision_year,
                "dev_team": dev_team,
                "transformation_target": transformation_target
            },
            "summary": {
                "total_applications": total_apps,
                "completed_applications": completed_apps,
                "average_progress": average_progress,
                "completion_rate": completion_rate,
                "delayed_projects": delayed_count
            },
            "status_distribution": dict(status_distribution),
            "progress_ranges": progress_ranges,
            "team_statistics": dict(team_stats),
            "target_statistics": target_stats,
            "charts": {
                "status_chart": self._generate_chart_config(
                    ChartType.PIE,
                    "应用状态分布",
                    dict(status_distribution)
                ),
                "progress_chart": self._generate_chart_config(
                    ChartType.BAR,
                    "进度范围分布",
                    progress_ranges
                ),
                "team_chart": self._generate_chart_config(
                    ChartType.BAR,
                    "团队进度对比",
                    {team: stats["average_progress"] for team, stats in team_stats.items()}
                )
            }
        }

        if include_details:
            report["application_details"] = application_details

        return report

    async def generate_department_comparison_report(
        self,
        db: AsyncSession,
        supervision_year: Optional[int] = None,
        include_subtasks: bool = True
    ) -> Dict[str, Any]:
        """Generate department/team comparison report."""

        # Get all teams
        teams_query = select(Application.dev_team).distinct()
        if supervision_year:
            teams_query = teams_query.where(Application.ak_supervision_acceptance_year == supervision_year)

        teams_result = await db.execute(teams_query)
        teams = [row[0] for row in teams_result.all() if row[0]]

        # Collect statistics for each team
        team_comparisons = []

        for team in teams:
            # Get team applications
            app_query = select(Application).options(selectinload(Application.sub_tasks))
            app_query = app_query.where(Application.dev_team == team)

            if supervision_year:
                app_query = app_query.where(Application.ak_supervision_acceptance_year == supervision_year)

            result = await db.execute(app_query)
            team_apps = result.scalars().all()

            if not team_apps:
                continue

            # Calculate team metrics
            total_apps = len(team_apps)
            completed_apps = sum(1 for app in team_apps if app.current_status == ApplicationStatus.COMPLETED)
            total_progress = sum(app.progress_percentage or 0 for app in team_apps)
            average_progress = round(total_progress / total_apps, 2) if total_apps > 0 else 0

            # Subtask statistics
            total_subtasks = 0
            completed_subtasks = 0
            blocked_subtasks = 0

            if include_subtasks:
                for app in team_apps:
                    total_subtasks += len(app.sub_tasks)
                    completed_subtasks += sum(1 for st in app.sub_tasks if st.task_status == SubTaskStatus.COMPLETED)
                    blocked_subtasks += sum(1 for st in app.sub_tasks if st.is_blocked)

            # Delay analysis
            delayed_apps = 0
            total_delay_days = 0

            for app in team_apps:
                delay_info = self._calculate_delay(app)
                if delay_info["is_delayed"]:
                    delayed_apps += 1
                    total_delay_days += delay_info["delay_days"]

            average_delay = round(total_delay_days / delayed_apps, 1) if delayed_apps > 0 else 0

            # Target distribution
            target_distribution = defaultdict(int)
            for app in team_apps:
                target_distribution[app.transformation_target] += 1

            team_comparison = {
                "team_name": team,
                "total_applications": total_apps,
                "completed_applications": completed_apps,
                "completion_rate": round((completed_apps / total_apps) * 100, 2) if total_apps > 0 else 0,
                "average_progress": average_progress,
                "delayed_applications": delayed_apps,
                "average_delay_days": average_delay,
                "target_distribution": dict(target_distribution),
                "ranking_score": average_progress - (delayed_apps * 5)  # Simple ranking score
            }

            if include_subtasks:
                team_comparison["subtask_metrics"] = {
                    "total": total_subtasks,
                    "completed": completed_subtasks,
                    "blocked": blocked_subtasks,
                    "completion_rate": round((completed_subtasks / total_subtasks) * 100, 2) if total_subtasks > 0 else 0
                }

            team_comparisons.append(team_comparison)

        # Sort teams by ranking score
        team_comparisons.sort(key=lambda x: x["ranking_score"], reverse=True)

        # Add ranking
        for i, team in enumerate(team_comparisons, 1):
            team["ranking"] = i

        # Generate comparison charts
        charts = {
            "progress_comparison": self._generate_chart_config(
                ChartType.BAR,
                "团队平均进度对比",
                {team["team_name"]: team["average_progress"] for team in team_comparisons}
            ),
            "completion_comparison": self._generate_chart_config(
                ChartType.BAR,
                "团队完成率对比",
                {team["team_name"]: team["completion_rate"] for team in team_comparisons}
            ),
            "delay_comparison": self._generate_chart_config(
                ChartType.LINE,
                "团队延期项目对比",
                {team["team_name"]: team["delayed_applications"] for team in team_comparisons}
            )
        }

        # Generate report
        return {
            "report_type": ReportType.DEPARTMENT_COMPARISON,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "supervision_year": supervision_year,
                "include_subtasks": include_subtasks
            },
            "summary": {
                "total_teams": len(team_comparisons),
                "best_performing_team": team_comparisons[0]["team_name"] if team_comparisons else None,
                "average_team_progress": round(
                    sum(t["average_progress"] for t in team_comparisons) / len(team_comparisons), 2
                ) if team_comparisons else 0
            },
            "team_comparisons": team_comparisons,
            "charts": charts
        }

    async def generate_delayed_projects_report(
        self,
        db: AsyncSession,
        supervision_year: Optional[int] = None,
        dev_team: Optional[str] = None,
        severity_threshold: int = 7  # Days delayed to be considered severe
    ) -> Dict[str, Any]:
        """Generate report of delayed projects with detailed analysis."""

        # Query applications
        query = select(Application).options(selectinload(Application.sub_tasks))

        conditions = []
        if supervision_year:
            conditions.append(Application.ak_supervision_acceptance_year == supervision_year)
        if dev_team:
            conditions.append(Application.dev_team == dev_team)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        applications = result.scalars().all()

        # Analyze delays
        delayed_projects = []
        delay_categories = {
            "minor": [],  # 1-7 days
            "moderate": [],  # 8-30 days
            "severe": [],  # 31+ days
        }

        total_delay_days = 0

        for app in applications:
            delay_info = self._calculate_comprehensive_delay(app)

            if delay_info["is_delayed"]:
                project_delay = {
                    "l2_id": app.l2_id,
                    "app_name": app.app_name,
                    "dev_team": app.dev_team,
                    "dev_owner": app.dev_owner,
                    "overall_status": app.current_status,
                    "progress_percentage": app.progress_percentage,
                    "delay_days": delay_info["total_delay_days"],
                    "delay_stages": delay_info["delayed_stages"],
                    "planned_completion": app.planned_biz_online_date.isoformat() if app.planned_biz_online_date else None,
                    "expected_completion": delay_info["expected_completion"],
                    "delay_severity": delay_info["severity"],
                    "blocked_subtasks": self._get_blocked_subtasks(app.sub_tasks),
                    "risk_factors": delay_info["risk_factors"]
                }

                delayed_projects.append(project_delay)
                total_delay_days += delay_info["total_delay_days"]

                # Categorize by severity
                if delay_info["total_delay_days"] <= 7:
                    delay_categories["minor"].append(project_delay)
                elif delay_info["total_delay_days"] <= 30:
                    delay_categories["moderate"].append(project_delay)
                else:
                    delay_categories["severe"].append(project_delay)

        # Sort by delay days (descending)
        delayed_projects.sort(key=lambda x: x["delay_days"], reverse=True)

        # Calculate statistics
        total_delayed = len(delayed_projects)
        average_delay = round(total_delay_days / total_delayed, 1) if total_delayed > 0 else 0

        # Team delay analysis
        team_delays = defaultdict(lambda: {"count": 0, "total_days": 0})
        for project in delayed_projects:
            team = project["dev_team"]
            team_delays[team]["count"] += 1
            team_delays[team]["total_days"] += project["delay_days"]

        # Generate charts
        charts = {
            "severity_distribution": self._generate_chart_config(
                ChartType.PIE,
                "延期严重程度分布",
                {
                    "轻微 (1-7天)": len(delay_categories["minor"]),
                    "中等 (8-30天)": len(delay_categories["moderate"]),
                    "严重 (31+天)": len(delay_categories["severe"])
                }
            ),
            "team_delays": self._generate_chart_config(
                ChartType.BAR,
                "团队延期项目数量",
                {team: data["count"] for team, data in team_delays.items()}
            ),
            "top_delays": self._generate_chart_config(
                ChartType.BAR,
                "延期最严重的项目 (前10)",
                {p["app_name"]: p["delay_days"] for p in delayed_projects[:10]}
            )
        }

        # Generate report
        return {
            "report_type": ReportType.DELAYED_PROJECTS,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "supervision_year": supervision_year,
                "dev_team": dev_team,
                "severity_threshold": severity_threshold
            },
            "summary": {
                "total_delayed_projects": total_delayed,
                "average_delay_days": average_delay,
                "max_delay_days": max(p["delay_days"] for p in delayed_projects) if delayed_projects else 0,
                "severe_delays": len(delay_categories["severe"]),
                "moderate_delays": len(delay_categories["moderate"]),
                "minor_delays": len(delay_categories["minor"])
            },
            "delayed_projects": delayed_projects,
            "delay_categories": delay_categories,
            "team_delay_analysis": dict(team_delays),
            "charts": charts,
            "recommendations": self._generate_delay_recommendations(delayed_projects, team_delays)
        }

    async def generate_trend_analysis_report(
        self,
        db: AsyncSession,
        supervision_year: Optional[int] = None,
        time_period: str = "monthly",  # daily, weekly, monthly, quarterly
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate trend analysis report with historical data."""

        # Default metrics if not specified
        if not metrics:
            metrics = ["progress", "completion_rate", "delay_rate", "blocked_tasks"]

        # Determine time ranges
        end_date = date.today()
        if time_period == "daily":
            start_date = end_date - timedelta(days=30)
            intervals = 30
        elif time_period == "weekly":
            start_date = end_date - timedelta(weeks=12)
            intervals = 12
        elif time_period == "quarterly":
            start_date = end_date - timedelta(days=365)
            intervals = 4
        else:  # monthly
            start_date = end_date - timedelta(days=180)
            intervals = 6

        # Generate trend data (simulated for now - would use audit logs in production)
        trend_data = self._generate_trend_data(
            start_date, end_date, intervals, time_period, metrics
        )

        # Calculate trend indicators
        trend_indicators = {}
        for metric in metrics:
            if metric in trend_data:
                values = list(trend_data[metric].values())
                if len(values) >= 2:
                    change = values[-1] - values[-2]
                    change_percent = round((change / values[-2]) * 100, 2) if values[-2] != 0 else 0
                    trend_indicators[metric] = {
                        "current_value": values[-1],
                        "previous_value": values[-2],
                        "change": change,
                        "change_percent": change_percent,
                        "trend": "up" if change > 0 else "down" if change < 0 else "stable"
                    }

        # Generate trend charts
        charts = {}
        if "progress" in trend_data:
            charts["progress_trend"] = self._generate_chart_config(
                ChartType.LINE,
                "进度趋势",
                trend_data["progress"]
            )

        if "completion_rate" in trend_data:
            charts["completion_trend"] = self._generate_chart_config(
                ChartType.AREA,
                "完成率趋势",
                trend_data["completion_rate"]
            )

        if "delay_rate" in trend_data:
            charts["delay_trend"] = self._generate_chart_config(
                ChartType.LINE,
                "延期率趋势",
                trend_data["delay_rate"]
            )

        # Generate report
        return {
            "report_type": ReportType.TREND_ANALYSIS,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "supervision_year": supervision_year,
                "time_period": time_period,
                "metrics": metrics
            },
            "time_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "intervals": intervals,
                "period_type": time_period
            },
            "trend_data": trend_data,
            "trend_indicators": trend_indicators,
            "charts": charts,
            "insights": self._generate_trend_insights(trend_data, trend_indicators)
        }

    async def generate_custom_report(
        self,
        db: AsyncSession,
        report_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate custom report based on user configuration."""

        # Extract configuration
        title = report_config.get("title", "自定义报表")
        filters = report_config.get("filters", {})
        metrics = report_config.get("metrics", [])
        groupings = report_config.get("groupings", [])
        chart_types = report_config.get("chart_types", {})

        # Build query based on filters
        query = select(Application).options(selectinload(Application.sub_tasks))

        conditions = []
        for field, value in filters.items():
            if hasattr(Application, field) and value is not None:
                conditions.append(getattr(Application, field) == value)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        applications = result.scalars().all()

        # Calculate requested metrics
        report_data = {
            "title": title,
            "filters": filters,
            "total_records": len(applications),
            "metrics": {}
        }

        for metric in metrics:
            if metric == "total_count":
                report_data["metrics"]["total_count"] = len(applications)
            elif metric == "average_progress":
                avg_progress = sum(app.progress_percentage or 0 for app in applications) / len(applications) if applications else 0
                report_data["metrics"]["average_progress"] = round(avg_progress, 2)
            elif metric == "completion_rate":
                completed = sum(1 for app in applications if app.current_status == ApplicationStatus.COMPLETED)
                report_data["metrics"]["completion_rate"] = round((completed / len(applications)) * 100, 2) if applications else 0
            elif metric == "delay_rate":
                delayed = sum(1 for app in applications if self._check_if_delayed(app))
                report_data["metrics"]["delay_rate"] = round((delayed / len(applications)) * 100, 2) if applications else 0

        # Apply groupings
        if groupings:
            grouped_data = {}
            for grouping in groupings:
                if grouping == "team":
                    grouped_data["by_team"] = self._group_by_field(applications, "dev_team")
                elif grouping == "status":
                    grouped_data["by_status"] = self._group_by_field(applications, "current_status")
                elif grouping == "target":
                    grouped_data["by_target"] = self._group_by_field(applications, "transformation_target")

            report_data["grouped_data"] = grouped_data

        # Generate charts based on configuration
        charts = {}
        for chart_name, chart_config in chart_types.items():
            chart_type = chart_config.get("type", ChartType.BAR)
            chart_data = chart_config.get("data", {})
            chart_title = chart_config.get("title", chart_name)

            charts[chart_name] = self._generate_chart_config(chart_type, chart_title, chart_data)

        report_data["charts"] = charts

        # Generate report
        return {
            "report_type": ReportType.CUSTOM_REPORT,
            "generated_at": datetime.utcnow().isoformat(),
            "report_config": report_config,
            "data": report_data
        }

    # Helper methods

    def _calculate_subtask_summary(self, subtasks: List[SubTask]) -> Dict[str, int]:
        """Calculate subtask summary statistics."""
        return {
            "total": len(subtasks),
            "completed": sum(1 for st in subtasks if st.task_status == SubTaskStatus.COMPLETED),
            "in_progress": sum(1 for st in subtasks if st.task_status in [
                SubTaskStatus.DEV_IN_PROGRESS, SubTaskStatus.TESTING, SubTaskStatus.DEPLOYMENT_READY
            ]),
            "not_started": sum(1 for st in subtasks if st.task_status == SubTaskStatus.NOT_STARTED),
            "blocked": sum(1 for st in subtasks if st.is_blocked)
        }

    def _check_if_delayed(self, application: Application) -> bool:
        """Check if application is delayed."""
        today = date.today()

        # Check each milestone
        if application.planned_requirement_date and application.planned_requirement_date < today:
            if not application.actual_requirement_date:
                return True

        if application.planned_release_date and application.planned_release_date < today:
            if not application.actual_release_date:
                return True

        if application.planned_tech_online_date and application.planned_tech_online_date < today:
            if not application.actual_tech_online_date:
                return True

        if application.planned_biz_online_date and application.planned_biz_online_date < today:
            if not application.actual_biz_online_date:
                return True

        return False

    def _calculate_delay(self, application: Application) -> Dict[str, Any]:
        """Calculate delay information for an application."""
        today = date.today()
        delay_days = 0
        is_delayed = False

        if application.planned_biz_online_date and application.planned_biz_online_date < today:
            if application.actual_biz_online_date:
                if application.actual_biz_online_date > application.planned_biz_online_date:
                    delay_days = (application.actual_biz_online_date - application.planned_biz_online_date).days
                    is_delayed = True
            else:
                delay_days = (today - application.planned_biz_online_date).days
                is_delayed = True

        return {
            "is_delayed": is_delayed,
            "delay_days": delay_days
        }

    def _calculate_comprehensive_delay(self, application: Application) -> Dict[str, Any]:
        """Calculate comprehensive delay information."""
        today = date.today()
        delayed_stages = []
        total_delay_days = 0
        risk_factors = []

        # Check each stage
        stages = [
            ("requirement", application.planned_requirement_date, application.actual_requirement_date),
            ("release", application.planned_release_date, application.actual_release_date),
            ("tech_online", application.planned_tech_online_date, application.actual_tech_online_date),
            ("biz_online", application.planned_biz_online_date, application.actual_biz_online_date)
        ]

        for stage_name, planned, actual in stages:
            if planned and planned < today:
                if actual:
                    if actual > planned:
                        delay = (actual - planned).days
                        delayed_stages.append({
                            "stage": stage_name,
                            "planned": planned.isoformat(),
                            "actual": actual.isoformat(),
                            "delay_days": delay
                        })
                        total_delay_days = max(total_delay_days, delay)
                else:
                    delay = (today - planned).days
                    delayed_stages.append({
                        "stage": stage_name,
                        "planned": planned.isoformat(),
                        "actual": None,
                        "delay_days": delay
                    })
                    total_delay_days = max(total_delay_days, delay)

        # Determine severity
        if total_delay_days == 0:
            severity = "none"
        elif total_delay_days <= 7:
            severity = "minor"
        elif total_delay_days <= 30:
            severity = "moderate"
        else:
            severity = "severe"

        # Identify risk factors
        if application.progress_percentage < 30 and total_delay_days > 0:
            risk_factors.append("低进度高延期")

        if len(delayed_stages) >= 2:
            risk_factors.append("多阶段延期")

        blocked_subtasks = sum(1 for st in application.sub_tasks if st.is_blocked)
        if blocked_subtasks > 0:
            risk_factors.append(f"{blocked_subtasks}个子任务阻塞")

        # Calculate expected completion
        expected_completion = None
        if application.planned_biz_online_date:
            expected_completion = (application.planned_biz_online_date + timedelta(days=total_delay_days)).isoformat()

        return {
            "is_delayed": total_delay_days > 0,
            "total_delay_days": total_delay_days,
            "delayed_stages": delayed_stages,
            "severity": severity,
            "risk_factors": risk_factors,
            "expected_completion": expected_completion
        }

    def _get_blocked_subtasks(self, subtasks: List[SubTask]) -> List[Dict[str, str]]:
        """Get blocked subtasks information."""
        blocked = []
        for st in subtasks:
            if st.is_blocked:
                blocked.append({
                    "module_name": st.module_name,
                    "block_reason": st.block_reason or "未指定原因"
                })
        return blocked

    def _generate_chart_config(
        self,
        chart_type: str,
        title: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate chart configuration."""
        return {
            "type": chart_type,
            "title": title,
            "data": {
                "labels": list(data.keys()),
                "values": list(data.values())
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "legend": {
                        "display": chart_type in [ChartType.PIE, ChartType.DOUGHNUT]
                    },
                    "title": {
                        "display": True,
                        "text": title
                    }
                }
            }
        }

    def _generate_delay_recommendations(
        self,
        delayed_projects: List[Dict],
        team_delays: Dict
    ) -> List[str]:
        """Generate recommendations based on delay analysis."""
        recommendations = []

        # Overall recommendations
        if len(delayed_projects) > 10:
            recommendations.append("建议：延期项目数量较多，需要进行整体资源评估和优先级调整")

        # Severe delays
        severe_count = sum(1 for p in delayed_projects if p["delay_severity"] == "severe")
        if severe_count > 0:
            recommendations.append(f"警告：有{severe_count}个项目严重延期，需要立即采取纠正措施")

        # Team-specific recommendations
        for team, data in team_delays.items():
            if data["count"] >= 3:
                avg_delay = data["total_days"] / data["count"]
                recommendations.append(f"建议：{team}团队有{data['count']}个延期项目，平均延期{avg_delay:.1f}天，需要团队内部评审")

        # Blocked tasks
        total_blocked = sum(len(p["blocked_subtasks"]) for p in delayed_projects)
        if total_blocked > 5:
            recommendations.append(f"建议：共有{total_blocked}个子任务被阻塞，需要协调解决依赖问题")

        return recommendations

    def _generate_trend_data(
        self,
        start_date: date,
        end_date: date,
        intervals: int,
        period_type: str,
        metrics: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Generate trend data (simulated for demonstration)."""
        import random

        trend_data = {}

        # Generate date labels
        date_labels = []
        current = start_date
        delta = (end_date - start_date) / intervals

        for i in range(intervals):
            if period_type == "daily":
                label = current.strftime("%m/%d")
            elif period_type == "weekly":
                label = f"Week {i+1}"
            elif period_type == "monthly":
                label = current.strftime("%Y/%m")
            else:  # quarterly
                label = f"Q{(i % 4) + 1}"

            date_labels.append(label)
            current += delta

        # Generate data for each metric
        for metric in metrics:
            if metric == "progress":
                # Simulated progress trend (generally increasing)
                base = 20
                trend_data["progress"] = {}
                for i, label in enumerate(date_labels):
                    base += random.randint(5, 15)
                    trend_data["progress"][label] = min(base, 100)

            elif metric == "completion_rate":
                # Simulated completion rate
                base = 10
                trend_data["completion_rate"] = {}
                for i, label in enumerate(date_labels):
                    base += random.randint(3, 8)
                    trend_data["completion_rate"][label] = min(base, 100)

            elif metric == "delay_rate":
                # Simulated delay rate (hopefully decreasing)
                base = 30
                trend_data["delay_rate"] = {}
                for i, label in enumerate(date_labels):
                    base -= random.randint(0, 5)
                    trend_data["delay_rate"][label] = max(base, 5)

            elif metric == "blocked_tasks":
                # Simulated blocked tasks
                trend_data["blocked_tasks"] = {}
                for label in date_labels:
                    trend_data["blocked_tasks"][label] = random.randint(5, 25)

        return trend_data

    def _generate_trend_insights(
        self,
        trend_data: Dict[str, Dict],
        trend_indicators: Dict[str, Dict]
    ) -> List[str]:
        """Generate insights based on trend analysis."""
        insights = []

        for metric, indicator in trend_indicators.items():
            if indicator["trend"] == "up":
                if metric == "progress" or metric == "completion_rate":
                    insights.append(f"积极趋势：{metric}呈上升趋势，增长{indicator['change_percent']}%")
                elif metric == "delay_rate":
                    insights.append(f"警告：延期率上升{indicator['change_percent']}%，需要关注")
            elif indicator["trend"] == "down":
                if metric == "progress" or metric == "completion_rate":
                    insights.append(f"警告：{metric}下降{abs(indicator['change_percent'])}%，需要采取措施")
                elif metric == "delay_rate":
                    insights.append(f"积极趋势：延期率下降{abs(indicator['change_percent'])}%")

        # Additional insights based on data patterns
        if "progress" in trend_data:
            values = list(trend_data["progress"].values())
            if len(values) >= 3:
                recent_trend = values[-3:]
                if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                    insights.append("发现：最近三个周期进度持续改善")

        return insights

    def _group_by_field(
        self,
        applications: List[Application],
        field_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """Group applications by specified field."""
        grouped = defaultdict(lambda: {
            "count": 0,
            "total_progress": 0,
            "completed": 0,
            "delayed": 0
        })

        for app in applications:
            key = getattr(app, field_name, "Unknown")
            grouped[key]["count"] += 1
            grouped[key]["total_progress"] += app.progress_percentage or 0

            if app.current_status == ApplicationStatus.COMPLETED:
                grouped[key]["completed"] += 1

            if self._check_if_delayed(app):
                grouped[key]["delayed"] += 1

        # Calculate averages
        for key, data in grouped.items():
            if data["count"] > 0:
                data["average_progress"] = round(data["total_progress"] / data["count"], 2)
                del data["total_progress"]

        return dict(grouped)