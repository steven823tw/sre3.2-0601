# V3.2 架构设计

## 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (User Layer)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ SRE 工程师│  │ 一线运维  │  │ 管理层   │  │ 自动化脚本   │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └──────┬───────┘   │
├────────┴─────────────┴────────────┴───────────────┴───────────┤
│                       接入层 (Access Layer)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React SPA (Vite)                                        │  │
│  │  Chat · Dashboard · Resources · Alerts · Operations      │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┴─────────────────────────────────┤
│                        API 层 (API Layer)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI (OpenAPI 3.1)                                   │  │
│  │  /api/v1/chat · /assets · /alerts · /operations          │  │
│  │  JWT Auth · Rate Limiting · Request ID                   │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┴─────────────────────────────────┤
│                      服务层 (Service Layer)                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ ChatService│ │AssetService│ │AlertService│ │ OpService  │  │
│  │ 意图识别   │ │ 资产管理   │ │ 告警处理   │ │ 操作管理   │  │
│  │ 命令推荐   │ │ 搜索过滤   │ │ 状态流转   │ │ 工作流     │  │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘  │
├────────┴──────────────┴──────────────┴──────────────┴─────────┤
│                      仓储层 (Repository Layer)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLAlchemy 2.0 (async)                                  │  │
│  │  Generic CRUD · Query Builder · Connection Pool          │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┴─────────────────────────────────┤
│                       数据层 (Data Layer)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ PostgreSQL 16│  │   Redis 7    │  │   Object Storage     │ │
│  │ 主数据存储    │  │ 缓存/队列    │  │   (MinIO/S3)         │ │
│  │ TimescaleDB  │  │ 会话/锁      │  │   报告/备份          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 核心设计原则

### 1. Engineer Assist

```
用户输入: "web-01 连接超时"
    ↓
IntentRecognizer (规则引擎)
    ↓ 意图: diagnose, 参数: {target: "web-01"}
CommandAdvisor (命令推荐)
    ↓ 推荐: [ping, vm_status, host_metrics]
RiskAssessor (风险评估)
    ↓ 风险: low, 需要确认: false
    ↓
返回: 结构化推荐 + 自然语言说明
```

### 2. 分层架构

每层职责清晰，依赖单向：

```
API Layer     → 只负责 HTTP 协议转换
Service Layer → 只负责业务逻辑
Repository    → 只负责数据访问
Database      → 只负责数据存储
```

### 3. 类型安全

- **后端**: Python 3.12+ type hints + Pydantic v2
- **前端**: TypeScript strict mode + Zod 验证
- **API**: OpenAPI 3.1 自动生成文档

### 4. 审计优先

```
每个操作 → audit_logs 表
每个请求 → request_id 跟踪
每个错误 → structured logging
```

## 组件交互

### Chat 流程

```
1. 用户输入自然语言
2. POST /api/v1/chat
3. IntentRecognizer 解析意图
4. CommandAdvisor 推荐操作
5. RiskAssessor 评估风险
6. 返回推荐列表
7. 用户确认
8. POST /api/v1/chat/confirm
9. OperationService 创建操作
10. 执行原子操作
11. 更新操作状态
12. 返回执行结果
```

### 告警处理流程

```
1. 告警源推送告警
2. POST /api/v1/alerts (webhook)
3. AlertService 创建告警
4. 通知 WebSocket 客户端
5. 前端实时显示
6. 工程师确认/解决
7. 更新告警状态
8. 记录审计日志
```

## 扩展性设计

### 平台适配器

```python
class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    @abstractmethod
    async def connect(self, config: dict) -> bool: ...
    
    @abstractmethod
    async def list_vms(self) -> list[Asset]: ...
    
    @abstractmethod
    async def execute_action(self, action: str, params: dict) -> Result: ...

class VSphereAdapter(PlatformAdapter):
    """VMware vSphere 适配器"""
    ...

class OpenStackAdapter(PlatformAdapter):
    """OpenStack 适配器"""
    ...
```

### 原子操作注册

```python
class AtomicRegistry:
    """原子操作注册表"""
    
    _ops: dict[str, type[AtomicOp]] = {}
    
    def register(self, op_class: type[AtomicOp]) -> None:
        self._ops[op_class.op_id] = op_class
    
    def get(self, op_id: str) -> type[AtomicOp] | None:
        return self._ops.get(op_id)
```

## 安全设计

### 认证

```
JWT Token → Authorization Header → FastAPI Dependency → User Context
```

### 授权

```
User → Role → Permission → Operation
admin    → *     → 全部
sre      → read  → 查询
sre      → write → 操作 (需确认)
operator → read  → 只读
```

### 审计

```
每个 API 请求 → request_id + user_id + timestamp
每个操作 → operation_id + steps + results + duration
每个变更 → before + after + reason
```

## 性能优化

### 数据库

- 连接池: 20 连接 + 10 溢出
- 索引: 40+ 索引覆盖主要查询
- 分区: 大表按月分区
- 缓存: Redis 缓存热点数据

### API

- 异步: FastAPI + asyncpg 全异步
- 分页: 游标分页避免深分页
- 压缩: gzip 响应压缩

### 前端

- 代码分割: 路由级别懒加载
- 虚拟滚动: 大列表虚拟化
- 缓存: TanStack Query 自动缓存
- 预加载: 鼠标悬停预加载数据
