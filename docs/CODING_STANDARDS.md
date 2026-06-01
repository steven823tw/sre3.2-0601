# V3.1 编码规范

## Python (后端)

### 命名规范

```python
# 模块名: snake_case
asset_service.py
alert_repository.py

# 类名: PascalCase
class AssetService:
class AlertRepository:

# 函数/方法: snake_case
async def get_assets() -> list[Asset]:
def _validate_params(params: dict) -> None:  # 私有函数前缀 _

# 常量: UPPER_SNAKE_CASE
MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50

# 变量: snake_case
asset_count = 0
is_connected = True
```

### 类型提示

```python
# 必须添加返回类型
async def get_asset(asset_id: UUID) -> Asset | None:
    ...

# 必须添加参数类型
def process_alert(alert: Alert, severity: str) -> bool:
    ...

# 使用 modern union syntax (Python 3.10+)
def get_status() -> str | None:  # 好
def get_status() -> Optional[str]:  # 也可以，但不推荐

# 复杂类型用 TypeAlias
AssetList = list[Asset]
AlertFilter = dict[str, str | int]
```

### Docstring

```python
async def get_assets(
    asset_type: AssetType | None = None,
    platform: str | None = None,
    status: AssetStatus | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> PaginatedResult[Asset]:
    """获取资产列表，支持过滤和分页。

    Args:
        asset_type: 资产类型过滤 (vm/physical/storage/network)
        platform: 平台过滤 (vSphere/FusionSphere/KVM)
        status: 状态过滤 (running/stopped/error)
        search: 名称或 IP 模糊搜索
        page: 页码 (从 1 开始)
        limit: 每页条数 (最大 200)

    Returns:
        分页结果，包含 items, total, page, limit, pages

    Raises:
        ValidationError: 参数校验失败
    """
```

### 错误处理

```python
# 自定义异常层次
class V3Error(Exception):
    """Base exception for V3 platform"""
    code: str = "INTERNAL_ERROR"
    status_code: int = 500

class NotFoundError(V3Error):
    code = "NOT_FOUND"
    status_code = 404

class ValidationError(V3Error):
    code = "VALIDATION_ERROR"
    status_code = 422

class ConflictError(V3Error):
    code = "CONFLICT"
    status_code = 409

# 不要 bare except
try:
    await do_something()
except SpecificError as e:
    logger.error("Failed", error=str(e))
    raise
```

### 日志

```python
import structlog

logger = structlog.get_logger(__name__)

# 结构化日志
logger.info(
    "Asset retrieved",
    asset_id=str(asset_id),
    asset_type=asset.type,
    duration_ms=elapsed,
)

# 错误日志
logger.error(
    "Failed to connect to platform",
    platform=platform_id,
    error=str(exc),
    exc_info=True,
)
```

---

## TypeScript (前端)

### 命名规范

```typescript
// 文件名: PascalCase (组件) | camelCase (工具/hooks)
AlertCard.tsx        // 组件
useAlerts.ts         // Hook
formatTime.ts        // 工具函数
alertTypes.ts        // 类型定义

// 组件: PascalCase
export function AlertCard({ alert }: AlertCardProps) { ... }

// Hooks: camelCase, use 前缀
export function useAlerts(filter: AlertFilter) { ... }

// 工具函数: camelCase
export function formatTime(iso: string): string { ... }

// 常量: UPPER_SNAKE_CASE
const MAX_PAGE_SIZE = 200;

// 类型/接口: PascalCase
interface AlertCardProps { ... }
type AlertSeverity = 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
```

### 组件模式

```typescript
// 1. 明确的 Props 接口
interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (id: string) => void;
  onResolve?: (id: string) => void;
}

// 2. 使用 cn() 拼接 className
import { cn } from '@/utils/cn';

export function AlertCard({ alert, onAcknowledge }: AlertCardProps) {
  return (
    <div className={cn(
      'rounded-lg border p-4 transition-colors',
      'border-v3-border bg-v3-bg-secondary hover:bg-v3-bg-tertiary',
      alert.severity === 'P0' && 'border-l-2 border-l-red-500',
    )}>
      ...
    </div>
  );
}

// 3. 不要使用 React.FC (已弃用)
// 好: export function AlertCard(props: AlertCardProps) { ... }
// 坏: export const AlertCard: React.FC<AlertCardProps> = (props) => { ... }
```

### 状态管理

```typescript
// Zustand store 模式
import { create } from 'zustand';

interface UIState {
  sidebarCollapsed: boolean;
  activeModal: string | null;
  toasts: Toast[];
  
  toggleSidebar: () => void;
  openModal: (id: string) => void;
  closeModal: () => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  activeModal: null,
  toasts: [],
  
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
  addToast: (toast) => set((s) => ({
    toasts: [...s.toasts, { ...toast, id: crypto.randomUUID() }],
  })),
  removeToast: (id) => set((s) => ({
    toasts: s.toasts.filter((t) => t.id !== id),
  })),
}));
```

### API 调用

```typescript
// TanStack Query 模式
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useAlerts(filter: AlertFilter) {
  return useQuery({
    queryKey: ['alerts', filter],
    queryFn: () => fetchAlerts(filter),
    staleTime: 30_000,  // 30 秒内不重新请求
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => acknowledgeAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}
```

---

## SQL (数据库)

### 命名规范

```sql
-- 表名: snake_case, 复数
CREATE TABLE assets (...);
CREATE TABLE alerts (...);
CREATE TABLE operation_steps (...);

-- 列名: snake_case
created_at TIMESTAMP WITH TIME ZONE
is_active BOOLEAN

-- 索引: idx_{table}_{columns}
CREATE INDEX idx_assets_name ON assets (name);
CREATE INDEX idx_alerts_severity_status ON alerts (severity, status);

-- 外键: fk_{table}_{referenced_table}
ALTER TABLE operation_steps ADD CONSTRAINT fk_operation_steps_operations
  FOREIGN KEY (operation_id) REFERENCES operations (id);

-- 检查约束: ck_{table}_{check}
ALTER TABLE alerts ADD CONSTRAINT ck_alerts_severity
  CHECK (severity IN ('P0', 'P1', 'P2', 'P3', 'P4'));
```

---

## Git 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat` — 新功能
- `fix` — 修复 bug
- `refactor` — 重构（不改变功能）
- `test` — 添加测试
- `docs` — 文档
- `chore` — 构建/工具

**示例**:
```
feat(chat): 实现意图识别引擎，支持 8 种自然语言模式

- 添加 IntentRecognizer 类
- 支持: 诊断/重启/关机/开机/快照/查看告警/查看资源/帮助
- 正则匹配 + 参数提取
- 单元测试覆盖 10+ 场景

Closes #42
```
