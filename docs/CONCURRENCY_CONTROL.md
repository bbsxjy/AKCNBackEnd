# 数据库并发控制和读写分离实现文档

## 概述

本系统实现了完整的数据库并发控制机制，包括：
- **读写分离**：支持主从数据库配置，读操作使用从库，写操作使用主库
- **乐观锁**：使用version字段防止并发写入冲突
- **悲观锁**：使用SELECT FOR UPDATE锁定行
- **死锁检测和重试**：自动检测死锁并重试
- **并发安全保证**：确保多用户同时写入时数据一致性

## 1. 读写分离配置

### 1.1 环境变量配置

在 `.env` 文件中配置：

```env
# 主数据库（写操作）
DATABASE_URL=postgresql+asyncpg://akcn_user:akcn_password@主库地址:5432/akcn_dev_db

# 从数据库（读操作，可选）
DATABASE_READ_URL=postgresql+asyncpg://akcn_user:akcn_password@从库地址:5432/akcn_dev_db

# 启用读写分离
ENABLE_READ_WRITE_SPLIT=true
```

### 1.2 如何工作

```
写操作 → DATABASE_URL（主库）
读操作 → DATABASE_READ_URL（从库）或 DATABASE_URL（如未配置从库）
```

**连接池配置**：
- 主库（写）：pool_size=20, max_overflow=40
- 从库（读）：pool_size=30, max_overflow=60（更大的连接池）

### 1.3 使用示例

```python
from app.core.database import get_async_session, get_read_session

# 写操作使用主库
async def update_application(app_id: int):
    async with AsyncSessionLocal() as db:  # 主库
        app = await db.get(Application, app_id)
        app.status = "completed"
        await db.commit()

# 读操作使用从库
async def get_applications():
    async with AsyncReadSessionLocal() as db:  # 从库
        result = await db.execute(select(Application))
        return result.scalars().all()
```

## 2. 乐观锁（Optimistic Locking）

### 2.1 原理

使用version字段跟踪记录版本：
- 每次更新时检查version是否匹配
- 更新后自动递增version
- 如果version不匹配，说明有其他用户已修改，抛出OptimisticLockError

### 2.2 已添加version字段的模型

| 模型 | Version字段 | 说明 |
|------|------------|------|
| Application | version | 应用版本号 |
| SubTask | lock_version | 子任务版本号（避免与version_name冲突） |

### 2.3 使用示例

```python
from app.utils.concurrency import update_with_version_check, OptimisticLockError

async def update_application_status(db, app_id, new_status):
    app = await db.get(Application, app_id)
    current_version = app.version

    try:
        await update_with_version_check(
            db,
            app,
            expected_version=current_version,
            current_status=new_status,
            updated_by=user_id
        )
        logger.info(f"Application {app_id} updated successfully")
    except OptimisticLockError:
        logger.warning(f"Application {app_id} was modified by another user")
        # 重新获取最新数据
        await db.refresh(app)
        # 重试或通知用户
        raise HTTPException(
            status_code=409,
            detail="应用已被其他用户修改，请刷新后重试"
        )
```

## 3. 悲观锁（Pessimistic Locking）

### 3.1 原理

使用SELECT FOR UPDATE锁定数据库行：
- 其他事务必须等待锁释放才能读取/修改
- 适用于高冲突场景
- 可配置nowait或skip_locked

### 3.2 使用方式

#### 方式1：使用LockContext上下文管理器

```python
from app.utils.concurrency import LockContext

async def process_application(db, app_id):
    async with db.begin():
        async with LockContext(db, Application, app_id) as app:
            if app:
                # 这里app已被锁定，其他事务无法修改
                app.status = "processing"
                app.progress = 50
                await db.commit()
            else:
                raise HTTPException(404, "Application not found")
```

#### 方式2：使用acquire_row_lock函数

```python
from app.utils.concurrency import acquire_row_lock

async def batch_update_applications(db, app_ids, new_status):
    async with db.begin():
        for app_id in app_ids:
            app = await acquire_row_lock(
                db,
                Application,
                app_id,
                nowait=False  # 等待锁释放
            )
            if app:
                app.status = new_status
        await db.commit()
```

#### 方式3：跳过已锁定的行

```python
async def try_update_applications(db, app_ids, new_status):
    updated_count = 0
    async with db.begin():
        for app_id in app_ids:
            app = await acquire_row_lock(
                db,
                Application,
                app_id,
                skip_locked=True  # 跳过已锁定的行
            )
            if app:
                app.status = new_status
                updated_count += 1
        await db.commit()
    return updated_count
```

## 4. 死锁检测和自动重试

### 4.1 原理

检测以下异常并自动重试：
- `DeadlockDetectedError`：死锁
- `SerializationError`：序列化失败
- `OptimisticLockError`：乐观锁冲突

### 4.2 使用@with_retry装饰器

```python
from app.utils.concurrency import with_retry

@with_retry(max_retries=3, retry_delay=0.1, exponential_backoff=True)
async def update_multiple_applications(db, updates):
    """
    批量更新应用，自动处理死锁和重试
    """
    async with db.begin():
        for app_id, status in updates.items():
            app = await acquire_row_lock(db, Application, app_id)
            if app:
                app.status = status
        await db.commit()

# 使用
try:
    await update_multiple_applications(db, {1: "completed", 2: "in_progress"})
except DeadlockError:
    logger.error("操作失败：多次重试后仍然死锁")
```

### 4.3 重试策略配置

```python
@with_retry(
    max_retries=5,          # 最多重试5次
    retry_delay=0.2,        # 初始延迟0.2秒
    exponential_backoff=True,  # 指数退避：0.2s, 0.4s, 0.8s, 1.6s, 3.2s
    handle_deadlock=True,   # 处理死锁
    handle_serialization=True  # 处理序列化错误
)
async def critical_operation(db):
    ...
```

## 5. 实际应用场景

### 5.1 场景1：进度计算时的并发更新

**问题**：多个用户同时提交子任务更新，触发应用进度重新计算

**解决方案**：使用乐观锁 + 重试

```python
@with_retry(max_retries=3)
async def update_application_progress(db, app_id):
    app = await db.get(Application, app_id)
    current_version = app.version

    # 计算新进度
    subtasks = await get_subtasks(db, app_id)
    new_progress = calculate_progress(subtasks)

    try:
        await update_with_version_check(
            db,
            app,
            expected_version=current_version,
            progress=new_progress,
            current_status=calculate_status(subtasks)
        )
    except OptimisticLockError:
        # 自动重试
        raise
```

### 5.2 场景2：批量状态更新

**问题**：管理员批量更新多个应用状态，可能与其他用户操作冲突

**解决方案**：使用悲观锁 + skip_locked

```python
async def batch_approve_applications(db, app_ids):
    approved = []
    skipped = []

    async with db.begin():
        for app_id in app_ids:
            # 尝试锁定，如果已被锁定则跳过
            app = await acquire_row_lock(
                db, Application, app_id,
                skip_locked=True
            )
            if app:
                app.status = "approved"
                approved.append(app_id)
            else:
                skipped.append(app_id)
        await db.commit()

    return {
        "approved": approved,
        "skipped": skipped,
        "message": f"已批准{len(approved)}个，跳过{len(skipped)}个正在使用的应用"
    }
```

### 5.3 场景3：Excel批量导入

**问题**：大量数据批量导入可能与现有数据更新冲突

**解决方案**：使用重试 + 事务批处理

```python
@with_retry(max_retries=3)
async def batch_import_applications(db, excel_data):
    batch_size = 100
    total = len(excel_data)

    for i in range(0, total, batch_size):
        batch = excel_data[i:i+batch_size]

        async with db.begin():
            for row in batch:
                # 检查是否存在
                existing = await db.execute(
                    select(Application).where(Application.l2_id == row['l2_id'])
                )
                app = existing.scalar_one_or_none()

                if app:
                    # 使用乐观锁更新
                    await update_with_version_check(
                        db, app,
                        expected_version=app.version,
                        **row
                    )
                else:
                    # 新建
                    new_app = Application(**row, version=1)
                    db.add(new_app)

            await db.commit()
```

## 6. 最佳实践

### 6.1 选择合适的锁策略

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 低并发、偶尔冲突 | 乐观锁 | 性能好，无额外锁开销 |
| 高并发、频繁冲突 | 悲观锁 | 避免频繁重试 |
| 批量操作 | 悲观锁 + skip_locked | 提高吞吐量 |
| 关键数据（如库存） | 悲观锁 + nowait | 快速失败 |
| 长事务 | 避免锁，使用队列 | 减少锁等待时间 |

### 6.2 避免死锁的建议

1. **按固定顺序锁定资源**
   ```python
   # 好：总是按ID升序锁定
   app_ids = sorted([3, 1, 2])
   for app_id in app_ids:
       app = await acquire_row_lock(db, Application, app_id)
   ```

2. **缩短事务时间**
   ```python
   # 坏：在事务中做耗时操作
   async with db.begin():
       app = await acquire_row_lock(db, Application, 1)
       await expensive_calculation()  # ❌
       app.status = "done"

   # 好：先计算，再开事务
   result = await expensive_calculation()
   async with db.begin():
       app = await acquire_row_lock(db, Application, 1)
       app.status = "done"
   ```

3. **使用重试机制**
   ```python
   @with_retry(max_retries=3)
   async def safe_update(...):
       ...
   ```

### 6.3 监控和告警

```python
import logging

logger = logging.getLogger(__name__)

# 在重试装饰器中已包含自动日志记录
# 可以额外添加监控指标

from prometheus_client import Counter

deadlock_counter = Counter('db_deadlocks_total', 'Total number of deadlocks')
retry_counter = Counter('db_retries_total', 'Total number of retries')

# 在重试时增加计数器
deadlock_counter.inc()
retry_counter.inc()
```

## 7. 性能优化

### 7.1 读写分离的性能提升

- 读操作负载分散到从库
- 主库专注于写操作
- 减少主库压力，提高响应速度
- 预期提升：30-50%（取决于读写比例）

### 7.2 连接池调优

```python
# 主库（写）
pool_size=20        # 基础连接数
max_overflow=40     # 最大额外连接
pool_recycle=3600   # 1小时回收连接

# 从库（读）
pool_size=30        # 更大的基础连接数
max_overflow=60     # 更多额外连接
```

### 7.3 锁超时配置

```python
# 在connect_args中设置
connect_args={
    "command_timeout": 60,  # SQL命令超时
    "timeout": 60,          # 连接超时
}
```

## 8. 故障排查

### 8.1 检查死锁

```sql
-- 查看当前锁等待
SELECT * FROM pg_locks WHERE NOT granted;

-- 查看阻塞会话
SELECT
    pid,
    usename,
    application_name,
    state,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

### 8.2 常见错误和解决

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| OptimisticLockError | Version冲突 | 自动重试或提示用户刷新 |
| DeadlockDetectedError | 死锁 | 自动重试，检查锁顺序 |
| Lock timeout | 锁等待超时 | 增加timeout或使用nowait |
| Connection pool exhausted | 连接数不足 | 增加pool_size |

## 9. 迁移检查清单

- [x] 添加version字段到applications表
- [x] 添加lock_version字段到sub_tasks表
- [x] 配置读写分离环境变量
- [x] 创建并发控制工具类
- [x] 在service层添加锁机制
- [ ] 更新所有批量操作使用重试装饰器
- [ ] 添加性能监控和告警
- [ ] 压力测试验证并发性能

## 10. 测试

### 10.1 并发写入测试

```python
import asyncio

async def concurrent_updates():
    tasks = []
    for i in range(10):
        task = asyncio.create_task(
            update_application(db, app_id=1, user_id=i)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if not isinstance(r, Exception))
    print(f"成功: {success}/10")
```

### 10.2 死锁模拟测试

```python
async def simulate_deadlock():
    async def task1(db):
        async with db.begin():
            await acquire_row_lock(db, Application, 1)
            await asyncio.sleep(0.1)
            await acquire_row_lock(db, Application, 2)

    async def task2(db):
        async with db.begin():
            await acquire_row_lock(db, Application, 2)
            await asyncio.sleep(0.1)
            await acquire_row_lock(db, Application, 1)

    # 运行并观察重试机制
    await asyncio.gather(task1(db), task2(db))
```

---

**实施日期**: 2025-10-12
**状态**: ✅ 已实现
**测试状态**: 待验证
**负责人**: Backend Team
