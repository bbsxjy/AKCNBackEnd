-- Add version fields for optimistic locking
-- This migration adds version control to support concurrent write operations

-- Add version field to applications table
ALTER TABLE applications ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Add lock_version field to sub_tasks table (named lock_version to avoid conflict with version_name)
ALTER TABLE sub_tasks ADD COLUMN IF NOT EXISTS lock_version INTEGER NOT NULL DEFAULT 1;

-- Create index on version fields for performance
CREATE INDEX IF NOT EXISTS idx_applications_version ON applications(version);
CREATE INDEX IF NOT EXISTS idx_sub_tasks_lock_version ON sub_tasks(lock_version);

COMMENT ON COLUMN applications.version IS 'Optimistic locking version number';
COMMENT ON COLUMN sub_tasks.lock_version IS 'Optimistic locking version number (named lock_version to avoid conflict with version_name)';
