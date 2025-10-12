-- =====================================
-- AKCN数据库表创建脚本 - akcn_dev_db
-- =====================================

-- 删除已存在的表（如果需要）
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS sub_tasks CASCADE;
DROP TABLE IF EXISTS applications CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 创建用户角色枚举类型
DROP TYPE IF EXISTS userrole CASCADE;
CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'EDITOR', 'VIEWER');

-- =====================================
-- 1. 用户表
-- =====================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    sso_user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(200),
    department VARCHAR(100),
    role userrole DEFAULT 'VIEWER',
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 2. 应用程序表
-- =====================================
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    l2_id VARCHAR(50) UNIQUE NOT NULL,
    app_name VARCHAR(200) NOT NULL,
    ak_supervision_acceptance_year INTEGER,
    overall_transformation_target VARCHAR(50),
    is_ak_completed BOOLEAN DEFAULT false,
    is_cloud_native_completed BOOLEAN DEFAULT false,
    current_transformation_phase VARCHAR(100),
    current_status VARCHAR(50),
    app_tier INTEGER,
    belonging_l1_name VARCHAR(200),
    belonging_projects VARCHAR(500),
    is_domain_transformation_completed BOOLEAN DEFAULT false,
    is_dbpm_transformation_completed BOOLEAN DEFAULT false,
    dev_mode VARCHAR(50),
    ops_mode VARCHAR(50),
    dev_owner VARCHAR(100),
    dev_team VARCHAR(200),
    ops_owner VARCHAR(100),
    ops_team VARCHAR(200),
    belonging_kpi VARCHAR(100),
    acceptance_status VARCHAR(50),
    planned_requirement_date DATE,
    planned_release_date DATE,
    planned_tech_online_date DATE,
    planned_biz_online_date DATE,
    actual_requirement_date DATE,
    actual_release_date DATE,
    actual_tech_online_date DATE,
    actual_biz_online_date DATE,
    is_delayed BOOLEAN DEFAULT false,
    delay_days INTEGER DEFAULT 0,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 3. 子任务表
-- =====================================
CREATE TABLE sub_tasks (
    id SERIAL PRIMARY KEY,
    l2_id INTEGER REFERENCES applications(id),
    app_name VARCHAR(200),
    sub_target VARCHAR(50),
    version_name VARCHAR(50),
    task_status VARCHAR(50),
    progress_percentage INTEGER DEFAULT 0,
    is_blocked BOOLEAN DEFAULT false,
    block_reason TEXT,
    resource_applied BOOLEAN DEFAULT false,
    ops_requirement_submitted TIMESTAMP WITHOUT TIME ZONE,
    ops_testing_status VARCHAR(50),
    launch_check_status VARCHAR(50),
    planned_requirement_date DATE,
    planned_release_date DATE,
    planned_tech_online_date DATE,
    planned_biz_online_date DATE,
    actual_requirement_date DATE,
    actual_release_date DATE,
    actual_tech_online_date DATE,
    actual_biz_online_date DATE,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 4. 通知表
-- =====================================
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200),
    message TEXT,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 5. 审计日志表
-- =====================================
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    record_id INTEGER,
    operation VARCHAR(50),
    old_values JSON,
    new_values JSON,
    changed_fields JSON,
    request_id VARCHAR(100),
    user_ip VARCHAR(50),
    user_agent TEXT,
    reason TEXT,
    extra_data JSON,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 创建索引以提高查询性能
-- =====================================
CREATE INDEX idx_users_sso_user_id ON users(sso_user_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

CREATE INDEX idx_applications_l2_id ON applications(l2_id);
CREATE INDEX idx_applications_status ON applications(current_status);
CREATE INDEX idx_applications_year ON applications(ak_supervision_acceptance_year);

CREATE INDEX idx_sub_tasks_l2_id ON sub_tasks(l2_id);
CREATE INDEX idx_sub_tasks_status ON sub_tasks(task_status);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- =====================================
-- 验证表创建
-- =====================================
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;