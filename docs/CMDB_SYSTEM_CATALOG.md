# CMDB系统目录使用指南

## 概述

CMDB系统目录模块用于管理公司的系统和应用配置信息，包括L2应用、156L1系统（当前使用）和87L1系统（未来规划）。该模块提供了完整的API接口和MCP工具支持，可作为智能助手的知识库使用。

## 功能特性

### 1. 数据模型

系统包含三个主要数据表：

- **cmdb_l2_applications**: L2应用信息（53个字段）
  - 基本信息：配置项ID、短名称、英文简称、描述、状态等
  - 管理信息：管理级别、系统产权、开发和运维信息等
  - 业务信息：业务主管单位、联系人、运营单位等
  - L1关联：所属156L1系统、所属87L1系统

- **cmdb_l1_systems_156**: 156L1系统信息（11个字段）
  - 当前使用的L1系统分类
  - 包含域、层、功能、开发单位等信息

- **cmdb_l1_systems_87**: 87L1系统信息（29个字段）
  - 未来规划的L1系统分类（预计到2027年底过渡）
  - 包含更详细的架构、性能、等保等信息

### 2. 数据关系

- L2应用通过"所属156L1系统"和"所属87L1系统"字段关联到L1系统
- 一个L2应用可以同时关联156L1和87L1系统
- 支持虚拟集合（如"EC应用集"、"代建应用集"等）

## 快速开始

### 1. 数据库迁移

```bash
# 应用迁移创建CMDB表
alembic upgrade head
```

### 2. 导入CMDB数据

**方法1：通过API导入**

```bash
curl -X POST "http://localhost:8000/api/v1/cmdb/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "C:\\Users\\Administrator\\Desktop\\TrackerBuilder\\sysmap-L2-156L1和87L-20250807.xlsx",
    "replace_existing": false
  }'
```

**方法2：通过MCP工具导入**

```json
{
  "tool": "cmdb_import",
  "arguments": {
    "file_path": "C:\\Users\\Administrator\\Desktop\\TrackerBuilder\\sysmap-L2-156L1和87L-20250807.xlsx",
    "replace_existing": false
  }
}
```

**方法3：使用Python脚本**

```python
from app.services.cmdb_import_service import CMDBImportService
from app.core.database import get_db_context

async def import_data():
    async with get_db_context()() as db:
        result = await CMDBImportService.import_from_excel(
            db,
            file_path="C:\\Users\\Administrator\\Desktop\\TrackerBuilder\\sysmap-L2-156L1和87L-20250807.xlsx",
            replace_existing=False
        )
        print(f"导入完成: {result}")
```

## API接口说明

### 基础URL
```
http://localhost:8000/api/v1/cmdb
```

所有API请求需要携带JWT Token：
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### L2应用查询

#### 1. 搜索L2应用
```http
GET /cmdb/l2/search?keyword=OA&limit=10
```

查询参数：
- `keyword`: 搜索关键词（搜索短名称、其他名称、配置项ID、描述）
- `status`: 状态筛选
- `management_level`: 管理级别筛选
- `belongs_to_156l1`: 156L1系统筛选
- `belongs_to_87l1`: 87L1系统筛选
- `limit`: 返回数量（1-1000，默认100）
- `offset`: 偏移量（默认0）

响应示例：
```json
[
  {
    "id": 1,
    "config_id": "CI000088354",
    "short_name": "OA网络",
    "status": "正常",
    "management_level": "技术底座，不定级",
    "business_supervisor_unit": "技术部",
    "contact_person": "鲍淼(l:01062363)",
    "dev_unit": "技术部",
    "dev_contact": null,
    "ops_unit": "技术部",
    "ops_contact": null,
    "belongs_to_156l1": null,
    "belongs_to_87l1": null
  }
]
```

#### 2. 获取L2应用详情
```http
GET /cmdb/l2/{config_id}
```

#### 3. 获取L2应用及其关联L1信息（需求场景3）
```http
GET /cmdb/l2/with-l1/{keyword}
```

这个接口满足需求："XX应用的管理级别是多少？其所属156L1系统是什么？"

响应示例：
```json
{
  "found": true,
  "count": 2,
  "applications": [
    {
      "config_id": "CI000088354",
      "short_name": "OA网络",
      "management_level": "技术底座，不定级",
      "business_supervisor_unit": "技术部",
      "contact_person": "鲍淼",
      "l1_156_systems": [
        {
          "config_id": "CI006989726",
          "short_name": "基础设施",
          "management_level": "A",
          "belongs_to_domain": "基础平台",
          "belongs_to_layer": "基础层"
        }
      ],
      "l1_87_systems": [
        {
          "config_id": "CI008167669",
          "short_name": "技术集合",
          "management_level": "A",
          "is_critical_system": "是"
        }
      ]
    }
  ]
}
```

### 156L1系统查询

#### 搜索156L1系统
```http
GET /cmdb/156l1/search?keyword=基础&domain=基础平台
```

查询参数：
- `keyword`: 搜索关键词
- `domain`: 所属域筛选
- `layer`: 所属层筛选
- `limit`: 返回数量

### 87L1系统查询

#### 搜索87L1系统
```http
GET /cmdb/87l1/search?keyword=支付&is_critical=是
```

查询参数：
- `keyword`: 搜索关键词
- `domain`: 所属域筛选
- `layer`: 所属层筛选
- `is_critical`: 是否关键系统筛选
- `limit`: 返回数量

### 关联查询

#### 获取L1系统下的L2应用
```http
GET /cmdb/l1/{l1_type}/{l1_system_name}/applications
```

- `l1_type`: L1类型（"156" 或 "87"）
- `l1_system_name`: L1系统名称

示例：
```http
GET /cmdb/l1/156/基础设施/applications
```

### 统计信息

#### 获取CMDB统计
```http
GET /cmdb/statistics
```

响应示例：
```json
{
  "l2_applications_total": 1500,
  "l1_156_systems_total": 156,
  "l1_87_systems_total": 87,
  "l2_by_status": {
    "正常": 1200,
    "下线": 150,
    "建设中": 150
  },
  "l2_by_management_level": {
    "A": 200,
    "B": 500,
    "C": 800
  }
}
```

## MCP工具使用

系统提供了7个MCP工具，可供AI助手使用：

### 1. cmdb_search_l2
搜索L2应用

```json
{
  "tool": "cmdb_search_l2",
  "arguments": {
    "keyword": "支付",
    "management_level": "A",
    "limit": 50
  }
}
```

### 2. cmdb_get_l2_with_l1
获取L2应用及其关联L1系统信息

```json
{
  "tool": "cmdb_get_l2_with_l1",
  "arguments": {
    "keyword": "网银"
  }
}
```

### 3. cmdb_search_156l1
搜索156L1系统

```json
{
  "tool": "cmdb_search_156l1",
  "arguments": {
    "keyword": "支付",
    "domain": "业务域"
  }
}
```

### 4. cmdb_search_87l1
搜索87L1系统

```json
{
  "tool": "cmdb_search_87l1",
  "arguments": {
    "keyword": "支付",
    "is_critical": "是"
  }
}
```

### 5. cmdb_get_stats
获取统计信息

```json
{
  "tool": "cmdb_get_stats",
  "arguments": {}
}
```

### 6. cmdb_import
导入CMDB数据

```json
{
  "tool": "cmdb_import",
  "arguments": {
    "file_path": "path/to/excel.xlsx",
    "replace_existing": false
  }
}
```

### 7. cmdb_get_l2_by_l1
根据L1系统获取L2应用

```json
{
  "tool": "cmdb_get_l2_by_l1",
  "arguments": {
    "l1_system_name": "支付系统",
    "l1_type": "156"
  }
}
```

## 需求场景示例

### 场景1: 查询L2应用的规范名称和联系人

**问题**: "某个L2应用的规范名称是什么？ID是什么？联系人？开发单位接口人？运维单位接口人？"

**解决方案**:
```http
GET /cmdb/l2/search?keyword=网银
```

或使用MCP工具：
```json
{
  "tool": "cmdb_search_l2",
  "arguments": {
    "keyword": "网银"
  }
}
```

响应会包含：
- 短名称（规范名称）
- 配置项ID
- 业务主管单位
- 联系人
- 系统开发单位
- 系统开发接口人
- 应用软件层运维单位
- 应用软件层运维接口人

### 场景2: 查询系统及应用信息

**问题**: "哪里可以查询系统、应用的信息？"

**解答**:
1. 通过OA主页的"系统及应用"图标访问在线查询页面
2. 通过本系统的API接口查询
3. 通过智能助手（使用MCP工具）查询

### 场景3: 查询应用的管理级别和所属L1系统

**问题**: "XX应用的管理级别是多少？其所属156L1系统是什么？"

**解决方案**:
```http
GET /cmdb/l2/with-l1/XX应用
```

或使用MCP工具：
```json
{
  "tool": "cmdb_get_l2_with_l1",
  "arguments": {
    "keyword": "XX应用"
  }
}
```

### 场景7: 156L1和87L1的区别

**问题**: "156L1系统与87L1系统有什么区别？"

**解答**:
- **156L1**: 当前使用的L1系统，也是对外报送的系统
- **87L1**: 规划的目标态系统，预计到2027年底，156L1系统会过渡到87L1系统

可以查询两种系统：
```http
GET /cmdb/156l1/search?keyword=支付
GET /cmdb/87l1/search?keyword=支付
```

### 场景9: L2应用和L1系统的管理级别关系

**问题**: "L2应用的管理级别与L1系统的管理级别是什么关系？"

**解答**:
L1系统的管理级别取自其关联的L2应用的最高管理级别。

可以通过以下方式验证：
```http
# 获取L1系统下的所有L2应用
GET /cmdb/l1/156/支付系统/applications

# 查看这些L2应用的管理级别，最高级别即为L1的管理级别
```

## 数据维护

### 更新数据

1. **完全替换**: 使用 `replace_existing=true` 导入新的Excel文件
2. **增量更新**: 使用 `replace_existing=false` 只添加新记录

### 数据来源

数据来自公司CMDB系统，由技术部祁凌涛负责维护。

### 联系方式

- 数据问题: 联系技术部祁凌涛
- 接口人调整:
  - 部门内: 发邮件给技术部祁凌涛并抄送新接口人
  - 跨部门: 通过"办公流程——系统备案及域名申请"提交

## 权限说明

- **查询操作**: 所有认证用户可执行
- **导入操作**: 仅管理员（ADMIN角色）可执行

## 技术架构

### 数据层
- SQLAlchemy ORM模型
- PostgreSQL数据库
- 支持异步查询

### 服务层
- `CMDBQueryService`: 查询服务
- `CMDBImportService`: 导入服务

### API层
- FastAPI RESTful接口
- 自动生成OpenAPI文档
- 支持Swagger UI (/docs)

### MCP层
- 7个MCP工具
- 与AI助手无缝集成
- 支持复杂查询场景

## 故障排查

### 导入失败

**问题**: Excel文件导入失败

**解决**:
1. 检查文件路径是否正确
2. 检查Excel文件格式（需要第二行作为列名）
3. 查看错误日志获取详细信息
4. 确认用户有管理员权限

### 查询无结果

**问题**: 搜索关键词没有返回结果

**解决**:
1. 尝试使用更短的关键词
2. 检查是否使用了正确的筛选条件
3. 使用 `GET /cmdb/statistics` 检查数据是否已导入

### 性能问题

**问题**: 查询响应慢

**解决**:
1. 使用筛选条件缩小查询范围
2. 减少 `limit` 参数值
3. 检查数据库索引是否正常
4. 考虑添加缓存（Redis）

## 开发说明

### 添加新字段

1. 修改模型文件 `app/models/cmdb_*.py`
2. 创建新的数据库迁移
3. 更新Schema `app/schemas/cmdb.py`
4. 更新服务逻辑
5. 更新API文档

### 测试

```bash
# 运行所有测试
pytest tests/

# 测试CMDB相关功能
pytest tests/test_cmdb.py -v
```

## 相关文档

- [API文档](http://localhost:8000/docs)
- [MCP协议规范](https://modelcontextprotocol.io/)
- [项目README](../README.md)
- [开发指南](../CLAUDE.md)

## 版本历史

- **v1.0.0** (2025-01-14)
  - 初始版本
  - 支持L2应用、156L1、87L1三种数据类型
  - 完整的API和MCP工具支持
  - Excel数据导入功能

---

**最后更新**: 2025-01-14
**维护者**: AKCN项目团队
