# CMDB系统目录 - 快速开始指南

## 简介

本指南帮助您快速开始使用CMDB系统目录模块，该模块用于管理公司的L2应用和L1系统信息，并作为MCP资源库供AI助手使用。

## 5分钟快速开始

### 步骤1: 应用数据库迁移

```bash
# 在项目根目录执行
cd D:\Program Files\Repos\AKCNBackEnd
alembic upgrade head
```

这将创建3个新表：
- `cmdb_l2_applications` - L2应用信息
- `cmdb_l1_systems_156` - 156L1系统（当前使用）
- `cmdb_l1_systems_87` - 87L1系统（未来规划）

### 步骤2: 导入CMDB数据

使用Python脚本导入数据：

```python
import asyncio
from app.services.cmdb_import_service import CMDBImportService
from app.core.database import get_db_context

async def import_cmdb_data():
    async with get_db_context()() as db:
        result = await CMDBImportService.import_from_excel(
            db,
            file_path=r"C:\Users\Administrator\Desktop\TrackerBuilder\sysmap-L2-156L1和87L-20250807.xlsx",
            replace_existing=False
        )

        print(f"✅ 导入完成!")
        print(f"   - L2应用: {result['l2_applications']['imported']} 条")
        print(f"   - 156L1系统: {result['l1_156_systems']['imported']} 条")
        print(f"   - 87L1系统: {result['l1_87_systems']['imported']} 条")
        print(f"   - 总耗时: {result['duration_seconds']:.2f} 秒")

# 运行导入
asyncio.run(import_cmdb_data())
```

保存为 `import_cmdb.py` 并运行：
```bash
python import_cmdb.py
```

### 步骤3: 验证数据导入

启动服务器：
```bash
uvicorn app.main:app --reload
```

访问API文档查看CMDB接口：
```
http://localhost:8000/docs#/cmdb
```

或者通过API验证：
```bash
curl -X GET "http://localhost:8000/api/v1/cmdb/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 常见使用场景

### 场景1: 查询某个应用的详细信息

**问题**: "网银系统的管理级别是多少？联系人是谁？"

**API调用**:
```bash
curl -X GET "http://localhost:8000/api/v1/cmdb/l2/with-l1/网银" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**MCP工具**:
```json
{
  "tool": "cmdb_get_l2_with_l1",
  "arguments": {
    "keyword": "网银"
  }
}
```

### 场景2: 查看某个L1系统下的所有应用

**问题**: "支付系统下有哪些L2应用？"

**API调用**:
```bash
curl -X GET "http://localhost:8000/api/v1/cmdb/l1/156/支付系统/applications" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**MCP工具**:
```json
{
  "tool": "cmdb_get_l2_by_l1",
  "arguments": {
    "l1_system_name": "支付系统",
    "l1_type": "156"
  }
}
```

### 场景3: 搜索A级管理级别的应用

**API调用**:
```bash
curl -X GET "http://localhost:8000/api/v1/cmdb/l2/search?management_level=A&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**MCP工具**:
```json
{
  "tool": "cmdb_search_l2",
  "arguments": {
    "management_level": "A",
    "limit": 50
  }
}
```

## MCP资源库配置

### 在Claude Desktop中使用

1. 确保MCP服务器正在运行：
```bash
cd D:\Program Files\Repos\AKCNBackEnd
python -m app.mcp.run_server
```

2. 在Claude Desktop配置文件中添加：
```json
{
  "mcpServers": {
    "akcn-cmdb": {
      "command": "python",
      "args": [
        "-m",
        "app.mcp.run_server"
      ],
      "cwd": "D:\\Program Files\\Repos\\AKCNBackEnd",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://akcn_user:akcn_password@localhost:5432/akcn_dev_db"
      }
    }
  }
}
```

3. 重启Claude Desktop，现在可以直接询问：
   - "网银系统的管理级别是什么？"
   - "支付系统有多少个关联的L2应用？"
   - "帮我查找所有A级管理级别的系统"

## 可用的MCP工具

系统提供7个MCP工具供AI助手使用：

| 工具名称 | 功能 | 示例 |
|---------|------|------|
| `cmdb_search_l2` | 搜索L2应用 | 搜索关键词、按状态/管理级别筛选 |
| `cmdb_get_l2_with_l1` | 获取L2及其L1信息 | 完整的应用和系统关联信息 |
| `cmdb_search_156l1` | 搜索156L1系统 | 查询当前L1系统分类 |
| `cmdb_search_87l1` | 搜索87L1系统 | 查询未来L1系统分类 |
| `cmdb_get_stats` | 获取统计信息 | 总览CMDB数据统计 |
| `cmdb_import` | 导入数据 | 从Excel导入CMDB数据 |
| `cmdb_get_l2_by_l1` | 按L1查询L2 | 查看L1下的所有L2应用 |

## API端点概览

### L2应用相关
- `GET /cmdb/l2/search` - 搜索L2应用
- `GET /cmdb/l2/{config_id}` - 获取L2应用详情
- `GET /cmdb/l2/with-l1/{keyword}` - 获取L2及其L1系统信息

### L1系统相关
- `GET /cmdb/156l1/search` - 搜索156L1系统
- `GET /cmdb/87l1/search` - 搜索87L1系统
- `GET /cmdb/l1/{l1_type}/{l1_system_name}/applications` - 获取L1下的L2应用

### 管理功能
- `GET /cmdb/statistics` - 获取统计信息
- `POST /cmdb/import` - 导入CMDB数据（仅管理员）

## 数据字段说明

### L2应用核心字段

| 字段 | 说明 | 示例 |
|------|------|------|
| config_id | 配置项ID（唯一） | CI000088354 |
| short_name | 短名称（规范名称） | OA网络 |
| management_level | 管理级别 | A/B/C |
| status | 状态 | 正常/下线/建设中 |
| contact_person | 联系人 | 张三(l:12345678) |
| dev_unit | 系统开发单位 | 技术部 |
| ops_unit | 运维单位 | 运维部 |
| belongs_to_156l1 | 所属156L1系统 | 支付系统 |
| belongs_to_87l1 | 所属87L1系统 | 核心支付平台 |

### 156L1系统核心字段

| 字段 | 说明 |
|------|------|
| config_id | 配置项ID |
| short_name | 短名称 |
| belongs_to_domain | 所属域 |
| belongs_to_layer | 所属层 |
| management_level | 管理级别 |

### 87L1系统核心字段

| 字段 | 说明 |
|------|------|
| config_id | 配置项ID |
| short_name | 短名称 |
| is_critical_system | 是否关键系统 |
| peak_tps | 峰值TPS |
| deployment_architecture | 部署架构 |

## 常见问题

### Q: 156L1和87L1有什么区别？

**A**:
- 156L1是当前使用的L1系统分类（156个）
- 87L1是未来规划的目标态分类（87个）
- 预计到2027年底，156L1会过渡到87L1

### Q: 如何更新CMDB数据？

**A**:
1. 获取最新的Excel文件
2. 使用 `cmdb_import` 工具或API导入
3. 设置 `replace_existing=true` 可完全替换现有数据

### Q: 数据来源是什么？

**A**:
数据来自公司CMDB系统，由技术部祁凌涛负责维护。如有数据问题请联系技术部。

### Q: 谁可以使用这些功能？

**A**:
- 查询功能：所有认证用户
- 导入功能：仅管理员（ADMIN角色）

## 下一步

- 📖 查看[完整文档](./CMDB_SYSTEM_CATALOG.md)了解所有功能
- 🚀 阅读[API文档](http://localhost:8000/docs)查看详细接口
- 🤖 配置MCP服务让AI助手使用CMDB数据
- 📊 使用统计接口了解系统概况

## 技术支持

- **数据问题**: 联系技术部祁凌涛
- **系统问题**: 提交Issue到项目仓库
- **功能建议**: 通过项目管理系统提交需求

---

**版本**: v1.0.0
**更新时间**: 2025-01-14
