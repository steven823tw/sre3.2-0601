# V3.2 API 契约

> 前后端分离开发的接口约定。所有端点以 `/api/v1` 为前缀。

## 通用约定

### 请求格式

```
Content-Type: application/json
Authorization: Bearer <jwt_token>  (除 /health 和 /chat 外)
X-Request-ID: <uuid>  (自动生成)
```

### 响应格式

**成功响应**:
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**分页响应**:
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "total": 1284,
    "page": 1,
    "limit": 50,
    "pages": 26
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "ASSET_NOT_FOUND",
    "message": "资源 web-01 未找到",
    "details": { ... }
  }
}
```

### 分页参数

所有列表端点支持:
- `page` (int, default 1) — 页码
- `limit` (int, default 50, max 200) — 每页条数

### 排序参数

- `sort_by` (string) — 排序字段
- `sort_order` (string) — `asc` | `desc`

---

## 1. 健康检查

### `GET /api/v1/health`

```json
{
  "status": "ok",
  "version": "3.2.0",
  "env": "development",
  "timestamp": "2026-05-30T10:00:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

---

## 2. 聊天 (Chat)

### `POST /api/v1/chat`

**请求**:
```json
{
  "message": "web-01 连接超时了",
  "conversation_id": "optional-uuid"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv-uuid",
    "message_id": "msg-uuid",
    "intent": "diagnose",
    "confidence": 0.92,
    "recommendations": [
      {
        "step": 1,
        "action": "infra.ping",
        "description": "检查网络可达性",
        "params": {"target": "10.0.1.51"},
        "risk_level": "low",
        "estimated_time_ms": 5000
      },
      {
        "step": 2,
        "action": "compute.vm_status",
        "description": "检查虚拟机状态",
        "params": {"vm": "web-01"},
        "risk_level": "low",
        "estimated_time_ms": 10000
      }
    ],
    "needs_confirmation": false,
    "message": "建议先检查网络可达性，再查看 VM 状态。点击执行开始诊断。"
  }
}
```

### `POST /api/v1/chat/confirm`

**请求**:
```json
{
  "conversation_id": "conv-uuid",
  "message_id": "msg-uuid",
  "action": "confirm"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "operation_id": "op-uuid",
    "status": "running",
    "steps": [
      {"step": 1, "action": "infra.ping", "status": "completed", "result": "10.0.1.51 is alive"},
      {"step": 2, "action": "compute.vm_status", "status": "running"}
    ]
  }
}
```

---

## 3. 资产 (Assets)

### `GET /api/v1/assets`

**查询参数**:
- `type` — `vm` | `physical` | `storage` | `network`
- `platform` — `vSphere` | `FusionSphere` | `KVM` | `OpenStack`
- `status` — `running` | `stopped` | `error` | `maintenance`
- `cluster` — 集群名称
- `search` — 名称/IP 模糊搜索

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "vm-uuid-001",
        "type": "vm",
        "name": "web-01",
        "ip_address": "10.0.1.51",
        "platform": "vSphere",
        "status": "running",
        "cpu": 4,
        "memory_gb": 16,
        "disk_gb": 200,
        "cluster": "PRD",
        "host": "esxi-03",
        "os_type": "CentOS",
        "os_version": "7.9",
        "created_at": "2026-01-15T08:00:00Z"
      }
    ],
    "total": 1284,
    "page": 1,
    "limit": 50
  }
}
```

### `GET /api/v1/assets/{id}`

返回单个资产的完整信息（包含快照、监控数据等）。

### `GET /api/v1/assets/{id}/metrics`

**查询参数**:
- `hours` (int, default 24) — 查询时间范围

**响应**:
```json
{
  "success": true,
  "data": {
    "asset_id": "vm-uuid-001",
    "metrics": [
      {
        "timestamp": "2026-05-30T10:00:00Z",
        "cpu_percent": 45.2,
        "memory_percent": 62.8,
        "disk_read_iops": 120,
        "disk_write_iops": 85,
        "network_in_mbps": 12.5,
        "network_out_mbps": 8.3
      }
    ]
  }
}
```

### `POST /api/v1/assets/{id}/actions`

**请求**:
```json
{
  "action": "restart",
  "params": {"graceful": true}
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "operation_id": "op-uuid",
    "status": "pending",
    "risk_level": "medium",
    "needs_approval": true
  }
}
```

---

## 4. 告警 (Alerts)

### `GET /api/v1/alerts`

**查询参数**:
- `severity` — `P0` | `P1` | `P2` | `P3` | `P4`
- `status` — `active` | `acknowledged` | `resolved`
- `resource_type` — `VM` | `Host` | `Datastore` | `Network`
- `hours` (int, default 168) — 查询时间范围

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "alert-uuid-001",
        "title": "db-01 连接超时",
        "description": "数据库主节点 ping 无响应超过 30s",
        "severity": "P0",
        "status": "active",
        "source": "Prometheus",
        "resource_type": "VM",
        "resource_name": "db-01",
        "created_at": "2026-05-30T09:32:00Z",
        "acknowledged_at": null,
        "resolved_at": null
      }
    ],
    "total": 50,
    "summary": {
      "P0": 3, "P1": 8, "P2": 15, "P3": 20, "P4": 4
    }
  }
}
```

### `PUT /api/v1/alerts/{id}/acknowledge`

```json
{
  "comment": "正在排查"
}
```

### `PUT /api/v1/alerts/{id}/resolve`

```json
{
  "resolution": "已修复: 重启网络服务",
  "root_cause": "网络服务进程异常退出"
}
```

---

## 5. 操作 (Operations)

### `GET /api/v1/operations`

**查询参数**:
- `status` — `pending` | `approved` | `running` | `completed` | `failed`
- `type` — `change` | `incident` | `inspection` | `deploy`
- `risk_level` — `low` | `medium` | `high` | `critical`

### `POST /api/v1/operations`

**请求**:
```json
{
  "type": "change",
  "title": "web-01 安全重启",
  "description": "创建快照后重启虚拟机",
  "risk_level": "medium",
  "steps": [
    {"action": "compute.vm_snapshot_create", "params": {"vm": "web-01"}},
    {"action": "compute.vm_reboot", "params": {"vm": "web-01", "graceful": true}}
  ]
}
```

### `PUT /api/v1/operations/{id}/approve`

### `PUT /api/v1/operations/{id}/reject`

```json
{
  "reason": "变更窗口未到"
}
```

---

## 6. 仪表盘 (Dashboard)

### `GET /api/v1/dashboard/summary`

```json
{
  "success": true,
  "data": {
    "assets": {
      "vms": {"total": 1284, "running": 1201, "stopped": 83},
      "hosts": {"total": 32, "online": 30, "maintenance": 2},
      "storage": {"total": 10, "warning": 1}
    },
    "alerts": {
      "active": 3,
      "critical": 1,
      "warning": 2
    },
    "operations": {
      "pending": 2,
      "running": 1,
      "completed_today": 15
    }
  }
}
```

### `GET /api/v1/dashboard/trends`

**查询参数**:
- `days` (int, default 7)

```json
{
  "success": true,
  "data": {
    "cpu_trend": [
      {"date": "2026-05-24", "avg": 45.2, "max": 89.1},
      {"date": "2026-05-25", "avg": 42.8, "max": 85.3}
    ],
    "memory_trend": [...],
    "alert_trend": [
      {"date": "2026-05-24", "P0": 1, "P1": 3, "P2": 5},
      {"date": "2026-05-25", "P0": 0, "P1": 2, "P2": 4}
    ]
  }
}
```

---

## WebSocket 事件 (Phase 4)

```
ws://localhost:8688/ws?token=<jwt>

// 告警推送
{"event": "alert.new", "data": {"id": "...", "severity": "P0", "title": "..."}}
{"event": "alert.acknowledged", "data": {"id": "..."}}
{"event": "alert.resolved", "data": {"id": "..."}}

// 操作进度
{"event": "operation.started", "data": {"id": "..."}}
{"event": "operation.step_completed", "data": {"id": "...", "step": 1, "result": "..."}}
{"event": "operation.completed", "data": {"id": "...", "status": "completed"}}
{"event": "operation.failed", "data": {"id": "...", "error": "..."}}
```
