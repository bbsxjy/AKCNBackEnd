-- ==========================================
-- AKCN数据库查询脚本 - pgAdmin使用
-- ==========================================

-- 1. 查看所有应用数据
SELECT * FROM applications ORDER BY created_at DESC;

-- 2. 查看所有子任务数据
SELECT * FROM sub_tasks ORDER BY application_id, created_at DESC;

-- 3. 查看用户数据
SELECT * FROM users;

-- 4. 查看审计日志
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100;

-- 5. 查看通知
SELECT * FROM notifications ORDER BY created_at DESC;

-- ==========================================
-- 统计查询
-- ==========================================

-- 6. 应用统计概览
SELECT
    COUNT(*) as total_apps,
    COUNT(CASE WHEN overall_status = '待启动' THEN 1 END) as pending,
    COUNT(CASE WHEN overall_status = '研发进行中' THEN 1 END) as in_progress,
    COUNT(CASE WHEN overall_status = '业务上线中' THEN 1 END) as deploying,
    COUNT(CASE WHEN overall_status = '全部完成' THEN 1 END) as completed
FROM applications;

-- 7. 每个应用的子任务数量
SELECT
    a.l2_id,
    a.app_name,
    COUNT(s.id) as subtask_count,
    a.overall_status,
    a.progress_percentage
FROM applications a
LEFT JOIN sub_tasks s ON a.id = s.application_id
GROUP BY a.id, a.l2_id, a.app_name, a.overall_status, a.progress_percentage
ORDER BY a.l2_id;

-- 8. 子任务状态分布
SELECT
    task_status,
    COUNT(*) as count
FROM sub_tasks
GROUP BY task_status
ORDER BY count DESC;

-- 9. 按团队分组的应用
SELECT
    responsible_team,
    COUNT(*) as app_count,
    AVG(progress_percentage) as avg_progress
FROM applications
GROUP BY responsible_team
ORDER BY app_count DESC;

-- 10. 延期应用（实际日期超过计划日期）
SELECT
    l2_id,
    app_name,
    planned_biz_online_date,
    actual_biz_online_date,
    actual_biz_online_date - planned_biz_online_date as delay_days
FROM applications
WHERE actual_biz_online_date > planned_biz_online_date
ORDER BY delay_days DESC;

-- ==========================================
-- 数据完整性检查
-- ==========================================

-- 11. 检查是否有重复的L2 ID
SELECT l2_id, COUNT(*) as count
FROM applications
GROUP BY l2_id
HAVING COUNT(*) > 1;

-- 12. 检查孤立的子任务（没有对应的应用）
SELECT s.*
FROM sub_tasks s
LEFT JOIN applications a ON s.application_id = a.id
WHERE a.id IS NULL;

-- 13. 查看最近创建的应用
SELECT
    l2_id,
    app_name,
    overall_status,
    created_at,
    updated_at
FROM applications
ORDER BY created_at DESC
LIMIT 10;

-- 14. 查看最近修改的子任务
SELECT
    s.id,
    a.l2_id,
    s.module_name,
    s.task_status,
    s.updated_at
FROM sub_tasks s
JOIN applications a ON s.application_id = a.id
ORDER BY s.updated_at DESC
LIMIT 10;

-- ==========================================
-- 导入数据检查
-- ==========================================

-- 15. 查看今天导入的数据
SELECT
    'Applications' as table_name,
    COUNT(*) as count
FROM applications
WHERE DATE(created_at) = CURRENT_DATE
UNION ALL
SELECT
    'SubTasks' as table_name,
    COUNT(*) as count
FROM sub_tasks
WHERE DATE(created_at) = CURRENT_DATE;

-- 16. 查看所有表的记录数
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;