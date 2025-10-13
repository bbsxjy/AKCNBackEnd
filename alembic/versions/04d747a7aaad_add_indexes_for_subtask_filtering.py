"""add_indexes_for_subtask_filtering

Revision ID: 04d747a7aaad
Revises:
Create Date: 2025-10-13 20:43:21.306425

Add indexes to improve performance for transformation statistics filtering:
- subtasks.l2_id (already exists as FK, but ensure indexed)
- subtasks.sub_target for filtering by AK/Cloud Native
- subtasks.task_status for status filtering
- subtasks.is_blocked for blocked task filtering
- Composite index on (l2_id, sub_target, task_status, is_blocked) for complex queries

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04d747a7aaad'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create index on subtasks.sub_target
    op.create_index(
        'idx_subtasks_sub_target',
        'sub_tasks',
        ['sub_target'],
        unique=False
    )

    # Create index on subtasks.task_status
    op.create_index(
        'idx_subtasks_task_status',
        'sub_tasks',
        ['task_status'],
        unique=False
    )

    # Create index on subtasks.is_blocked
    op.create_index(
        'idx_subtasks_is_blocked',
        'sub_tasks',
        ['is_blocked'],
        unique=False
    )

    # Create composite index for complex filtering queries
    # This will speed up queries that filter by multiple conditions
    op.create_index(
        'idx_subtasks_lookup',
        'sub_tasks',
        ['l2_id', 'sub_target', 'task_status', 'is_blocked'],
        unique=False
    )

    # Additional indexes for application filtering
    op.create_index(
        'idx_applications_belonging_projects',
        'applications',
        ['belonging_projects'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('idx_applications_belonging_projects', table_name='applications')
    op.drop_index('idx_subtasks_lookup', table_name='sub_tasks')
    op.drop_index('idx_subtasks_is_blocked', table_name='sub_tasks')
    op.drop_index('idx_subtasks_task_status', table_name='sub_tasks')
    op.drop_index('idx_subtasks_sub_target', table_name='sub_tasks')