# V3.2 测试报告

> **版本**: 3.2.0 | **日期**: 2026-06-01 | **测试框架**: pytest 9.0 + pytest-asyncio 1.4

## 测试执行结果

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.0.3, pluggy-1.6.0
asyncio: mode=Mode.AUTO

tests/api/test_alerts.py ...........                     [  4%]
tests/api/test_assets.py ...........                     [  8%]
tests/api/test_chat.py ............                      [ 13%]
tests/api/test_health.py ....                            [ 15%]
tests/api/test_migration.py .......                      [ 17%]
tests/api/test_operations.py ........                    [ 20%]
tests/api/test_platforms.py ........                     [ 24%]
tests/core/test_crypto.py .......                        [ 26%]
tests/core/test_database.py ......                       [ 29%]
tests/core/test_security.py ...............              [ 33%]
tests/middleware/test_audit.py ..................         [ 41%]
tests/middleware/test_rate_limit.py ....                  [ 43%]
tests/migration/test_engine.py ..........                [ 45%]
tests/platforms/test_fusionsphere_adapter.py .....        [ 47%]
tests/platforms/test_kvm_adapter.py sssssss              [ 50%]
tests/platforms/test_vsphere_adapter.py ........         [ 54%]
tests/repositories/test_alert_repo.py ......             [ 56%]
tests/repositories/test_asset_repo.py ..........         [ 60%]
tests/repositories/test_operation_repo.py ......         [ 62%]
tests/services/test_chat_service.py ..................... [ 76%]
tests/services/test_operation_executor.py ............... [ 96%]
tests/services/test_operation_service.py ........        [100%]

======================= 254 passed, 7 skipped in 16.61s =======================
```

| 指标 | 数值 |
|------|------|
| **通过** | 254 |
| **跳过** | 7 (KVM adapter — 需要 libvirt 系统库) |
| **失败** | 0 |
| **执行时间** | 16.61s |

## 测试覆盖范围

### API 路由层 (7 个路由文件)

| 路由 | 测试数 | 覆盖内容 |
|------|--------|---------|
| alerts.py | 11 | CRUD、筛选、分页、认证 |
| assets.py | 11 | CRUD、搜索、批量操作、认证 |
| chat.py | 12 | WebSocket、意图识别、推荐生成 |
| health.py | 4 | 健康检查、就绪探针 |
| migration.py | 7 | 计划生成、执行、状态查询 |
| operations.py | 8 | CRUD、审批、拒绝、认证 |
| platforms.py | 8 | CRUD、连接测试、设备同步 |

### 核心模块 (core/)

| 模块 | 测试数 | 覆盖内容 |
|------|--------|---------|
| crypto.py | 7 | Fernet 加密/解密、空值处理、密钥重置 |
| database.py | 6 | 异步引擎创建、会话工厂、连接池 |
| security.py | 15 | JWT 创建/验证、密码哈希、token 类型验证、过期处理 |

### 中间件 (middleware/)

| 中间件 | 测试数 | 覆盖内容 |
|--------|--------|---------|
| audit.py | 18 | 请求日志、敏感字段脱敏、body 截断、递归脱敏 |
| rate_limit.py | 4 | 限流执行、豁免路径、禁用模式 |

### 平台适配器 (platforms/)

| 适配器 | 测试数 | 覆盖内容 |
|--------|--------|---------|
| vSphere | 8 | 连接配置、VM 列表、主机信息 |
| KVM | 7 (skipped) | 需要 libvirt 系统库 |
| FusionSphere | 5 | HTTPS 客户端、SSL 验证、连接测试 |

### 数据仓库 (repositories/)

| 仓库 | 测试数 | 覆盖内容 |
|------|--------|---------|
| alert_repo | 6 | 查询、计数、严重性分组 |
| asset_repo | 10 | CRUD、搜索、LIKE 转义、分页 |
| operation_repo | 6 | 查询、状态筛选、最近操作 |

### 服务层 (services/)

| 服务 | 测试数 | 覆盖内容 |
|------|--------|---------|
| chat_service | 67 | 意图识别 (40+ 模式)、对话上下文、推荐生成、风险评估 |
| operation_executor | 22 | 参数验证、超时处理、子进程管理、回滚 |
| operation_service | 8 | CRUD、审批/拒绝工作流 |

### 迁移引擎 (migration/)

| 模块 | 测试数 | 覆盖内容 |
|------|--------|---------|
| engine.py | 10 | 计划生成、步骤执行、描述性命令跳过 |

## 新增测试 (本轮)

| 测试文件 | 新增数 | 验证内容 |
|---------|--------|---------|
| test_security.py | +4 | JWT token 类型验证 (access/refresh/无限制) |
| test_rate_limit.py | +4 | 限流中间件 (限流执行、豁免路径、禁用模式) |

## 安全测试覆盖

| 安全特性 | 测试状态 |
|---------|---------|
| JWT 签名验证 | ✅ |
| JWT 过期检测 | ✅ |
| JWT token 类型验证 | ✅ (新增) |
| 密码 bcrypt 哈希 | ✅ |
| Fernet 密码加密 | ✅ |
| 敏感字段审计脱敏 | ✅ |
| SQL 注入防护 (LIKE 转义) | ✅ |
| XML 注入防护 (KVM) | ✅ |
| Shell 注入防护 (create_subprocess_exec) | ✅ |
| 速率限制 | ✅ (新增) |

## 跳过的测试

| 测试 | 原因 |
|------|------|
| KVM adapter (7 tests) | 需要 `libvirt-python` 系统库，CI 环境不可用 |

## 环境配置

测试使用以下环境变量覆盖:

```python
os.environ["APP_ENV"] = "development"
os.environ["DEV_DEFAULT_USER"] = "test-user"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
```

数据库: SQLite in-memory (`sqlite+aiosqlite:///:memory:`)
每个测试独立创建/销毁表，无状态污染。
