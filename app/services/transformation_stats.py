"""
Transformation Statistics Calculation Module

Provides utility functions for calculating AK/Cloud Native transformation statistics.
"""

from typing import List, Dict, Any
from app.models.subtask import SubTask, SubTaskStatus


def calculate_completion_percentage(completed_count: int, total_count: int) -> float:
    """
    Calculate completion percentage.

    Args:
        completed_count: Number of completed tasks
        total_count: Total number of tasks

    Returns:
        Completion percentage (0-100), rounded to 2 decimal places
    """
    if total_count == 0:
        return 0.0
    return round((completed_count / total_count) * 100, 2)


def get_transformation_status(
    total_count: int,
    completed_count: int,
    blocked_count: int,
    not_started_count: int
) -> str:
    """
    Derive transformation status based on subtask counts.

    Args:
        total_count: Total number of subtasks
        completed_count: Number of completed subtasks
        blocked_count: Number of blocked subtasks
        not_started_count: Number of not started subtasks

    Returns:
        Status string: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED" | "BLOCKED"
    """
    # No subtasks or all not started
    if total_count == 0 or (not_started_count == total_count and completed_count == 0):
        return "NOT_STARTED"

    # Has blocked subtasks
    if blocked_count > 0:
        return "BLOCKED"

    # All completed
    if completed_count == total_count:
        return "COMPLETED"

    # Otherwise in progress
    return "IN_PROGRESS"


def generate_phase_description(ak_status: str, cloud_native_status: str) -> str:
    """
    Generate current phase description in Chinese.

    Args:
        ak_status: AK transformation status
        cloud_native_status: Cloud Native transformation status

    Returns:
        Chinese description of current phase

    Examples:
        - "AK已完成,云原生进行中"
        - "AK进行中,云原生待启动"
        - "全部完成(AK+云原生)"
        - "仅AK改造(已完成)"
    """
    status_map = {
        "NOT_STARTED": "待启动",
        "IN_PROGRESS": "进行中",
        "COMPLETED": "已完成",
        "BLOCKED": "阻塞"
    }

    ak_text = status_map.get(ak_status, "未知")
    cn_text = status_map.get(cloud_native_status, "未知")

    # Both completed
    if ak_status == "COMPLETED" and cloud_native_status == "COMPLETED":
        return "全部完成(AK+云原生)"

    # Only AK, no Cloud Native
    if ak_status != "NOT_STARTED" and cloud_native_status == "NOT_STARTED":
        return f"仅AK改造({ak_text})"

    # Only Cloud Native, no AK
    if ak_status == "NOT_STARTED" and cloud_native_status != "NOT_STARTED":
        return f"仅云原生改造({cn_text})"

    # Both have subtasks
    return f"AK{ak_text},云原生{cn_text}"


def calculate_subtask_statistics(subtasks: List[SubTask], target: str) -> Dict[str, Any]:
    """
    Calculate statistics for subtasks of a specific target type.

    Args:
        subtasks: List of SubTask objects
        target: Target type ("AK" or "云原生")

    Returns:
        Dictionary containing:
            - subtask_count: Total count
            - completed_count: Completed count
            - in_progress_count: In progress count
            - blocked_count: Blocked count
            - not_started_count: Not started count
            - completion_percentage: Completion percentage
            - status: Transformation status
    """
    # Filter subtasks by target
    target_subtasks = [st for st in subtasks if st.sub_target == target]

    total_count = len(target_subtasks)

    if total_count == 0:
        return {
            'subtask_count': 0,
            'completed_count': 0,
            'in_progress_count': 0,
            'blocked_count': 0,
            'not_started_count': 0,
            'completion_percentage': 0.0,
            'status': 'NOT_STARTED'
        }

    # Count by status
    completed_count = 0
    in_progress_count = 0
    blocked_count = 0
    not_started_count = 0

    # Status categories for "in progress"
    in_progress_statuses = [
        SubTaskStatus.REQUIREMENT_IN_PROGRESS,
        SubTaskStatus.DEV_IN_PROGRESS,
        SubTaskStatus.TECH_ONLINE,
        SubTaskStatus.BIZ_ONLINE
    ]

    for st in target_subtasks:
        if st.task_status == SubTaskStatus.COMPLETED:
            completed_count += 1
        elif st.is_blocked or st.task_status == SubTaskStatus.BLOCKED:
            blocked_count += 1
        elif st.task_status == SubTaskStatus.NOT_STARTED:
            not_started_count += 1
        elif st.task_status in in_progress_statuses:
            in_progress_count += 1
        else:
            # Default to in progress for unknown statuses
            in_progress_count += 1

    # Calculate percentage
    completion_percentage = calculate_completion_percentage(completed_count, total_count)

    # Determine status
    status = get_transformation_status(
        total_count=total_count,
        completed_count=completed_count,
        blocked_count=blocked_count,
        not_started_count=not_started_count
    )

    return {
        'subtask_count': total_count,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'blocked_count': blocked_count,
        'not_started_count': not_started_count,
        'completion_percentage': completion_percentage,
        'status': status
    }


def calculate_application_transformation_stats(subtasks: List[SubTask]) -> Dict[str, Any]:
    """
    Calculate comprehensive transformation statistics for an application.

    Args:
        subtasks: List of all subtasks for the application

    Returns:
        Dictionary containing:
            - AK statistics (ak_*)
            - Cloud Native statistics (cloud_native_*)
            - current_phase_description
    """
    # Calculate AK statistics
    ak_stats = calculate_subtask_statistics(subtasks, "AK")

    # Calculate Cloud Native statistics
    cn_stats = calculate_subtask_statistics(subtasks, "云原生")

    # Generate phase description
    phase_description = generate_phase_description(ak_stats['status'], cn_stats['status'])

    return {
        # AK statistics
        'ak_subtask_count': ak_stats['subtask_count'],
        'ak_completed_count': ak_stats['completed_count'],
        'ak_in_progress_count': ak_stats['in_progress_count'],
        'ak_blocked_count': ak_stats['blocked_count'],
        'ak_not_started_count': ak_stats['not_started_count'],
        'ak_completion_percentage': ak_stats['completion_percentage'],
        'ak_status': ak_stats['status'],

        # Cloud Native statistics
        'cloud_native_subtask_count': cn_stats['subtask_count'],
        'cloud_native_completed_count': cn_stats['completed_count'],
        'cloud_native_in_progress_count': cn_stats['in_progress_count'],
        'cloud_native_blocked_count': cn_stats['blocked_count'],
        'cloud_native_not_started_count': cn_stats['not_started_count'],
        'cloud_native_completion_percentage': cn_stats['completion_percentage'],
        'cloud_native_status': cn_stats['status'],

        # Phase description
        'current_phase_description': phase_description
    }
