# Inspection V3.2 智慧維運工程師輔助平台 — 功能操作手冊

> **版本**: 3.2.0 | **文件日期**: 2026-06-01 | **語言**: 繁體中文 (zh-TW)
>
> **適用對象**: SRE 運維工程師、基礎架構管理員、平台管理員

---

## 目錄

1. [平台總覽](#1-平台總覽)
2. [快速入門](#2-快速入門)
3. [平台管理操作](#3-平台管理操作)
4. [資產管理操作](#4-資產管理操作)
5. [告警管理操作](#5-告警管理操作)
6. [AI 助手操作](#6-ai-助手操作)
7. [原子操作手冊](#7-原子操作手冊)
8. [遷移操作](#8-遷移操作)
9. [儀表板操作](#9-儀表板操作)
10. [審計日誌](#10-審計日誌)
11. [鍵盤快捷鍵](#11-鍵盤快捷鍵)
12. [API 參考](#12-api-參考)
13. [常見問題 FAQ](#13-常見問題-faq)
14. [最佳實踐](#14-最佳實踐)

---

## 1. 平台總覽

### 1.1 平台定位

**Inspection V3.2 — Engineer Assist SRE Platform** 是一套專為 SRE（Site Reliability Engineering）團隊設計的智慧維運輔助平台，整合資產管理、告警處理、原子化維運操作、跨平台遷移以及 AI 輔助對話等核心能力，協助工程師在日常運維工作中快速定位問題、執行標準操作並維持變更的可追溯性。

### 1.2 系統架構

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         使用者瀏覽器 (http://localhost:5173)               │
│                     React 18 + TypeScript + Tailwind CSS                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ChatView  │  DashboardView  │  ResourcesView  │  AlertsView  │  Ops   │
│──────────────────────────── HTTP REST API ──────────────────────────────│
├─────────────────────────────────────────────────────────────────────────┤
│                     FastAPI Backend (port 8688)                           │
│                                                                          │
│  ┌──────────────┬──────────────┬──────────────┬──────────────────────┐  │
│  │ API Layer    │   Service    │  Repository  │     Middleware        │  │
│  │ (api/v1/*)   │    Layer     │    Layer     │  audit | error | req  │  │
│  ├──────────────┼──────────────┼──────────────┼──────────────────────┤  │
│  │ health.py    │ alert_svc    │ base.py      │  AuditMiddleware      │  │
│  │ alerts.py    │ asset_svc    │ alert_repo   │  ErrorHandler         │  │
│  │ assets.py    │ ops_svc      │ ops_repo     │  RequestID            │  │
│  │ atomics.py   │ chat_svc     │              │                       │  │
│  │ dashboard.py │ dash_svc     │              │                       │  │
│  │ operations.py│              │              │                       │  │
│  │ platforms.py │ plat_svc     │              │                       │  │
│  │ chat.py      │              │              │                       │  │
│  │ migration.py │ MigrationEng │              │                       │  │
│  └──────────────┴──────────────┴──────────────┴──────────────────────┘  │
│                                                                          │
│  ┌───────────────────┬──────────────────┬──────────────────────────────┐ │
│  │  Core             │  Platforms       │  Migration                   │ │
│  │  config/security  │  vsphere/kvm/    │  engine.py                   │ │
│  │  registry/database│  fusionsphere    │  V2V/QEMU/Live               │ │
│  └───────────────────┴──────────────────┴──────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│                    PostgreSQL 16  │  Redis 7  (Docker)                   │
│                    schema: v32_sre │  cache/session                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 核心概念

| 概念 | 說明 |
|------|------|
| **資產 (Asset)** | 基礎設施資源：VM、Host、Storage、Network、Database、Container |
| **平台 (Platform)** | 虛擬化平台接入：VMware vSphere、KVM/QEMU、Huawei FusionSphere |
| **告警 (Alert)** | 監控告警，含 P0~P4 嚴重等級，生命周期：active → acknowledged → resolved |
| **原子操作 (Atomic Operation)** | 109 個標準化維運操作，分屬 9 大類別，附風險等級與參數 |
| **操作 (Operation)** | 變更工單，含審批流程：pending → approved → executing → completed/failed |
| **遷移 (Migration)** | 跨平台 VM 遷移：VMware↔KVM、VMware↔FusionSphere |
| **審計日誌 (Audit Log)** | 不可變更的操作審計記錄，涵蓋所有變異請求 |
| **AI 助手 (Chat)** | 規則式意圖識別代理，97+ 正則模式、40+ 意圖類型 |

### 1.4 支援平台

| 平台 | SDK | 版本 | 支援操作 |
|------|-----|------|----------|
| VMware vSphere | pyVmomi | 8.0.3 | VM 管理、快照、vMotion |
| KVM/QEMU | libvirt-python | 12.x | VM 管理、快照、遷移 |
| Huawei FusionSphere | httpx (REST) | 8.0 | VM 管理、快照 |

### 1.5 遷移路徑

| 來源 | 目標 | 工具 | 方法 |
|------|------|------|------|
| VMware | KVM | virt-v2v | OVA 匯出 → virt-v2v 轉換 → virsh 匯入 |
| VMware | FusionSphere | qemu-img | 磁碟匯出 → qemu-img 轉換 → 匯入 |
| KVM | VMware | qemu-img | 磁碟匯出 → qemu-img 轉換 → 匯入 |

### 1.6 技術棧一覽

| 層級 | 技術 | 版本 |
|------|------|------|
| 前端框架 | React + TypeScript | 18.x |
| UI 框架 | Tailwind CSS | 3.x |
| 狀態管理 | Zustand | - |
| 資料獲取 | TanStack React Query | - |
| 圖標 | Lucide React | - |
| 後端框架 | FastAPI (Python) | - |
| 資料庫 | PostgreSQL (asyncpg) | 16 |
| 快取 | Redis | 7 |
| 認證 | JWT (HS256) | - |
| 密碼雜湊 | bcrypt (passlib) | - |
| 容器化 | Docker Compose | - |

---

## 2. 快速入門

### 2.1 環境需求

| 需求 | 說明 |
|------|------|
| Python | 3.14+ |
| Node.js | 18+ |
| Docker | 24+ (用於 PostgreSQL 與 Redis) |
| npm | 9+ |

### 2.2 啟動流程

**步驟一：啟動基礎設施**

```bash
# 啟動 PostgreSQL 16 與 Redis 7
docker compose up -d postgres redis
```

**步驟二：設定環境變數**

```bash
cd backend
cp ../.env.example .env
# 編輯 .env 檔案，至少確認 DATABASE_URL 與 JWT_SECRET_KEY
```

關鍵環境變數說明：

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `DATABASE_URL` | (空，使用 SQLite in-memory) | `postgresql+asyncpg://user:pass@host:5432/v32_sre` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 連線字串 |
| `JWT_SECRET_KEY` | (開發模式自動產生) | 正式環境必須設定 |
| `JWT_ACCESS_EXPIRE_MINUTES` | `30` | Access Token 有效期 (分鐘) |
| `APP_ENV` | `development` | `development` / `staging` / `production` |
| `DEV_DEFAULT_USER` | (空) | 開發模式預設使用者，設為 `dev-user` 啟用 |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | 允許的跨域來源 |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `RATE_LIMIT_PER_MINUTE` | `60` | 每分鐘 API 請求上限 |

**步驟三：啟動後端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8688
```

**步驟四：啟動前端**

```bash
cd frontend
npm install
npm run dev
```

**步驟五：存取平台**

開啟瀏覽器，前往 `http://localhost:5173`。

### 2.3 一鍵啟動 (使用 Makefile)

```bash
# 建置開發環境
make setup

# 啟動開發伺服器
make dev

# 執行所有測試
make test

# 資料庫遷移
make db-migrate

# 重置資料庫 (含種子資料)
make db-reset

# 查看日誌
make logs
```

### 2.4 首次登入

1. 啟動後端與前端服務
2. 開啟瀏覽器，導向 `http://localhost:5173`
3. 開發模式下設定 `DEV_DEFAULT_USER=dev-user` 可跳過認證
4. 正式環境需透過 JWT Token 認證 (Bearer Token)

### 2.5 頁面導覽

平台預設導向 **AI 助手 (Chat)** 頁面。左側導覽列提供五個主要入口：

| 導覽項目 | 路徑 | 圖標 | 說明 |
|----------|------|------|------|
| Dashboard | `/dashboard` | LayoutDashboard | 系統總覽儀表板 |
| Resources | `/resources` | Server | 資產/資源管理 |
| Alerts | `/alerts` | Bell | 告警管理 |
| Operations | `/operations` | Terminal | 運維操作工單 |
| Engineer Assist | `/chat` | MessageSquare | AI 智慧助手 (預設首頁) |

側邊欄支援以下操作：
- **桌面端 (>768px)**：可折疊收合，展開時 224px 寬，收合時 64px 寬 (僅顯示圖標)
- **行動端 (<768px)**：預設隱藏，點選漢堡選單按鈕後以全高浮層顯示，附遮罩背景，點選遮罩或導覽後自動關閉

### 2.6 狀態列

底部狀態列 (StatusBar) 顯示以下資訊：

| 項目 | 說明 |
|------|------|
| API 連線狀態 | 每 30 秒自動輪詢 `/health`，顯示 API Connected (綠色) 或 API Disconnected (紅色) |
| 延遲 | 顯示最近一次健康檢查的響應延遲 (ms) |
| 版本號 | 當前平台版本號 |
| 平台名稱 | SRE Engineer Assist Platform |

---

## 3. 平台管理操作

### 3.1 功能概述

平台管理模組允許您新增、編輯、刪除虛擬化平台的連線設定，並支援測試連線與設備同步功能。

### 3.2 平台欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `name` | string (1-100) | 是 | 平台顯示名稱 |
| `platform_type` | enum | 是 | `vsphere` / `kvm` / `fusionsphere` |
| `host` | string | 是 | 主機名稱或 IP 位址 |
| `port` | int (1-65535) | 否 | API 埠號，預設 443 |
| `username` | string | 否 | 認證使用者名稱 |
| `password` | string | 否 | 認證密碼 (儲存時以 Fernet 加密) |
| `verify_ssl` | bool | 否 | 是否驗證 TLS 憑證，預設 true |
| `extra` | dict | 否 | 平台特定額外設定 |

### 3.3 新增平台

**畫面操作流程**：

1. 點選左側導覽 **Resources** → 進入資源管理頁面
2. 在上方工具列點選 **Platforms** 分頁 (或透過 API 直接操作)
3. 點選 **Add Platform** 按鈕
4. 填寫表單：名稱、平台類型、主機位址、埠號、使用者名稱、密碼
5. 點選 **Save** 儲存

**API 操作**：

```bash
# 新增 vSphere 平台
curl -X POST http://localhost:8688/api/v1/platforms/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "生產環境 vSphere",
    "platform_type": "vsphere",
    "host": "vcenter.example.com",
    "port": 443,
    "username": "admin@vsphere.local",
    "password": "your-secure-password",
    "verify_ssl": true,
    "extra": {}
  }'

# 新增 KVM 平台
curl -X POST http://localhost:8688/api/v1/platforms/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "開發環境 KVM",
    "platform_type": "kvm",
    "host": "kvm-host-01.example.com",
    "port": 22,
    "username": "root",
    "password": "your-secure-password",
    "verify_ssl": false
  }'
```

**回應範例**：

```json
{
  "id": 1,
  "name": "生產環境 vSphere",
  "platform_type": "vsphere",
  "host": "vcenter.example.com",
  "port": 443,
  "username": "admin@vsphere.local",
  "verify_ssl": true,
  "connected": false
}
```

### 3.4 測試連線

新增或編輯平台後，建議立即測試連線以確保設定正確。

```bash
curl -X POST http://localhost:8688/api/v1/platforms/1/test \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "success": true,
  "latency_ms": 245,
  "version": "8.0.3",
  "details": {
    "cluster_count": 3,
    "host_count": 12,
    "api_version": "8.0.3.0"
  },
  "error": null
}
```

### 3.5 同步設備

將平台上的所有 VM 與 Host 同步至本地資產表。

```bash
curl -X POST http://localhost:8688/api/v1/platforms/1/sync \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "total": 47,
  "vms": 42,
  "hosts": 5,
  "status": "completed"
}
```

同步過程中，系統會：
1. 連線至目標平台
2. 擷取所有 VM 清單 (含名稱、狀態、IP、規格等)
3. 擷取所有 Host 清單
4. 將設備資訊寫入 `assets` 資料表
5. 回傳彙總統計

### 3.6 查看設備

```bash
# 列出指定平台下的所有設備
curl http://localhost:8688/api/v1/platforms/1/devices \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
[
  {
    "id": "vm-1001",
    "name": "web-01",
    "device_type": "vm",
    "status": "running",
    "ip_address": "10.0.1.101",
    "platform": "vsphere",
    "metadata": {
      "cpu": 4,
      "memory_mb": 8192,
      "disk_gb": 100
    }
  }
]
```

### 3.7 編輯與刪除平台

```bash
# 更新平台設定 (部分更新)
curl -X PUT http://localhost:8688/api/v1/platforms/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "生產環境 vSphere (已更新)",
    "password": "new-secure-password"
  }'

# 刪除平台
curl -X DELETE http://localhost:8688/api/v1/platforms/1 \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 4. 資產管理操作

### 4.1 功能概述

資產管理模組提供完整的基礎設施資源管理能力，涵蓋 VM、Host、Storage、Network、Database、Container 六大類型。

### 4.2 資產類型與狀態

**資產類型 (AssetType)**：

| 類型 | 值 | 說明 |
|------|-----|------|
| 虛擬機 | `vm` | 虛擬機器 |
| 實體主機 | `host` | 實體伺服器 / Hypervisor 主機 |
| 儲存 | `storage` | 儲存裝置 / 資料存放區 |
| 網路 | `network` | 網路設備 / 交換器 |
| 資料庫 | `database` | 資料庫執行個體 |
| 容器 | `container` | 容器 / Pod |

**資產狀態 (AssetStatus)**：

| 狀態 | 值 | 說明 |
|------|-----|------|
| 運行中 | `running` | 資產正常運行 |
| 已停止 | `stopped` | 資產已關機或停止 |
| 錯誤 | `error` | 資產發生異常 |
| 維護中 | `maintenance` | 資產正在進行維護作業 |
| 未知 | `unknown` | 狀態無法確定 (預設值) |

**支援平台 (Platform)**：

| 平台 | 值 | 說明 |
|------|-----|------|
| VMware vSphere | `vsphere` | VMware 虛擬化平台 |
| KVM/QEMU | `kvm` | KVM 虛擬化平台 |
| Huawei FusionSphere | `fusionsphere` | FusionSphere 平台 |
| OpenStack | `OpenStack` | OpenStack 雲平台 |
| Kubernetes | `Kubernetes` | K8s 容器平台 |
| Physical | `Physical` | 實體機器 |
| Other | `Other` | 其他平台 |

### 4.3 資產資料結構

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | int | 資產 ID (自動遞增) |
| `name` | string(255) | 資產名稱 |
| `asset_type` | AssetType | 資產類型 |
| `platform` | Platform | 所屬平台 |
| `status` | AssetStatus | 當前狀態 |
| `ip_address` | string(45) | IP 位址 (支援 IPv4/IPv6) |
| `hostname` | string(255) | 主機名稱 |
| `location` | string(255) | 實體位置 / 資料中心 |
| `environment` | string(50) | 環境標籤 (如 prod/staging/dev) |
| `description` | text | 說明文字 |
| `tags` | JSON | 自訂標籤 |
| `metadata_` | JSON | 額外 metadata |

### 4.4 資產 CRUD 操作

#### 查詢資產列表 (支援過濾與分頁)

```bash
# 列出所有資產 (預設每頁 50 筆)
curl "http://localhost:8688/api/v1/assets?page=1&limit=50" \
  -H "Authorization: Bearer <TOKEN>"

# 依類型過濾
curl "http://localhost:8688/api/v1/assets?asset_type=vm" \
  -H "Authorization: Bearer <TOKEN>"

# 依平台過濾
curl "http://localhost:8688/api/v1/assets?platform=vsphere" \
  -H "Authorization: Bearer <TOKEN>"

# 依狀態過濾
curl "http://localhost:8688/api/v1/assets?status=running" \
  -H "Authorization: Bearer <TOKEN>"

# 全文搜尋 (名稱與主機名稱)
curl "http://localhost:8688/api/v1/assets?search=web" \
  -H "Authorization: Bearer <TOKEN>"

# 複合過濾
curl "http://localhost:8688/api/v1/assets?asset_type=vm&platform=vsphere&status=running&search=prod" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "items": [
    {
      "id": 1,
      "name": "web-01",
      "asset_type": "vm",
      "platform": "vsphere",
      "status": "running",
      "ip_address": "10.0.1.101",
      "hostname": "web-01.prod.example.com",
      "location": "IDC-A",
      "environment": "production",
      "description": "前端 Web 伺服器",
      "tags": {"role": "web", "tier": "frontend"},
      "metadata_": {"cpu": 4, "memory_gb": 8, "disk_gb": 100}
    }
  ],
  "total": 156,
  "page": 1,
  "limit": 50,
  "pages": 4
}
```

#### 取得單一資產

```bash
curl "http://localhost:8688/api/v1/assets/1" \
  -H "Authorization: Bearer <TOKEN>"
```

#### 新增資產

```bash
curl -X POST http://localhost:8688/api/v1/assets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "app-server-03",
    "asset_type": "vm",
    "platform": "kvm",
    "status": "running",
    "ip_address": "10.0.2.50",
    "hostname": "app-03.staging.example.com",
    "location": "IDC-B",
    "environment": "staging",
    "description": "應用伺服器",
    "tags": {"role": "app", "tier": "backend"},
    "metadata_": {"cpu": 8, "memory_gb": 16, "disk_gb": 200}
  }'
```

#### 更新資產 (部分更新)

```bash
curl -X PATCH http://localhost:8688/api/v1/assets/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "status": "maintenance",
    "description": "進行例行維護"
  }'
```

#### 刪除資產

```bash
curl -X DELETE http://localhost:8688/api/v1/assets/1 \
  -H "Authorization: Bearer <TOKEN>"
```

### 4.5 快速操作 (Quick Actions)

對資產執行快速操作。目前支援的操作：`boot`、`shutdown`、`restart`。

```bash
curl -X POST "http://localhost:8688/api/v1/assets/1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "action": "restart",
    "confirm": true
  }'
```

**回應範例**：

```json
{
  "status": "ok",
  "message": "Action 'restart' queued for asset web-01"
}
```

> **已知限制**: 快速操作的實作為 stub 模式 ── 命令已被記錄但不會實際觸發平台層級的 VM 操作。正式環境中需透過原子操作或變更工單執行。

### 4.6 前端畫面操作

**Resources 頁面 (ResourcesView)** 包含：

| 組件 | 功能 |
|------|------|
| **FilterBar** | 依類型、平台、狀態、環境過濾；支援文字搜尋 |
| **AssetTable** | 分頁表格，顯示名稱、類型、平台、狀態、IP、位置；支援排序 |
| **DetailPanel** | 側邊詳細面板，顯示資產的完整屬性、metadata、標籤 |
| **BatchActions** | 批次操作工具列 (目前為 no-op，UI 已就緒但後端未實作批次處理) |

篩選操作流程：
1. 在 FilterBar 選擇過濾條件 (類型/平台/狀態)
2. 可輸入搜尋關鍵字進行全文搜尋
3. 系統自動向 `/assets` 端點發送帶有 query params 的 GET 請求
4. 結果以分頁表格呈現

---

## 5. 告警管理操作

### 5.1 功能概述

告警管理模組實現完整的告警生命周期管理，支援 P0~P4 五個嚴重等級。

### 5.2 告警嚴重等級

| 等級 | 值 | 定義 | 回應時效 | 範例 |
|------|-----|------|----------|------|
| P0 | `P0` | 緊急 — 服務完全中斷 | 立即 (< 5 分鐘) | 核心資料庫宕機 |
| P1 | `P1` | 嚴重 — 服務部分中斷 | 15 分鐘內 | 主要 API 回應逾時 |
| P2 | `P2` | 警告 — 服務效能下降 | 1 小時內 | CPU 使用率 > 90% |
| P3 | `P3` | 注意 — 潛在風險 | 4 小時內 | 磁碟使用率 > 80% |
| P4 | `P4` | 資訊 — 一般通知 | 24 小時內 | SSL 憑證 30 天內到期 |

### 5.3 告警生命周期

```
┌────────┐    確認      ┌──────────────┐    解決      ┌──────────┐
│ ACTIVE │ ──────────> │ ACKNOWLEDGED │ ──────────> │ RESOLVED │
│ (活躍)  │             │   (已確認)    │             │  (已解決)  │
└────────┘             └──────────────┘             └──────────┘
     │
     │ 抑制
     v
┌───────────┐
│SUPPRESSED │
│  (已抑制)  │
└───────────┘
```

### 5.4 告警資料結構

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | int | 告警 ID |
| `title` | string(500) | 告警標題 |
| `description` | text | 詳細描述 |
| `severity` | AlertSeverity | 嚴重等級 (P0/P1/P2/P3/P4) |
| `status` | AlertStatus | 告警狀態 (active/acknowledged/resolved/suppressed) |
| `source` | string(255) | 告警來源 |
| `asset_id` | int | 關聯資產 ID |
| `metric_name` | string(255) | 觸發指標名稱 |
| `metric_value` | string(100) | 指標當前值 |
| `threshold` | string(100) | 告警閾值 |
| `acknowledged_by` | string(255) | 確認人 |
| `acknowledged_at` | datetime | 確認時間 |
| `resolved_by` | string(255) | 解決人 |
| `resolved_at` | datetime | 解決時間 |
| `resolution_notes` | text | 解決備註 |

### 5.5 告警 API 操作

#### 查詢告警列表

```bash
# 列出所有告警 (預設每頁 20 筆)
curl "http://localhost:8688/api/v1/alerts?page=1&limit=20" \
  -H "Authorization: Bearer <TOKEN>"

# 依嚴重等級過濾
curl "http://localhost:8688/api/v1/alerts?severity=P0" \
  -H "Authorization: Bearer <TOKEN>"

# 依狀態過濾
curl "http://localhost:8688/api/v1/alerts?status=active" \
  -H "Authorization: Bearer <TOKEN>"

# 依資產過濾
curl "http://localhost:8688/api/v1/alerts?asset_id=1" \
  -H "Authorization: Bearer <TOKEN>"

# 複合過濾: P0/P1 的活躍告警
curl "http://localhost:8688/api/v1/alerts?severity=P1&status=active" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "items": [
    {
      "id": 1,
      "title": "CPU 使用率過高 - web-01",
      "description": "過去 5 分鐘 CPU 使用率持續超過 95%",
      "severity": "P1",
      "status": "active",
      "source": "prometheus",
      "asset_id": 1,
      "metric_name": "cpu_usage_percent",
      "metric_value": "97.3",
      "threshold": "90.0",
      "acknowledged_by": null,
      "acknowledged_at": null,
      "resolved_by": null,
      "resolved_at": null,
      "resolution_notes": null
    }
  ],
  "total": 23,
  "page": 1,
  "limit": 20,
  "pages": 2
}
```

#### 取得單一告警

```bash
curl "http://localhost:8688/api/v1/alerts/1" \
  -H "Authorization: Bearer <TOKEN>"
```

#### 確認告警 (Acknowledge)

```bash
curl -X PUT "http://localhost:8688/api/v1/alerts/1/acknowledge" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "notes": "正在調查原因，已通知值班工程師"
  }'
```

#### 解決告警 (Resolve)

```bash
curl -X PUT "http://localhost:8688/api/v1/alerts/1/resolve" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "resolution_notes": "重新啟動 web-01 上的 Nginx 服務後恢復正常"
  }'
```

### 5.6 前端畫面操作

**Alerts 頁面 (AlertsView)** 包含：

| 組件 | 功能 |
|------|------|
| **嚴重等級標籤列** | 顯示各等級告警數量 (P0/P1/P2/P3/P4) 以及 active 數量 |
| **Tabs 分頁** | 按嚴重等級切換 (All / P0 / P1 / P2 / P3 / P4) |
| **AlertFilters** | 依狀態過濾 (active/acknowledged/resolved/suppressed)；支援文字搜尋 |
| **AlertCard** | 告警卡片，顯示標題、描述、等級、狀態、時間，附 Acknowledge/Resolve 按鈕 |

操作流程：
1. 進入 Alerts 頁面，查看各等級告警數量
2. 點選 P1 分頁，查看所有 P1 告警
3. 找到需要處理的告警，點選 **Acknowledge** 確認接手
4. 問題解決後，點選 **Resolve** 並填寫解決備註

---

## 6. AI 助手操作

### 6.1 功能概述

AI 助手 (Engineer Assist) 是平台的預設首頁，提供自然語言 (中文) 互動介面。使用者以日常用語描述問題或下達操作指令，系統自動進行意圖識別，回傳結構化的推薦操作步驟。

### 6.2 技術實現

AI 助手基於 **規則式意圖識別引擎 (IntentRecognizer)** 實現，無需外部 LLM 依賴：

| 特性 | 說明 |
|------|------|
| 正則模式 | 97+ 個匹配規則 |
| 意圖類型 | 40+ 種 (diagnose, restart, shutdown, snapshot, db_status 等) |
| 參數提取 | 自動從訊息中提取 target、service 等參數 |
| 操作對應 | 意圖 → 原子操作自動映射 |
| 上下文記憶 | ConversationContext，記住最近 5 個目標，TTL 2 小時 |
| 風險評估 | 自動計算整體風險等級 (low/medium/high/critical) |
| 時間估算 | 自動彙總預計執行時間 |
| 最大上下文 | 1000 個並行對話 (LRU 淘汰) |

### 6.3 支援的意圖類型

| 意圖 | 觸發關鍵詞 | 對應操作 | 說明 |
|------|-----------|----------|------|
| `diagnose` | 「連接超時」「不通」「宕機」「掛了」「連不上」 | `infra.ping` + `compute.vm_status` | 故障診斷 |
| `restart` | 「重啟」+ 主機名 | `compute.vm_restart` | 重啟 VM |
| `shutdown` | 「關機」「關閉」+ 主機名 | `compute.vm_stop` | 關機 |
| `power_on` | 「開機」「啟動」+ 主機名 | `compute.vm_start` | 開機 |
| `snapshot` | 「快照」「備份快照」 | `compute.vm_snapshot` | 建立快照 |
| `disk_usage` | 「磁碟」「硬碟」「空間」「容量」「滿了」 | `storage.disk_usage` | 磁碟使用量 |
| `network_check` | 「網路」「ping」「連通」 | `infra.ping` + `infra.traceroute` | 網路檢查 |
| `check_status` | 「狀態」「情況」+ 主機名 | `compute.vm_status` | 狀態查詢 |
| `db_status` | 「資料庫」+「狀態/健康/連接」 | `database.status` + `database.connection_pool` | 資料庫狀態 |
| `db_slow_queries` | 「資料庫」+「慢查詢/慢SQL/性能」 | `database.slow_queries` | 慢查詢分析 |
| `db_replication` | 「資料庫」+「複製/同步/主從/延遲」 | `database.replication_lag` | 複製延遲 |
| `db_backup` | 「資料庫」+「備份/恢復」 | `database.backup_status` | 備份狀態 |
| `backup_create` | 「備份」+ 主機名 | `backup.create` | 建立備份 |
| `backup_restore` | 「恢復」+「備份」+ 主機名 | `backup.restore` | 恢復備份 |
| `backup_verify` | 「驗證」+「備份」+「完整性」 | `backup.verify` | 驗證備份 |
| `security_scan` | 「漏洞掃描」「安全掃描」 | `security.vulnerability_scan` | 安全掃描 |
| `patch_check` | 「補丁」「更新」「patch」+「狀態」 | `security.patch_status` | 補丁狀態 |
| `cert_check` | 「證書」「SSL」「TLS」+「過期/到期」 | `infra.cert_check` | 憑證檢查 |
| `cert_renew` | 「續簽」「更新」+「證書」 | `security.cert_renew` | 續簽憑證 |
| `log_search` | 「日誌」「log」「錯誤日誌」 | `monitoring.log_search` | 日誌搜索 |
| `performance_check` | 「性能」「CPU」「記憶體」「負載」 | `compute.cpu_usage` + `compute.memory_usage` | 性能檢查 |
| `metric_query` | 「指標」「metric」「監控數據」 | `monitoring.metric_query` | 指標查詢 |
| `migrate` | 「遷移」「漂移」 | `compute.vm_migrate` | VM 遷移 |
| `maintenance_mode` | 「進入維護模式」 | `compute.host_maintenance` | 維護模式 |
| `firewall_list` | 「防火牆」「firewall」+「規則/策略」 | `network.firewall_rule_list` | 防火牆規則 |
| `dns_check` | 「DNS」「域名解析」+「檢查」 | `infra.dns_check` | DNS 檢查 |
| `service_restart` | 「重啟」+ 主機名 + 服務名 | `maintenance.service_restart` | 服務重啟 |
| `service_status` | 「查看」+ 主機名 + 服務名 +「狀態」 | `maintenance.service_status` | 服務狀態 |
| `help` | 「幫助」「你能做什麼」「怎麼用」 | - | 顯示幫助訊息 |
| `general` | (未匹配) | - | 一般性回覆，提示可用功能 |

### 6.4 使用範例

#### 範例 1：診斷故障

**使用者輸入**：
```
web-01 連接超時
```

**系統回應**：
```
檢測到 web-01 存在問題，建議按以下步驟診斷：

1. [infra.ping] Ping Host
   檢查網路可達性 (ICMP ping)
   風險: low | 預計耗時: 5 秒
   參數: {"target": "web-01"}

2. [compute.vm_status] VM Status
   檢查虛擬機電源狀態與健康狀況
   風險: low | 預計耗時: 10 秒
   參數: {"vm": "web-01"}

風險評估：低風險 — 可安全執行，無需審批
預計耗時 15 秒
```

#### 範例 2：執行操作

**使用者輸入**：
```
重啟 app-server-02
```

**系統回應**：
```
將為您重啟 app-server-02，建議先確認當前狀態：

1. [compute.vm_restart] VM Restart
   重啟虛擬機
   風險: medium | 預計耗時: 120 秒
   參數: {"vm": "app-server-02"}

風險評估：中風險 — 建議確認後執行
預計耗時 2 分鐘
```

#### 範例 3：資料庫操作

**使用者輸入**：
```
查看主資料庫的慢查詢
```

**系統回應**：
```
查看 主資料庫 的慢查詢情況：

1. [database.slow_queries] DB Slow Queries
   列出當前執行的慢查詢
   風險: low | 預計耗時: 10 秒
   參數: {"instance": "主資料庫", "threshold_sec": "int"}
```

#### 範例 4：安全檢查

**使用者輸入**：
```
檢查 web-01 證書是否過期
```

**系統回應**：
```
檢查 web-01 的 SSL/TLS 證書狀態：

1. [infra.cert_check] Certificate Check
   檢查 SSL/TLS 證書到期時間
   風險: low | 預計耗時: 5 秒
   參數: {"hostname": "web-01", "port": "int"}
```

#### 範例 5：服務管理

**使用者輸入**：
```
重啟 db-server-01 上的 postgresql 服務
```

**系統回應**：
```
重啟 db-server-01 上的服務：

1. [maintenance.service_restart] Restart Service
   重啟系統服務
   風險: medium | 預計耗時: 30 秒
   參數: {"host": "db-server-01", "service": "postgresql"}
```

### 6.5 推薦操作工作流程

1. **輸入問題** — 在對話框輸入自然語言描述
2. **AI 分析** — 系統進行意圖識別，提取 target 與參數
3. **回傳建議** — 顯示結構化推薦步驟 (RecommendationCard)，含操作名稱、描述、風險、預估時間
4. **使用者確認** — 選擇要執行的步驟，點選 **Execute All** 或勾選特定步驟
5. **確認對話框** — 系統彈出 ConfirmDialog，顯示風險警告，需再次確認
6. **建立工單** — 系統呼叫 `POST /operations` 建立變更工單，回傳工單編號
7. **追蹤進度** — 透過 Operations 頁面追蹤工單狀態

### 6.6 輸入快捷方式

| 輸入操作 | 說明 |
|----------|------|
| `Enter` | 發送訊息 |
| `Shift + Enter` | 換行 (不發送) |
| 對話框下方提示 | 「Press Enter to send, Shift+Enter for new line」 |

### 6.7 快速操作按鈕 (QuickActions)

在歡迎畫面提供預設快速操作按鈕，點選即自動發送對應訊息：
- 「查看告警」
- 「資源概覽」
- 「幫助」

### 6.8 已知限制

- **上下文僅存於記憶體**：服務重啟後所有 ConversationContext 遺失
- **無 WebSocket 串流**：對話為標準 HTTP 請求/回應模式，無即時串流
- **規則式識別**：使用正則匹配而非 LLM，複雜或模糊表達可能無法準確識別
- **LRU 淘汰**：超過 1000 個並行對話時會淘汰最舊的上下文

---

## 7. 原子操作手冊

### 7.1 概述

原子操作註冊表 (Atomic Operations Registry) 包含 **109 個** 標準化維運操作，分屬 **9 大類別**。每個操作皆明確定義風險等級、參數結構、預估執行時間與審批需求。

### 7.2 風險等級定義

| 等級 | 值 | 圖標顏色 | 審批需求 | 說明 |
|------|-----|----------|----------|------|
| 低風險 | `low` | 綠色 | 無需審批 | 唯讀操作，不影響服務 |
| 中風險 | `medium` | 黃色 | 建議確認後執行 | 可能短暫影響服務 |
| 高風險 | `high` | 橙色 | 需要審批 | 可能影響服務可用性 |
| 嚴重風險 | `critical` | 紅色 | 必須審批 | 可能造成不可逆影響 |

### 7.3 操作類別總覽

| 類別 | ID | 操作數量 | 說明 |
|------|-----|----------|------|
| 基礎設施 | `infra` | 20 | Ping、Traceroute、DNS、SSL、頻寬測試等 |
| 計算資源 | `compute` | 20 | VM 管理、快照、遷移、主機維護 |
| 儲存資源 | `storage` | 12 | 磁碟、LUN、NFS、快照、Volume 擴展 |
| 網路資源 | `network` | 12 | VLAN、防火牆、負載平衡器、拓樸 |
| 資料庫 | `database` | 12 | 連線、慢查詢、複製、備份、鎖定 |
| 安全 | `security` | 9 | 漏洞掃描、登入稽核、憑證、合規檢查 |
| 監控 | `monitoring` | 11 | CPU/記憶體/磁碟/進程/URL/SSL 檢查 |
| 備份 | `backup` | 5 | 備份建立、驗證、還原、排程、保留 |
| 維護 | `maintenance` | 8 | 補丁、服務重啟、設定應用、日誌清理 |

### 7.4 全部 109 個原子操作明細

#### 7.4.1 基礎設施 (infra) — 20 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `infra.ping` | Ping Host | 透過 ICMP ping 檢查網路可達性 | low | 5s | `target`: string | 否 | 否 |
| `infra.traceroute` | Traceroute | 追蹤到目標主機的網路路徑 | low | 15s | `target`: string | 否 | 否 |
| `infra.nslookup` | NSLookup | DNS 名稱解析查詢 | low | 3s | `target`: string | 否 | 否 |
| `infra.port_scan` | Port Scan | 檢查主機上特定埠號是否開放 | low | 10s | `target`: string, `ports`: list[int] | 否 | 否 |
| `infra.ssh_check` | SSH Check | 驗證 SSH 連線可用性 | low | 5s | `target`: string | 否 | 否 |
| `infra.dns_lookup` | DNS Lookup | 查詢 DNS 記錄 (A/AAAA/CNAME/MX) | low | 3s | `target`: string | 否 | 否 |
| `infra.mtr` | MTR | 結合 ping 與 traceroute 的網路診斷 | low | 30s | `target`: string | 否 | 否 |
| `infra.curl_check` | HTTP Check | 檢查 HTTP/HTTPS 端點可用性 | low | 10s | `target`: string | 否 | 否 |
| `infra.telnet_check` | Telnet Check | 測試 TCP 連線可達性 | low | 5s | `target`: string, `port`: int | 否 | 否 |
| `infra.bandwidth_test` | Bandwidth Test | 測量到目標的網路頻寬 | low | 30s | `target`: string | 否 | 否 |
| `infra.latency_test` | Latency Test | 測量網路延遲 | low | 10s | `target`: string | 否 | 否 |
| `infra.packet_loss` | Packet Loss | 檢測封包遺失率 | low | 15s | `target`: string | 否 | 否 |
| `infra.arp_table` | ARP Table | 查詢 ARP 表 | low | 5s | `target`: string | 否 | 否 |
| `infra.netstat` | Netstat | 查詢網路連線狀態 | low | 5s | `target`: string | 否 | 否 |
| `infra.route_table` | Route Table | 查詢路由表 | low | 5s | `target`: string | 否 | 否 |
| `infra.interface_status` | Interface Status | 檢查網路介面狀態 | low | 5s | `target`: string | 否 | 否 |
| `infra.dhcp_check` | DHCP Check | 檢查 DHCP 服務狀態 | low | 5s | `target`: string | 否 | 否 |
| `infra.ntp_sync` | NTP Sync | 檢查 NTP 時間同步狀態 | low | 5s | `target`: string | 否 | 否 |
| `infra.cert_check` | Certificate Check | 檢查 SSL/TLS 憑證到期日 | low | 5s | `hostname`: string, `port`: int | 否 | 否 |
| `infra.ssl_scan` | SSL Scan | 掃描 SSL/TLS 設定安全性 | low | 30s | `target`: string | 否 | 否 |

#### 7.4.2 計算資源 (compute) — 20 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `compute.vm_list` | List VMs | 列出所有虛擬機器 | low | 5s | `target`: string | 否 | 否 |
| `compute.vm_info` | VM Info | 取得虛擬機詳細資訊 | low | 5s | `vm`: string | 否 | 否 |
| `compute.vm_start` | Start VM | 啟動虛擬機 | medium | 30s | `vm`: string | 是 | 否 |
| `compute.vm_stop` | Stop VM | 關閉虛擬機 (優雅關機) | high | 60s | `vm`: string | 是 | 是 |
| `compute.vm_restart` | Restart VM | 重啟虛擬機 | medium | 120s | `vm`: string | 是 | 否 |
| `compute.vm_suspend` | Suspend VM | 暫停虛擬機 | medium | 30s | `vm`: string | 是 | 否 |
| `compute.vm_resume` | Resume VM | 恢復虛擬機 | low | 30s | `vm`: string | 否 | 否 |
| `compute.vm_snapshot` | Create Snapshot | 建立 VM 快照 | medium | 60s | `vm`: string, `name`: string, `memory`: bool | 否 | 是 |
| `compute.vm_clone` | Clone VM | 複製虛擬機 | high | 300s | `vm`: string, `name`: string | 是 | 否 |
| `compute.vm_migrate` | Migrate VM | 即時遷移 VM 到另一台主機 | high | 300s | `vm`: string, `target_host`: string | 是 | 否 |
| `compute.vm_console` | VM Console | 取得 VM 主控台存取 | low | 5s | `vm`: string | 否 | 否 |
| `compute.vm_performance` | VM Performance | 查看 VM 效能指標 | low | 10s | `vm`: string | 否 | 否 |
| `compute.host_list` | List Hosts | 列出所有主機 | low | 5s | - | 否 | 否 |
| `compute.host_info` | Host Info | 取得主機詳細資訊 | low | 5s | `host`: string | 否 | 否 |
| `compute.host_maintenance` | Enter Maintenance | 將主機設為維護模式 | high | 300s | `host`: string | 是 | 否 |
| `compute.cluster_status` | Cluster Status | 檢查叢集狀態 | low | 10s | `host`: string | 否 | 否 |
| `compute.resource_pool` | Resource Pool | 查看資源池使用狀況 | low | 10s | `host`: string | 否 | 否 |
| `compute.vm_template` | VM Template | 從 VM 建立範本 | medium | 120s | `vm`: string, `name`: string | 否 | 否 |
| `compute.vm_hardware` | VM Hardware | 查看/修改 VM 硬體設定 | medium | 30s | `vm`: string | 是 | 否 |
| `compute.process_list` | Process List | 列出主機上運行的進程 | low | 10s | `host`: string | 否 | 否 |

#### 7.4.3 儲存資源 (storage) — 12 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `storage.storage_list` | Storage List | 列出所有儲存資源 | low | 5s | `target`: string | 否 | 否 |
| `storage.volume_list` | Volume List | 列出所有 Volume | low | 5s | `target`: string | 否 | 否 |
| `storage.volume_info` | Volume Info | 取得 Volume 詳細資訊 | low | 5s | `volume_id`: string | 否 | 否 |
| `storage.volume_create` | Create Volume | 建立新的 Volume | medium | 30s | `size_gb`: int | 否 | 否 |
| `storage.volume_delete` | Delete Volume | 刪除 Volume | critical | 30s | `volume_id`: string | 是 | 否 |
| `storage.volume_extend` | Extend Volume | 擴展 Volume 大小 | critical | 120s | `volume_id`: string, `size_gb`: int | 是 | 否 |
| `storage.volume_attach` | Attach Volume | 掛載 Volume 到 VM | medium | 30s | `volume_id`: string, `vm`: string | 是 | 否 |
| `storage.volume_detach` | Detach Volume | 從 VM 卸載 Volume | medium | 30s | `volume_id`: string, `vm`: string | 是 | 否 |
| `storage.volume_snapshot` | Volume Snapshot | 建立 Volume 快照 | medium | 60s | `volume_id`: string, `name`: string | 否 | 是 |
| `storage.datastore_usage` | Datastore Usage | 檢查資料存放區使用量 | low | 10s | `target`: string | 否 | 否 |
| `storage.disk_performance` | Disk Performance | 檢查磁碟 I/O 效能 | low | 15s | `target`: string | 否 | 否 |
| `storage.storage_policy` | Storage Policy | 查看儲存策略設定 | low | 5s | `target`: string | 否 | 否 |

#### 7.4.4 網路資源 (network) — 12 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `network.network_list` | Network List | 列出所有網路 | low | 5s | `target`: string | 否 | 否 |
| `network.network_create` | Create Network | 建立新的虛擬網路 | medium | 30s | `name`: string, `vlan_id`: int | 否 | 否 |
| `network.subnet_list` | Subnet List | 列出所有子網路 | low | 5s | `target`: string | 否 | 否 |
| `network.port_list` | Port List | 列出網路埠號 | low | 5s | `target`: string | 否 | 否 |
| `network.port_create` | Create Port | 建立網路埠號 | low | 10s | `network_id`: string | 否 | 否 |
| `network.security_group_list` | Security Group List | 列出安全群組 | low | 5s | `target`: string | 否 | 否 |
| `network.security_group_rule` | Security Group Rule | 管理安全群組規則 | medium | 15s | `sg_id`: string, `rule`: string | 是 | 否 |
| `network.firewall_rule` | Firewall Rule | 管理防火牆規則 | high | 15s | `target`: string, `rule`: string | 是 | 否 |
| `network.load_balancer` | Load Balancer | 管理負載平衡器 | medium | 20s | `lb_id`: string | 是 | 否 |
| `network.vlan_list` | VLAN List | 列出 VLAN 設定 | low | 10s | `vlan_id`: int | 否 | 否 |
| `network.bandwidth_monitor` | Bandwidth Monitor | 監控頻寬使用量 | low | 10s | `target`: string | 否 | 否 |
| `network.network_topology` | Network Topology | 查看網路拓樸 | low | 15s | `target`: string | 否 | 否 |

#### 7.4.5 資料庫 (database) — 12 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `database.db_list` | DB List | 列出所有資料庫 | low | 5s | `instance`: string | 否 | 否 |
| `database.db_status` | DB Status | 檢查資料庫健康狀態與連線數 | low | 10s | `instance`: string | 否 | 否 |
| `database.db_connections` | DB Connections | 查看資料庫連線詳細資訊 | low | 5s | `instance`: string | 否 | 否 |
| `database.db_slow_query` | DB Slow Query | 查詢慢查詢日誌 | low | 10s | `instance`: string, `threshold_sec`: int | 否 | 否 |
| `database.db_long_running` | DB Long Running | 列出長時間執行的查詢 | low | 5s | `instance`: string | 否 | 否 |
| `database.db_locks` | DB Locks | 檢查資料庫鎖定狀態 | low | 5s | `instance`: string | 否 | 否 |
| `database.db_replication` | DB Replication | 檢查複製狀態與延遲 | low | 5s | `instance`: string | 否 | 否 |
| `database.db_backup` | DB Backup | 執行資料庫備份 | medium | 300s | `instance`: string | 是 | 否 |
| `database.db_restore` | DB Restore | 還原資料庫備份 | critical | 600s | `instance`: string, `backup_id`: string | 是 | 否 |
| `database.db_performance` | DB Performance | 查看資料庫效能指標 | low | 10s | `instance`: string | 否 | 否 |
| `database.db_vacuum` | DB Vacuum | 執行資料庫 VACUUM 操作 | medium | 300s | `instance`: string | 是 | 否 |
| `database.db_index_usage` | DB Index Usage | 檢查索引使用情況 | low | 10s | `instance`: string | 否 | 否 |

#### 7.4.6 安全 (security) — 9 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `security.audit_log` | Audit Log | 查詢安全審計日誌 | low | 10s | `target`: string | 否 | 否 |
| `security.user_list` | User List | 列出系統使用者 | low | 5s | `target`: string | 否 | 否 |
| `security.user_permissions` | User Permissions | 檢查使用者權限 | low | 5s | `target`: string | 否 | 否 |
| `security.login_history` | Login History | 查看登入歷史記錄 | low | 10s | `target`: string, `hours`: int | 否 | 否 |
| `security.failed_logins` | Failed Logins | 查看失敗登入嘗試 | low | 10s | `target`: string, `hours`: int | 否 | 否 |
| `security.cert_list` | Certificate List | 列出所有 SSL/TLS 憑證 | low | 5s | `target`: string | 否 | 否 |
| `security.cert_expiry` | Certificate Expiry | 檢查憑證到期日 | low | 5s | `hostname`: string | 否 | 否 |
| `security.vuln_scan` | Vulnerability Scan | 執行漏洞掃描 | low | 120s | `target`: string | 否 | 否 |
| `security.compliance_check` | Compliance Check | 執行合規檢查 | low | 120s | `target`: string, `baseline`: string | 否 | 否 |

#### 7.4.7 監控 (monitoring) — 11 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `monitoring.check_cpu` | Check CPU | 檢查 CPU 使用率 | low | 5s | `target`: string, `hours`: int | 否 | 否 |
| `monitoring.check_memory` | Check Memory | 檢查記憶體使用率 | low | 5s | `target`: string, `hours`: int | 否 | 否 |
| `monitoring.check_disk` | Check Disk | 檢查磁碟使用率 | low | 5s | `target`: string, `path`: string | 否 | 否 |
| `monitoring.check_process` | Check Process | 檢查指定進程狀態 | low | 5s | `host`: string, `process`: string | 否 | 否 |
| `monitoring.check_service` | Check Service | 檢查系統服務狀態 | low | 5s | `host`: string, `service`: string | 否 | 否 |
| `monitoring.check_port` | Check Port | 檢查埠號監聽狀態 | low | 5s | `target`: string, `port`: int | 否 | 否 |
| `monitoring.check_url` | Check URL | 檢查 URL 可訪問性與回應碼 | low | 10s | `url`: string | 否 | 否 |
| `monitoring.check_log` | Check Log | 檢查日誌中的錯誤模式 | low | 15s | `target`: string, `pattern`: string, `hours`: int | 否 | 否 |
| `monitoring.check_ssl` | Check SSL | 檢查 SSL 憑證有效性 | low | 5s | `hostname`: string, `port`: int | 否 | 否 |
| `monitoring.check_performance` | Check Performance | 綜合效能檢查 | low | 30s | `target`: string | 否 | 否 |
| `monitoring.check_cluster` | Check Cluster | 檢查叢集健康狀態 | low | 15s | `target`: string | 否 | 否 |

#### 7.4.8 備份 (backup) — 5 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `backup.backup_list` | Backup List | 列出所有備份 | low | 10s | `target`: string | 否 | 否 |
| `backup.backup_create` | Create Backup | 觸發備份作業 | low | 300s | `target`: string, `type`: string | 否 | 否 |
| `backup.backup_verify` | Verify Backup | 驗證備份完整性 | low | 120s | `backup_id`: string | 否 | 否 |
| `backup.backup_restore` | Restore Backup | 從備份還原 | critical | 600s | `target`: string, `backup_id`: string | 是 | 否 |
| `backup.backup_schedule` | Backup Schedule | 管理備份排程 | low | 10s | `target`: string | 否 | 否 |
| `backup.backup_retention` | Backup Retention | 檢查備份保留策略 | low | 30s | `target`: string | 否 | 否 |

#### 7.4.9 維護 (maintenance) — 8 個操作

| ID | 名稱 | 描述 | 風險 | 耗時 | 參數 | 審批 | 可逆 |
|----|------|------|------|------|------|------|------|
| `maintenance.patch_list` | Patch List | 列出可用修補程式 | low | 30s | `host`: string | 否 | 否 |
| `maintenance.patch_apply` | Apply Patches | 套用系統修補程式 | high | 600s | `host`: string, `packages`: list[string] | 是 | 否 |
| `maintenance.maint_schedule` | Maintenance Schedule | 排定維護窗口 | low | 10s | `host`: string, `time`: string | 否 | 否 |
| `maintenance.restart_service` | Restart Service | 重啟系統服務 | medium | 30s | `host`: string, `service`: string | 是 | 否 |
| `maintenance.reload_config` | Reload Config | 重新載入設定檔 | medium | 10s | `host`: string, `config_path`: string | 是 | 否 |
| `maintenance.clear_cache` | Clear Cache | 清除系統快取 | medium | 60s | `host`: string, `path`: string | 是 | 否 |
| `maintenance.rotate_logs` | Rotate Logs | 強制日誌輪替 | low | 15s | `host`: string, `log_path`: string | 否 | 否 |
| `maintenance.config_validate` | Validate Config | 驗證設定檔語法 | low | 10s | `host`: string, `config_path`: string | 否 | 否 |

### 7.5 原子操作 API

```bash
# 列出所有原子操作
curl "http://localhost:8688/api/v1/atomics" \
  -H "Authorization: Bearer <TOKEN>"

# 按類別過濾
curl "http://localhost:8688/api/v1/atomics?category=compute" \
  -H "Authorization: Bearer <TOKEN>"

# 搜尋操作
curl "http://localhost:8688/api/v1/atomics?search=backup" \
  -H "Authorization: Bearer <TOKEN>"

# 取得單一操作 (使用 dot-notation ID)
curl "http://localhost:8688/api/v1/atomics/compute.vm_restart" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 8. 遷移操作

### 8.1 功能概述

跨平台 VM 遷移引擎支援 VMware vSphere、KVM/QEMU、Huawei FusionSphere 之間的虛擬機器遷移。引擎自動根據來源/目標平台選擇合適的遷移方法。

### 8.2 遷移方法

| 方法 | 值 | 適用場景 | 工具 |
|------|-----|----------|------|
| V2V 轉換 | `virt-v2v` | VMware → KVM | virt-v2v |
| 磁碟格式轉換 | `qemu-img-convert` | VMware ↔ FusionSphere, KVM → VMware | qemu-img |
| 同平台即時遷移 | `live-migrate` | 相同平台間 (如 vSphere vMotion) | 平台原生 |

### 8.3 遷移狀態

| 狀態 | 值 | 說明 |
|------|-----|------|
| 已規劃 | `planned` | 遷移計劃已生成，等待執行 |
| 執行中 | `in_progress` | 遷移正在執行中 |
| 已完成 | `completed` | 遷移成功完成 |
| 失敗 | `failed` | 遷移執行失敗 |
| 已回滾 | `rolled_back` | 遷移已回滾至原始狀態 |

### 8.4 遷移 API 操作

#### 步驟一：產生遷移計劃

```bash
curl -X POST http://localhost:8688/api/v1/migration/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "vm_id": "vm-web-01",
    "source": "vsphere",
    "target": "kvm"
  }'
```

**回應範例** (VMware → KVM)：

```json
{
  "plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "vm_id": "vm-web-01",
  "source_platform": "vsphere",
  "target_platform": "kvm",
  "method": "virt-v2v",
  "steps": [
    {
      "order": 1,
      "action": "export",
      "description": "Export VM disk from vSphere",
      "command": "export OVA from vSphere",
      "status": "pending",
      "error": null
    },
    {
      "order": 2,
      "action": "convert",
      "description": "Convert disk using virt-v2v",
      "command": "virt-v2v -i ova disk.ova -o local -os /var/lib/libvirt/images",
      "status": "pending",
      "error": null
    },
    {
      "order": 3,
      "action": "import",
      "description": "Import VM into KVM/libvirt",
      "command": "virsh define converted-vm.xml",
      "status": "pending",
      "error": null
    },
    {
      "order": 4,
      "action": "verify",
      "description": "Verify VM boots and network connectivity",
      "command": "virsh dominfo <vm_id>",
      "status": "pending",
      "error": null
    }
  ],
  "status": "planned"
}
```

#### 步驟二：執行遷移

```bash
curl -X POST "http://localhost:8688/api/v1/migration/execute?plan_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "success": true,
  "message": "Migration completed"
}
```

#### 步驟三：查詢遷移狀態

```bash
curl "http://localhost:8688/api/v1/migration/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "current_step": 4,
  "total_steps": 4,
  "progress_pct": 100.0,
  "error": null
}
```

#### 步驟四：回滾 (若遷移失敗)

```bash
curl -X POST "http://localhost:8688/api/v1/migration/550e8400-e29b-41d4-a716-446655440000/rollback" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "success": true,
  "message": "Rollback completed"
}
```

### 8.5 遷移步驟詳解

#### VMware → KVM (virt-v2v)

| 步驟 | 動作 | 說明 | 命令 |
|------|------|------|------|
| 1 | export | 從 vSphere 匯出 VM 磁碟 | 匯出 OVA (描述性步驟) |
| 2 | convert | 使用 virt-v2v 轉換磁碟格式 | `virt-v2v -i ova disk.ova -o local -os /var/lib/libvirt/images` |
| 3 | import | 將轉換後的 VM 匯入 libvirt | `virsh define converted-vm.xml` |
| 4 | verify | 驗證 VM 啟動與網路連線 | `virsh dominfo <vm_id>` (描述性步驟) |

#### VMware ↔ FusionSphere / KVM → VMware (qemu-img-convert)

| 步驟 | 動作 | 說明 | 命令 |
|------|------|------|------|
| 1 | export | 從來源平台匯出磁碟映像 | 下載磁碟映像 (描述性步驟) |
| 2 | convert | qemu-img 轉換磁碟格式 | `qemu-img convert -f vmdk -O qcow2 source.vmdk target.qcow2` |
| 3 | import | 匯入至目標平台 | 從轉換後磁碟建立 VM (描述性步驟) |
| 4 | verify | 驗證 VM 啟動 | 檢查 VM 狀態 (描述性步驟) |

#### 同平台即時遷移 (live-migrate)

| 步驟 | 動作 | 說明 | 命令 |
|------|------|------|------|
| 1 | pre_check | 驗證來源/目標相容性 | 檢查資源 (描述性步驟) |
| 2 | migrate | 執行即時遷移 | 即時遷移 VM (描述性步驟) |
| 3 | verify | 驗證目標主機上的 VM | 檢查 VM 狀態 (描述性步驟) |

### 8.6 已知限制

- **描述性步驟**：遷移計劃中以 `is_descriptive=true` 標記的步驟不會在 `execute` 時實際執行子進程命令，僅記錄於日誌中
- **引擎為模組級單例**：`MigrationEngine` 使用 `engine = MigrationEngine()` 模組級單例模式，非依賴注入
- **計劃儲存於記憶體**：服務重啟後所有遷移計劃遺失
- **子進程逾時**：每個步驟的執行逾時為 3600 秒 (1 小時)
- **回滾為標記式**：回滾操作僅將步驟狀態標記為 `rolled_back`，不實際執行逆向命令

---

## 9. 儀表板操作

### 9.1 功能概述

儀表板提供系統資源、告警、操作的彙總檢視，協助運維人員快速掌握整體健康狀態。

### 9.2 儀表板組件

| 組件 | 說明 | 資料來源 |
|------|------|----------|
| **StatCards** | 四個統計卡片：總資產數、活躍告警數、待審批操作數、運行中資產數 | `GET /dashboard/summary` |
| **AlertDistribution** | 環形圖 (Donut Chart)，依嚴重等級顯示告警分佈 | `GET /dashboard/summary` |
| **ResourceUsage** | 長條圖，依類型顯示資源使用量 | `GET /dashboard/summary` |
| **RecentOperations** | 最近操作列表，含狀態與時間 | `GET /dashboard/summary` |
| **AlertSummary** | 依狀態 (active/acknowledged/resolved) 彙總告警數量 | `GET /dashboard/summary` |
| **TrendChart** | 7 天趨勢折線圖 (CPU、記憶體、告警數量) | `GET /dashboard/trends?days=7` |

### 9.3 Dashboard Summary API

```bash
curl "http://localhost:8688/api/v1/dashboard/summary" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "total_assets": 156,
  "assets_by_type": [
    {"asset_type": "vm", "count": 120},
    {"asset_type": "host", "count": 12},
    {"asset_type": "storage", "count": 8},
    {"asset_type": "network", "count": 10},
    {"asset_type": "database", "count": 5},
    {"asset_type": "container", "count": 1}
  ],
  "assets_by_status": [
    {"status": "running", "count": 130},
    {"status": "stopped", "count": 18},
    {"status": "error", "count": 3},
    {"status": "maintenance", "count": 5}
  ],
  "active_alerts": 23,
  "alerts_by_severity": [
    {"severity": "P0", "count": 1},
    {"severity": "P1", "count": 3},
    {"severity": "P2", "count": 8},
    {"severity": "P3", "count": 7},
    {"severity": "P4", "count": 4}
  ],
  "recent_operations": [
    {"id": 45, "title": "AI 推薦操作: diagnose", "status": "completed", "created_at": "2026-06-01T10:30:00Z"}
  ],
  "operations_pending_approval": 5
}
```

### 9.4 Dashboard Trends API

```bash
# 取得最近 7 天的趨勢資料 (預設)
curl "http://localhost:8688/api/v1/dashboard/trends?days=7" \
  -H "Authorization: Bearer <TOKEN>"

# 取得最近 30 天的趨勢資料
curl "http://localhost:8688/api/v1/dashboard/trends?days=30" \
  -H "Authorization: Bearer <TOKEN>"
```

**回應範例**：

```json
{
  "days": 7,
  "cpu_trend": {
    "name": "CPU Usage",
    "unit": "%",
    "data": [
      {"timestamp": "2026-05-26T00:00:00Z", "value": 0.0},
      {"timestamp": "2026-05-27T00:00:00Z", "value": 0.0}
    ]
  },
  "memory_trend": {
    "name": "Memory Usage",
    "unit": "%",
    "data": [
      {"timestamp": "2026-05-26T00:00:00Z", "value": 0.0},
      {"timestamp": "2026-05-27T00:00:00Z", "value": 0.0}
    ]
  },
  "alert_trend": {
    "name": "Alert Count",
    "unit": "count",
    "data": [
      {"timestamp": "2026-05-26T00:00:00Z", "value": 5.0},
      {"timestamp": "2026-05-27T00:00:00Z", "value": 3.0}
    ]
  }
}
```

### 9.5 儀表板操作說明

1. **進入 Dashboard** 頁面後，系統自動載入彙總資料與趨勢資料
2. 點選右上角 **Refresh** 按鈕可手動重新整理
3. 刷新時按鈕圖標會旋轉 (animate-spin)，表示正在載入
4. 可切換趨勢天數 (7/14/30 天)，調整 TrendChart 顯示範圍
5. 載入失敗時顯示錯誤卡片，附 **Retry** 按鈕

### 9.6 已知限制

- **CPU/記憶體趨勢資料為佔位符**：`cpu_trend` 和 `memory_trend` 的數值目前為 `0.0`
- 告警趨勢資料為模擬數據

---

## 10. 審計日誌

### 10.1 功能概述

所有變異請求 (POST/PUT/PATCH/DELETE) 皆透過 `AuditMiddleware` 自動記錄至 `audit_logs` 資料表。審計記錄為不可變更 (append-only)。

### 10.2 審計記錄結構

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | int | 記錄 ID |
| `request_id` | string(36) | 請求唯一識別碼 (由 RequestIDMiddleware 產生) |
| `user` | string(255) | 操作使用者 |
| `action` | string(50) | 動作類型 (如 `create_asset`, `acknowledge_alert`) |
| `resource_type` | string(100) | 資源類型 (如 `Asset`, `Alert`, `Operation`) |
| `resource_id` | string(100) | 資源 ID |
| `method` | string(10) | HTTP 方法 (POST/PUT/PATCH/DELETE) |
| `path` | string(500) | 請求路徑 |
| `status_code` | int | HTTP 回應狀態碼 |
| `ip_address` | string(45) | 客戶端 IP 位址 |
| `user_agent` | string(500) | 客戶端 User-Agent |
| `request_body` | text | 請求主體內容 |
| `response_summary` | text | 回應摘要 |
| `duration_ms` | int | 請求處理時間 (毫秒) |
| `created_at` | datetime | 記錄建立時間 |

### 10.3 審計索引

- `ix_audit_user_action` — (user, action) 複合索引，支援快速查詢特定使用者的操作歷史
- `ix_audit_created` — (created_at) 索引，支援時間範圍查詢

### 10.4 審計記錄涵蓋範圍

| 操作類型 | 觸發端點 |
|----------|----------|
| 資產建立/修改/刪除 | POST/PATCH/DELETE `/assets` |
| 告警確認/解決 | PUT `/alerts/{id}/acknowledge`, PUT `/alerts/{id}/resolve` |
| 操作建立/審批/拒絕 | POST `/operations`, PUT `/operations/{id}/approve`, PUT `/operations/{id}/reject` |
| 平台建立/修改/刪除 | POST/PUT/DELETE `/platforms` |
| 平台測試/同步 | POST `/platforms/{id}/test`, POST `/platforms/{id}/sync` |
| 資產快速操作 | POST `/assets/{id}/actions` |
| 遷移計劃/執行/回滾 | POST `/migration/plan`, POST `/migration/execute`, POST `/migration/{id}/rollback` |

> **注意**：唯讀操作 (GET / HEAD) 不記錄審計日誌。

---

## 11. 鍵盤快捷鍵

### 11.1 全域快捷鍵

| 快捷鍵 | 功能 | 說明 |
|--------|------|------|
| `Ctrl + K` | 開啟命令面板 | 全域搜尋與快速導覽 (CommandPalette) |
| `Escape` | 關閉彈窗/面板 | 關閉 CommandPalette、Modal 等 |
| `/` | 快速跳轉至 Chat | 在非輸入框焦點時按下，直接導向 AI 助手頁面 |

### 11.2 命令面板操作

| 按鍵 | 功能 |
|------|------|
| `Ctrl + K` | 開啟命令面板 |
| `↑` / `↓` | 上下移動選擇 |
| `Enter` | 執行選取項目 |
| `Escape` | 關閉命令面板 |
| 文字輸入 | 即時過濾命令 |

### 11.3 命令面板支援的操作

| 類別 | 命令 | 說明 |
|------|------|------|
| navigation | Go to Chat | 前往 AI 助手頁面 |
| navigation | Go to Dashboard | 前往儀表板 |
| navigation | Go to Resources | 前往資源管理 |
| navigation | Go to Alerts | 前往告警管理 |
| action | Diagnose Issue | 開始診斷工作流程 (導向 Chat) |

### 11.4 Chat 輸入框快捷鍵

| 按鍵 | 功能 |
|------|------|
| `Enter` | 發送訊息 |
| `Shift + Enter` | 換行 (不發送) |

### 11.5 側邊欄

| 操作 | 功能 |
|------|------|
| 點選折疊按鈕 | 桌面端收合/展開側邊欄 |
| 點選漢堡選單 | 行動端開啟導覽浮層 |
| 點選遮罩/連結 | 行動端關閉導覽浮層 |

---

## 12. API 參考

### 12.1 API 概覽

| 模組 | 前綴 | 端點數量 | 說明 |
|------|------|----------|------|
| Health | - | 4 | 健康檢查 (liveness/readiness/db/redis) |
| Alerts | `/alerts` | 4 | 告警清單/詳情/確認/解決 |
| Assets | `/assets` | 6 | 資產 CRUD + 快速操作 |
| Atomics | `/atomics` | 2 | 原子操作清單/詳情 |
| Dashboard | `/dashboard` | 2 | 儀表板彙總/趨勢 |
| Operations | `/operations` | 5 | 操作 CRUD + 審批/拒絕 |
| Platforms | `/platforms` | 8 | 平台 CRUD + 測試/同步/設備 |
| Chat | `/chat` | 1 | AI 對話 |
| Migration | `/migration` | 4 | 遷移計劃/執行/狀態/回滾 |

**Base URL**: `http://localhost:8688/api/v1`

### 12.2 認證

所有 API 端點 (除 Health 外) 需要 JWT Bearer Token 認證：

```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" http://localhost:8688/api/v1/...
```

開發模式下可設定 `DEV_DEFAULT_USER=dev-user` 跳過認證。

JWT Token 設定：
- 演算法：HS256
- Access Token 有效期：30 分鐘 (可設定)
- Refresh Token 有效期：7 天 (可設定)

### 12.3 通用回應格式

**成功回應**：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

**錯誤回應**：

```json
{
  "success": false,
  "error": {
    "code": "ASSET_NOT_FOUND",
    "message": "Asset with id '999' not found",
    "details": null
  }
}
```

### 12.4 通用錯誤碼

| HTTP 狀態碼 | 錯誤碼 | 說明 |
|-------------|--------|------|
| 400 | `HTTP_400` | 請求格式錯誤 |
| 401 | `UNAUTHORIZED` | 未認證或 Token 無效/過期 |
| 403 | `FORBIDDEN` | 權限不足 |
| 404 | `<RESOURCE>_NOT_FOUND` | 資源不存在 |
| 409 | `CONFLICT` | 資源衝突 |
| 422 | `VALIDATION_ERROR` | 請求驗證失敗 |
| 500 | `INTERNAL_ERROR` | 伺服器內部錯誤 |
| 500 | `OPERATION_FAILED` | 操作執行失敗 |

### 12.5 健康檢查端點

| 方法 | 路徑 | 說明 | 成功狀態碼 |
|------|------|------|-----------|
| GET | `/health` | Liveness 探針 (進程存活) | 200 |
| GET | `/ready` | Readiness 探針 (含 DB + Redis) | 200 / 503 (降級) |
| GET | `/health/db` | 資料庫健康檢查 (SELECT 1) | 200 / 503 |
| GET | `/health/redis` | Redis 健康檢查 (PING) | 200 / 503 |

**`/health` 回應範例**：

```json
{
  "status": "healthy",
  "version": "3.1.0"
}
```

**`/ready` 回應範例**：

```json
{
  "status": "ready",
  "version": "3.1.0",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 2.34},
    "redis": {"status": "healthy", "latency_ms": 1.12, "pong": true}
  }
}
```

### 12.6 完整 API 端點明細

#### Alerts

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| GET | `/alerts` | 告警列表 | `severity`, `status`, `asset_id`, `page`, `limit` | - |
| GET | `/alerts/{alert_id}` | 告警詳情 | - | - |
| PUT | `/alerts/{alert_id}/acknowledge` | 確認告警 | - | `{"notes": "string"}` |
| PUT | `/alerts/{alert_id}/resolve` | 解決告警 | - | `{"resolution_notes": "string"}` |

#### Assets

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| GET | `/assets` | 資產列表 | `asset_type`, `platform`, `status`, `search`, `page`, `limit` | - |
| GET | `/assets/{asset_id}` | 資產詳情 | - | - |
| POST | `/assets` | 建立資產 | - | AssetCreate schema |
| PATCH | `/assets/{asset_id}` | 更新資產 | - | AssetUpdate schema |
| DELETE | `/assets/{asset_id}` | 刪除資產 | - | - |
| POST | `/assets/{asset_id}/actions` | 快速操作 | - | `{"action": "boot/shutdown/restart", "confirm": true}` |

#### Atomics

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| GET | `/atomics` | 原子操作列表 | `category`, `search` | - |
| GET | `/atomics/{operation_id}` | 單一原子操作 | - | - |

#### Dashboard

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| GET | `/dashboard/summary` | 儀表板彙總 | - | - |
| GET | `/dashboard/trends` | 趨勢資料 | `days` (1-90, 預設 7) | - |

#### Operations

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| GET | `/operations` | 操作列表 | `status`, `asset_id`, `page`, `limit` | - |
| GET | `/operations/{operation_id}` | 操作詳情 | - | - |
| POST | `/operations` | 建立操作 | - | OperationCreateRequest schema |
| PUT | `/operations/{operation_id}/approve` | 審批操作 | - | `{}` |
| PUT | `/operations/{operation_id}/reject` | 拒絕操作 | - | `{"reason": "string"}` |

#### Platforms

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| GET | `/platforms/` | 平台列表 | - | - |
| POST | `/platforms/` | 新增平台 | - | PlatformCreateRequest |
| GET | `/platforms/{platform_id}` | 平台詳情 | - | - |
| PUT | `/platforms/{platform_id}` | 更新平台 | - | PlatformUpdateRequest |
| DELETE | `/platforms/{platform_id}` | 刪除平台 | - | - |
| POST | `/platforms/{platform_id}/test` | 測試連線 | - | - |
| POST | `/platforms/{platform_id}/sync` | 同步設備 | - | - |
| GET | `/platforms/{platform_id}/devices` | 設備列表 | - | - |

#### Chat

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| POST | `/chat` | 發送訊息 | - | `{"message": "string", "conversation_id": null}` |

#### Migration

| 方法 | 路徑 | 說明 | 查詢參數 | 請求主體 |
|------|------|------|----------|----------|
| POST | `/migration/plan` | 產生遷移計劃 | - | `{"vm_id": "string", "source": "string", "target": "string"}` |
| POST | `/migration/execute` | 執行遷移 | `plan_id` (query) | - |
| GET | `/migration/{plan_id}` | 查詢狀態 | - | - |
| POST | `/migration/{plan_id}/rollback` | 回滾遷移 | - | - |

### 12.7 分頁說明

所有列表端點支援分頁，使用以下查詢參數：

| 參數 | 類型 | 預設值 | 限制 | 說明 |
|------|------|--------|------|------|
| `page` | int | 1 | >= 1 | 頁碼 |
| `limit` | int | 20 (alerts/ops) / 50 (assets) | 1-100 (alerts/ops) / 1-200 (assets) | 每頁筆數 |

分頁回應格式：

```json
{
  "items": [...],
  "total": 156,
  "page": 1,
  "limit": 50,
  "pages": 4
}
```

---

## 13. 常見問題 FAQ

### 13.1 啟動與環境

**Q: 啟動後端時出現 `ModuleNotFoundError: No module named 'app'`**

A: 請確認您在 `backend/` 目錄下執行命令，且已啟動虛擬環境：

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8688
```

**Q: 資料庫連線失敗**

A: 請確認 PostgreSQL 容器已啟動：

```bash
docker compose up -d postgres
# 檢查 PostgreSQL 狀態
docker compose ps
```

確認 `.env` 檔案中的 `DATABASE_URL` 正確。若使用 Docker Compose 啟動後端，資料庫主機名為 `postgres`（容器間通訊）；若在本地啟動後端，主機名為 `localhost`。

**Q: 前端畫面空白或無法載入**

A:
1. 確認後端已啟動且可存取：`curl http://localhost:8688/health`
2. 確認前端開發伺服器已啟動：`cd frontend && npm run dev`
3. 檢查瀏覽器 Console 是否有 CORS 錯誤
4. 確認 `.env` 中的 `CORS_ORIGINS` 包含前端 URL (`http://localhost:5173`)

**Q: 開發模式下 JWT Token 認證失敗**

A: 確認 `.env` 中設定了 `DEV_DEFAULT_USER=dev-user`。設定後，未附帶 Authorization Header 的請求將自動使用 `dev-user` 身份。

### 13.2 平台管理

**Q: 平台密碼如何儲存？**

A: 平台密碼在寫入資料庫前透過 Fernet 對稱加密。加密金鑰由 `ENCRYPTION_KEY` 環境變數設定。若未設定，系統將無法加密/解密密碼。

**Q: 測試連線失敗，但憑證正確**

A: 請檢查以下項目：
1. 網路連通性：後端伺服器是否能存取目標平台主機
2. SSL 憑證：若目標使用自簽憑證，請將 `verify_ssl` 設為 `false`
3. 防火牆規則：確認目標埠號未被阻擋
4. 平台 SDK 依賴：vSphere 需要 pyVmomi，KVM 需要 libvirt-python

**Q: 同步設備後資產數量與預期不符**

A: 同步操作會將平台上的 VM 與 Host 匯入 `assets` 表。若數量不符，請檢查：
1. 平台權限：使用者是否具有列出所有 VM 的權限
2. 平台 API 限制：部分平台 API 可能有分頁限制

### 13.3 資產管理

**Q: 快速操作 (boot/shutdown/restart) 沒有實際效果**

A: 快速操作目前為 stub 實作 ── 命令被記錄但不會實際觸發平台層級的 VM 操作。請透過原子操作或建立正式變更工單來執行實際操作。

**Q: 批次操作按鈕存在但無法使用**

A: 批次操作 UI 已實作在前端，但後端尚未實作批次處理端點。這是一個已知限制。

**Q: 如何大量匯入資產？**

A: 可以使用以下方式：
1. 平台同步：先新增平台，再執行 `POST /platforms/{id}/sync` 同步設備
2. CSV 匯入：前端提供 `importDevicesCSV` API 函數 (於 `frontend/src/api/platforms.ts`)
3. API 批次建立：透過腳本循環呼叫 `POST /assets`

### 13.4 告警管理

**Q: 告警狀態轉換規則**

A:
- `active` → `acknowledged`：確認告警 (PUT `/alerts/{id}/acknowledge`)
- `acknowledged` → `resolved`：解決告警 (PUT `/alerts/{id}/resolve`)
- `active` → 不可直接跳至 `resolved`，必須先經過 `acknowledged`
- `active` → `suppressed`：抑制告警 (目前已定義狀態但 API 尚未實作)

**Q: 告警可以修改內容嗎？**

A: 告警內容 (`title`, `description`, `severity`) 不可修改。僅可操作狀態變更 (確認/解決)。

### 13.5 AI 助手

**Q: AI 助手為什麼無法理解我的問題？**

A: AI 助手使用規則式意圖識別 (正則匹配)，非 LLM 模型。請嘗試：
1. 使用更簡潔明確的描述
2. 參考 [第 6.3 節](#63-支援的意圖類型) 的觸發關鍵詞
3. 輸入「幫助」查看支援的功能清單
4. 包含具體的主機名稱或目標

**Q: 對話歷史在重新整理後消失**

A: Chat 上下文 (ConversationContext) 僅存於後端記憶體，服務重啟後會遺失。前端對話歷史也存在於瀏覽器記憶體中，重新整理頁面會重置。

**Q: 推薦操作如何轉換為工單？**

A: 在 AI 助手回傳推薦步驟後：
1. 勾選要執行的步驟
2. 點選 **Execute All** 或 **Execute Selected**
3. 在 ConfirmDialog 中確認風險
4. 系統自動呼叫 `POST /operations` 建立工單

### 13.6 遷移

**Q: 遷移執行後步驟停留在 pending 狀態**

A: 遷移引擎中標記為 `is_descriptive=true` 的步驟不會實際執行子進程命令。只有包含可執行命令的步驟 (如 `virt-v2v` 轉換步驟) 才會實際執行。這表示部分步驟需要人工介入完成。

**Q: 遷移失敗後如何回滾？**

A: 使用 `POST /migration/{plan_id}/rollback`。請注意回滾為標記式操作 ── 僅將步驟狀態標記為 `rolled_back`，不實際執行逆向命令。建議在遷移前先建立 VM 快照。

**Q: 支援哪些遷移路徑？**

A:
- VMware → KVM (virt-v2v)
- VMware → FusionSphere (qemu-img-convert)
- KVM → VMware (qemu-img-convert)
- 同平台即時遷移 (live-migrate)
- 不支援：FusionSphere → KVM, FusionSphere → VMware (需自訂流程)

### 13.7 儀表板

**Q: CPU 和記憶體趨勢圖顯示數值為 0**

A: 這是已知限制。`cpu_trend` 和 `memory_trend` 的資料目前為佔位值 (0.0)。告警趨勢為模擬數據。

**Q: Dashboard 資料何時更新？**

A: Dashboard 資料於每次請求時即時查詢資料庫。可點選 **Refresh** 按鈕手動更新。無自動輪詢機制。

### 13.8 安全性

**Q: 某些 GET 端點是否需要認證？**

A: 目前大多數 GET 端點需要 JWT Token 認證，但部分端點在特定設定下可能不需要。正式環境建議全面啟用認證並設定強密碼的 JWT_SECRET_KEY。

**Q: JWT Token 過期後如何處理？**

A: Access Token 過期 (預設 30 分鐘) 後需使用 Refresh Token 取得新的 Access Token。Refresh Token 有效期為 7 天。

---

## 14. 最佳實踐

### 14.1 一般運維原則

1. **先診斷，後操作**：遇到問題時先使用 AI 助手的診斷功能 (`diagnose` 意圖)，確認問題根因後再執行修復操作。

2. **善用審批流程**：所有高風險和嚴重風險的操作必須經過審批流程 (pending → approved → executing)。不要繞過審批機制。

3. **留下審計記錄**：所有變更操作應透過平台 API 執行，確保自動記錄審計日誌。避免直接登入平台後端執行操作。

4. **建立變更工單**：使用 AI 助手的推薦操作功能，自動將原子操作轉換為正式工單，確保操作可追溯。

### 14.2 告警處理流程

建議採用以下告警處理 SOP：

```
1. 告警觸發 → 2. 確認告警 (Acknowledge) → 3. 診斷問題
       ↓                                         ↓
   4. 執行修復 (經 AI 助手或手動) → 5. 驗證修復 → 6. 解決告警 (Resolve)
```

處理重點：
- P0/P1 告警應在接收後 5-15 分鐘內確認
- 確認時填寫具體的處理備註 (`notes`)
- 解決時填寫詳細的解決記錄 (`resolution_notes`)，供後續事件回顧

### 14.3 資產管理建議

1. **命名規範**：建立一致的資產命名規範，例如 `<環境>-<角色>-<編號>`（如 `prod-web-01`）
2. **標籤管理**：善用 `tags` 欄位標記角色、部門、專案等分類
3. **環境標記**：使用 `environment` 欄位區分 production/staging/development
4. **定期同步**：定期執行平台設備同步，確保資產清單與實際平台一致

### 14.4 AI 助手使用建議

1. **明確的目標描述**：包含主機名稱 + 具體問題描述，如「web-01 CPU 使用率過高」
2. **輸入「幫助」**：不確定可用功能時，隨時輸入「幫助」查看功能清單
3. **善用上下文**：AI 助手會記住最近 5 個目標，後續操作可省略主機名稱
4. **審查建議再執行**：仔細閱讀 AI 回傳的風險評估和預估時間，確認無誤後再建立工單

### 14.5 遷移操作建議

1. **遷移前建立快照**：使用 `compute.vm_snapshot` 建立 VM 快照作為回滾點
2. **驗證目標環境**：確認目標平台有足夠的 CPU、記憶體、儲存資源
3. **安排維護窗口**：即使支援即時遷移，仍建議安排在維護窗口內執行
4. **遷移後驗證**：遷移完成後驗證 VM 啟動狀態、網路連線、應用程式功能

### 14.6 安全建議

1. **正式環境設定**：
   - `JWT_SECRET_KEY` 必須使用強密碼（建議 `openssl rand -hex 64` 產生）
   - `DEBUG` 必須設為 `false`
   - `ENCRYPTION_KEY` 必須設定，用於加密平台密碼

2. **密碼管理**：
   - 平台密碼應使用專用服務帳號，避免使用個人帳號
   - 定期更新平台密碼
   - 不要在日誌中輸出任類型的密碼

3. **API 限流**：
   - 預設每分鐘 60 次請求 (`RATE_LIMIT_PER_MINUTE`)
   - 正式環境依實際需求調整

### 14.7 監控與健康檢查

1. **健康檢查端點**：
   - 使用 `/health` 作為 Kubernetes liveness probe
   - 使用 `/ready` 作為 Kubernetes readiness probe
   - 定期檢查 `/health/db` 和 `/health/redis` 確保依賴服務正常

2. **日誌管理**：
   - 正式環境建議使用 `LOG_FORMAT=json` 以利於日誌聚合
   - 設定 `LOG_LEVEL=INFO` 減少不必要的 DEBUG 日誌

### 14.8 資料庫維護

1. **定期備份**：透過 `backup.create` 原子操作或外部工具定期備份 PostgreSQL
2. **連線池監控**：監控 `DB_POOL_SIZE` (預設 20) 和 `DB_MAX_OVERFLOW` (預設 10) 的使用率
3. **資料清理**：定期檢查 `audit_logs` 資料表的增長，必要時歸檔歷史記錄

### 14.9 已知限制與注意事項總結

| 項目 | 限制 | 影響 | 建議 |
|------|------|------|------|
| 資產快速操作 | Stub 實作 | boot/shutdown/restart 不實際執行 | 使用原子操作或變更工單 |
| 遷移命令 | 描述性步驟不實際執行 | 部分步驟需人工介入 | 在遷移 SOP 中標註人工步驟 |
| Chat 上下文 | 僅存於記憶體 | 服務重啟後遺失 | 重要對話應建立工單保存 |
| Dashboard 趨勢 | CPU/記憶體為佔位值 | 趨勢圖不反映實際數據 | 依賴外部監控系統 (如 Prometheus) |
| 批次操作 | 後端未實作 | 批次按鈕為 no-op | 使用 API 腳本進行批次處理 |
| 部分 GET 端點 | 可能不需認證 | 資訊洩漏風險 | 正式環境全面啟用認證 |
| Chat 串流 | 無 WebSocket | 無法即時顯示 AI 回應 | 目前為同步 HTTP 請求/回應 |
| 遷移引擎 | 模組級單例 | 計劃在重啟後遺失 | 重要遷移應記錄 plan_id |

---

> **文件版本**: v3.2.0-ops-20260601
>
> **生成工具**: 基於 Inspection V3.2 程式碼庫自動分析生成
>
> **維護者**: SRE Platform Team
>
> 本文件基於 `C:\cc\Inspection\v3.2\` 程式碼庫的實際分析撰寫，涵蓋後端 9 個 API 模組、前端 5 個主要視圖、109 個原子操作、以及完整的資料庫模型與中間件實現。
