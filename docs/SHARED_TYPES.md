# V3.1 共享类型定义

> 前后端共用的类型定义。前端用 TypeScript，后端用 Pydantic，保持字段名一致。

## 资产 (Asset)

```typescript
// TypeScript
type AssetType = 'vm' | 'physical' | 'storage' | 'network';
type AssetStatus = 'running' | 'stopped' | 'error' | 'maintenance' | 'migrating';
type Platform = 'vSphere' | 'FusionSphere' | 'KVM' | 'OpenStack' | 'Physical';

interface Asset {
  id: string;
  type: AssetType;
  name: string;
  ip_address: string;
  platform: Platform;
  status: AssetStatus;
  cpu: number;
  memory_gb: number;
  disk_gb: number;
  cluster: string;
  host: string;
  os_type: string;
  os_version: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
```

```python
# Pydantic
from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class AssetType(str, Enum):
    vm = "vm"
    physical = "physical"
    storage = "storage"
    network = "network"

class AssetStatus(str, Enum):
    running = "running"
    stopped = "stopped"
    error = "error"
    maintenance = "maintenance"
    migrating = "migrating"

class Asset(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    type: AssetType
    name: str
    ip_address: str
    platform: str
    status: AssetStatus
    cpu: int
    memory_gb: int
    disk_gb: int
    cluster: str
    host: str
    os_type: str
    os_version: str
    metadata: dict
    created_at: datetime
    updated_at: datetime
```

## 告警 (Alert)

```typescript
type AlertSeverity = 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
type AlertStatus = 'active' | 'acknowledged' | 'resolved';

interface Alert {
  id: string;
  title: string;
  description: string;
  severity: AlertSeverity;
  status: AlertStatus;
  source: string;
  resource_type: string;
  resource_name: string;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}
```

## 操作 (Operation)

```typescript
type OperationType = 'change' | 'incident' | 'inspection' | 'deploy';
type OperationStatus = 'pending' | 'approved' | 'running' | 'completed' | 'failed' | 'cancelled';
type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

interface Operation {
  id: string;
  type: OperationType;
  title: string;
  description: string;
  risk_level: RiskLevel;
  status: OperationStatus;
  steps: OperationStep[];
  created_by: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

interface OperationStep {
  step: number;
  action: string;
  description: string;
  params: Record<string, unknown>;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  result: unknown | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}
```

## 聊天 (Chat)

```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  recommendations?: Recommendation[];
  operation_id?: string;
}

interface Recommendation {
  step: number;
  action: string;
  description: string;
  params: Record<string, unknown>;
  risk_level: RiskLevel;
  estimated_time_ms: number;
}
```

## 仪表盘 (Dashboard)

```typescript
interface DashboardSummary {
  assets: {
    vms: { total: number; running: number; stopped: number };
    hosts: { total: number; online: number; maintenance: number };
    storage: { total: number; warning: number };
  };
  alerts: {
    active: number;
    critical: number;
    warning: number;
  };
  operations: {
    pending: number;
    running: number;
    completed_today: number;
  };
}

interface TrendPoint {
  date: string;
  avg: number;
  max: number;
}
```

## API 响应

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

interface PaginatedResponse<T> {
  success: boolean;
  data: {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}
```
