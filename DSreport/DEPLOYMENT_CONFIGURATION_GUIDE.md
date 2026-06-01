# Inspection V3.2 - SRE 工程師輔助平台<br>部署與設定完整指南

> **版本**: 3.2.0 | **文件日期**: 2026-06-01 | **文件用途**: 部署、設定與維運參考手冊

---

## 目錄

1. [系統需求](#1-系統需求)
2. [環境變數完整設定表](#2-環境變數完整設定表)
3. [Docker Compose 部署（開發環境）](#3-docker-compose-部署開發環境)
4. [Docker 生產環境部署](#4-docker-生產環境部署)
5. [本機開發環境部署](#5-本機開發環境部署)
6. [資料庫初始化與遷移](#6-資料庫初始化與遷移)
7. [設定檔對照表](#7-設定檔對照表)
8. [安全性設定要點](#8-安全性設定要點)
9. [監控與健康檢查](#9-監控與健康檢查)
10. [備份與災難恢復](#10-備份與災難恢復)
11. [常見問題排查](#11-常見問題排查)
12. [已知問題與風險](#12-已知問題與風險)
13. [附錄：完整目錄結構](#13-附錄完整目錄結構)

---

## 1. 系統需求

### 1.1 硬體需求

| 資源 | 開發環境（最低） | 開發環境（建議） | 測試環境 | 生產環境 |
|------|-----------------|-----------------|---------|---------|
| CPU | 2 核心 | 4 核心 | 4 核心 | 8+ 核心 |
| 記憶體 | 4 GB | 8 GB | 8 GB | 16 GB+ |
| 磁碟 | 20 GB SSD | 50 GB SSD | 50 GB SSD | 200 GB SSD (RAID-1) |
| 網路 | 100 Mbps | 1 Gbps | 1 Gbps | 1 Gbps 雙鏈路 |

### 1.2 軟體需求

| 軟體 | 版本 | 用途 | 必要性 |
|------|------|------|--------|
| Docker | 24.0+ | 容器引擎 | **必須** (Docker 部署) |
| Docker Compose | 2.20+ | 容器編排 | **必須** (Docker 部署) |
| Git | 2.30+ | 版本控制 | **必須** |
| Python | 3.12+ | 後端執行環境 | 本機開發必須 |
| Node.js | 20 LTS+ | 前端建構 | 本機開發必須 |
| PostgreSQL | 16 | 關聯式資料庫 | 非容器化部署必須 |
| Redis | 7 | 快取 / 訊息佇列 | 非容器化部署必須 |
| OpenSSL | 1.1+ | 憑證與金鑰產生 | 生產環境必須 |

> **重要說明**: README.md 宣稱 Python 3.14.5，但 `backend/Dockerfile` 實際使用 `python:3.12-slim` 基礎映像；`backend/pyproject.toml` 要求 `requires-python = ">=3.12"`。**Python 3.12 為目前實際驗證版本**，Python 3.14 不應作為部署標準。

### 1.3 網路埠號需求

| 服務 | 埠號 | 通訊協定 | 說明 | 備註 |
|------|------|----------|------|------|
| Frontend (Vite) | 3000 | HTTP | React 開發伺服器 | `vite.config.ts` 定義 |
| Frontend (Docker) | 5173 | HTTP | Vite 容器內埠號 | 與 vite.config.ts (3000) **不一致** |
| Backend | 8688 | HTTP | FastAPI uvicorn | `Dockerfile` EXPOSE 8688 |
| PostgreSQL | 5432 | TCP | 資料庫連線 | docker-compose 暴露 |
| Redis | 6379 | TCP | 快取/佇列 | docker-compose 暴露 |

> **Port 不一致警告**: 前端在 `vite.config.ts` 中設定埠號為 **3000**，但在 `docker-compose.yml` 及 `frontend/Dockerfile` 中使用 **5173**。這是已知的埠號不一致問題，開發與容器化環境需分別對應正確埠號：

| 啟動方式 | 前端埠號 | 後端代理埠號 |
|----------|---------|-------------|
| `npm run dev`（本機） | **3000** | 8688 (透過 Vite proxy) |
| `docker compose up` | **5173** | 8688 (直接呼叫) |

### 1.4 防火牆規則需求

| 方向 | 來源 | 目標 | 埠號 | 通訊協定 |
|------|------|------|------|----------|
| 入站 | 使用者 | Frontend | 3000 或 5173 | TCP/HTTP |
| 入站 | 使用者 | Backend | 8688 | TCP/HTTP |
| 內部 | Backend | PostgreSQL | 5432 | TCP |
| 內部 | Backend | Redis | 6379 | TCP |
| 出站 | Backend | vCenter/ESXi | 443 | TCP/HTTPS |
| 出站 | Backend | KVM 主機 | 22 | TCP/SSH |
| 出站 | Backend | FusionSphere | 7443 (預設) | TCP/HTTPS |

---

## 2. 環境變數完整設定表

### 2.1 後端環境變數 (`backend/.env.example` 完整規格)

本節依據 `backend/app/config.py` (pydantic-settings BaseSettings) 以及 `backend/.env.example` 進行完整記錄。

| 變數名稱 | 型別 | 預設值 | 說明 | 必填 | 生產注意事項 |
|----------|------|--------|------|------|-------------|
| **應用程式** | | | | | |
| `APP_NAME` | `str` | `Engineer Assist` | 應用程式顯示名稱 | 否 | 無特別限制 |
| `APP_VERSION` | `str` | `3.1.0` | 語意化版本號 | 否 | **注意**: pyproject.toml 預設為 3.1.0，但專案版本為 3.2.0 |
| `APP_ENV` | `str` | `development` | 執行環境：`development` / `staging` / `production` | 否 | 生產須設為 `production` |
| `DEBUG` | `bool` | `false` | 除錯模式開關 | 否 | 生產**必須**為 `false` |
| `API_V1_PREFIX` | `str` | `/api/v1` | API 版本化前綴 | 否 | 不可輕易變更 |
| **資料庫** | | | | | |
| `DATABASE_URL` | `str` | `""` (空字串) | PostgreSQL 連線字串 | 生產必填 | 格式：`postgresql+asyncpg://user:pass@host:5432/dbname` |
| `DB_ECHO` | `bool` | `false` | SQL 語句日誌輸出 | 否 | 生產應保持 `false` |
| `DB_POOL_SIZE` | `int` | `20` | 持久連線池大小 | 否 | 建議維持預設值 |
| `DB_MAX_OVERFLOW` | `int` | `10` | 超過 pool_size 的額外連線數 | 否 | 最大值為 pool_size + max_overflow = 30 |
| **Redis** | | | | | |
| `REDIS_URL` | `str` | `redis://localhost:6379/0` | Redis 連線字串 | 否 | 生產應設為實際 Redis 位址 |
| **JWT 認證** | | | | | |
| `JWT_SECRET_KEY` | `str` | `""` (開發時自動產生) | JWT 簽章密鑰 | 生產**必填** | 使用 `openssl rand -hex 64` 產生 |
| `JWT_ALGORITHM` | `str` | `HS256` | JWT 簽章演算法 | 否 | 支援 HS256/HS384/HS512，建議 RS256 作非對稱 |
| `JWT_ACCESS_EXPIRE_MINUTES` | `int` | `30` | Access Token 有效期（分鐘） | 否 | 建議維持 15-30 分鐘 |
| `JWT_REFRESH_EXPIRE_DAYS` | `int` | `7` | Refresh Token 有效期（天） | 否 | 建議維持 7 天 |
| **CORS** | | | | | |
| `CORS_ORIGINS` | `str` | `http://localhost:3000,http://localhost:5173` | 允許的來源網域（逗號分隔） | 生產必填 | 生產應設為實際前端網域，如 `https://sre.example.com` |
| **日誌** | | | | | |
| `LOG_LEVEL` | `str` | `INFO` | 最低日誌級別 | 否 | 有效值：`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | `str` | `json` | 日誌輸出格式 | 否 | `json` (結構化 JSON) 或 `console` (人類可讀) |
| **速率限制** | | | | | |
| `RATE_LIMIT_PER_MINUTE` | `int` | `60` | 每個客戶端每分鐘最大 API 請求數 | 否 | 可依負載調整 |
| **加密** | | | | | |
| `ENCRYPTION_KEY` | `str` | `""` | Fernet 密鑰，用於加密平台密碼 | 生產必填 | 使用 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 產生 |
| **開發驗證** | | | | | |
| `DEV_DEFAULT_USER` | `str` | `""` | 開發環境預設使用者名稱 | 否 | 僅在 `APP_ENV=development` 且無 Authorization 標頭時生效 |

### 2.2 前端環境變數 (`frontend/.env.example`)

| 變數名稱 | 型別 | 預設值 | 說明 | 必填 |
|----------|------|--------|------|------|
| `VITE_API_BASE_URL` | `string` | `/api/v1` | API 基礎路徑（開發時透過 Vite proxy 轉發） | 否 |
| `VITE_WS_URL` | `string` | `ws://localhost:8688/ws` | WebSocket 連線網址 | 否 |

### 2.3 Docker Compose 環境變數 (`docker-compose.yml`)

| 變數名稱 | 使用服務 | 值 | 說明 |
|----------|---------|-----|------|
| `POSTGRES_DB` | postgres | `v32_sre` | 資料庫名稱 |
| `POSTGRES_USER` | postgres | `v32` | 資料庫使用者 |
| `POSTGRES_PASSWORD` | postgres | `${DB_PASSWORD:-v32_dev_password}` | 資料庫密碼（可透過 `.env` 覆蓋） |
| `DATABASE_URL` | backend | `postgresql+asyncpg://v32:${DB_PASSWORD:-v32_dev_password}@postgres:5432/v32_sre` | 後端資料庫連線 |
| `REDIS_URL` | backend | `redis://redis:6379/0` | 後端 Redis 連線 |
| `APP_ENV` | backend | `development` | 執行環境 |
| `APP_DEBUG` | backend | `true` | 除錯模式 |
| `LOG_LEVEL` | backend | `DEBUG` | 日誌級別 |
| `JWT_SECRET_KEY` | backend | `${JWT_SECRET_KEY:-dev-secret-key}` | JWT 密鑰 |
| `DEV_DEFAULT_USER` | backend | `dev-user` | 開發預設使用者 |

### 2.4 JWT 設定細節

| 參數 | 值 | 說明 |
|------|-----|------|
| 演算法 | HS256 | 對稱式 HMAC-SHA256 |
| Access Token 有效期 | 30 分鐘 | 可透過 `JWT_ACCESS_EXPIRE_MINUTES` 調整 |
| Refresh Token 有效期 | 7 天 | 可透過 `JWT_REFRESH_EXPIRE_DAYS` 調整 |
| Token 類型聲明 | `"type": "access"` / `"type": "refresh"` | 用於區分 token 用途 |
| 密碼雜湊 | bcrypt | 使用 passlib[bcrypt] |

### 2.5 平台轉接器預設埠號

| 平台 | 預設埠號 | 環境變數 | 通訊協定 |
|------|---------|----------|----------|
| VMware vSphere | 443 | (無獨立變數) | HTTPS |
| KVM/QEMU | 22 | `KVM_DEFAULT_PORT` | SSH |
| Huawei FusionSphere | 7443 | `FUSIONSPHERE_DEFAULT_PORT` | HTTPS (REST API) |

---

## 3. Docker Compose 部署（開發環境）

### 3.1 架構概覽

```
┌─────────────────────────────────────────────────┐
│                   Docker Network                 │
│                                                  │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐  │
│  │  frontend │  │  backend  │  │   postgres  │  │
│  │  :5173    │──│  :8688    │──│   :5432     │  │
│  │  (Vite)   │  │ (uvicorn) │  │   (PG 16)   │  │
│  └───────────┘  └─────┬─────┘  └────────────┘  │
│                       │                         │
│                  ┌────┴─────┐                   │
│                  │   redis   │                   │
│                  │   :6379   │                   │
│                  └──────────┘                   │
└─────────────────────────────────────────────────┘
```

### 3.2 快速啟動

```bash
# 步驟 1：進入專案目錄
cd C:\cc\Inspection\v3.2

# 步驟 2：複製環境設定檔（可選）
cp .env.example .env

# 步驟 3：啟動所有服務
docker compose up -d

# 步驟 4：驗證服務狀態
docker compose ps
```

預期輸出：
```
NAME            IMAGE                  STATUS                    PORTS
v32-postgres    postgres:16-alpine     Up (healthy)             0.0.0.0:5432->5432/tcp
v32-redis       redis:7-alpine         Up (healthy)             0.0.0.0:6379->6379/tcp
v32-backend     v32-backend            Up                       0.0.0.0:8688->8688/tcp
v32-frontend    v32-frontend           Up                       0.0.0.0:5173->5173/tcp
```

### 3.3 docker-compose.yml 完整解析

```yaml
version: "3.9"

services:
  # ── PostgreSQL 16 ────────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine              # 基於 Alpine Linux 的輕量映像
    container_name: v32-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: v32_sre                 # 資料庫名稱
      POSTGRES_USER: v32                   # 資料庫使用者
      POSTGRES_PASSWORD: ${DB_PASSWORD:-v32_dev_password}  # 支援 .env 覆蓋
    volumes:
      - postgres_data:/var/lib/postgresql/data  # 持久化資料
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U v32 -d v32_sre"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Redis 7 ─────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: v32-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Backend ─────────────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: v32-backend
    restart: unless-stopped
    ports:
      - "8688:8688"
    environment:
      DATABASE_URL: postgresql+asyncpg://v32:${DB_PASSWORD:-v32_dev_password}@postgres:5432/v32_sre
      REDIS_URL: redis://redis:6379/0
      APP_ENV: development
      APP_DEBUG: "true"
      LOG_LEVEL: DEBUG
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-dev-secret-key}
      DEV_DEFAULT_USER: dev-user
    depends_on:
      postgres:
        condition: service_healthy       # 等待 PostgreSQL 健康檢查通過
      redis:
        condition: service_healthy       # 等待 Redis 健康檢查通過
    volumes:
      - ./backend:/app                   # 代碼熱掛載（開發用）
    command: uvicorn app.main:app --host 0.0.0.0 --port 8688 --reload

  # ── Frontend ────────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: v32-frontend
    restart: unless-stopped
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app                  # 代碼熱掛載
      - /app/node_modules                # 匿名卷：防止覆蓋容器內 node_modules
    command: npm run dev -- --host 0.0.0.0
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 3.4 服務依賴關係

```
postgres (健康檢查通過)
    │
    ├──> backend (等待 postgres + redis 健康檢查)
    │
redis (健康檢查通過)
    │
    └──> backend
              │
              └──> frontend (等待 backend 啟動)
```

### 3.5 常用操作

```bash
# 查看所有服務日誌
docker compose logs -f

# 查看後端日誌
docker compose logs -f backend

# 查看前端日誌
docker compose logs -f frontend

# 查看資料庫日誌
docker compose logs -f postgres

# 重啟單一服務
docker compose restart backend

# 重建並重啟單一服務
docker compose up -d --build backend

# 停止所有服務
docker compose down

# 停止所有服務並清除資料卷（警告：會清除資料庫資料）
docker compose down -v

# 進入後端容器
docker compose exec backend bash

# 進入資料庫容器
docker compose exec postgres psql -U v32 -d v32_sre
```

### 3.6 驗證部署

```bash
# 後端健康檢查
curl http://localhost:8688/health
# 期望: {"status":"healthy","version":"3.1.0"}

# 後端就緒檢查
curl http://localhost:8688/ready
# 期望: {"status":"ready","version":"3.1.0","checks":{...}}

# 前端可訪問性
curl -I http://localhost:5173
# 期望: HTTP/1.1 200 OK

# API 端點測試
curl http://localhost:8688/api/v1/assets
curl http://localhost:8688/api/v1/alerts
curl http://localhost:8688/api/v1/operations
```

---

## 4. Docker 生產環境部署

### 4.1 生產環境 Dockerfile 強化建議

> **警告**: 目前專案的 `backend/Dockerfile` 和 `frontend/Dockerfile` 均為**開發用映像**，不適合直接用於生產環境。以下列出已知問題及強化建議。

#### 問題清單

| # | 問題 | 影響 | 嚴重程度 |
|---|------|------|---------|
| 1 | 後端 Dockerfile 以 root 執行 | 安全風險 | **高** |
| 2 | 前端 Dockerfile 僅執行 `npm run dev` | 無生產建構 | **高** |
| 3 | 後端 Dockerfile 無 HEALTHCHECK | 無法自動偵測故障 | **中** |
| 4 | 後端使用 `python:3.12-slim` 而非 `-alpine` | 映像較大 | 低 |
| 5 | 前後端均未設定 `USER` 指令 | 容器以 root 執行 | **高** |

#### 建議的生產用 Backend Dockerfile

```dockerfile
# ── Stage 1: Build ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ───────────────────────────────────────────
FROM python:3.12-slim

# 建立非 root 使用者
RUN groupadd -r sre && useradd -r -g sre -d /app sre

WORKDIR /app

# 安裝執行時期系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 從 builder 複製 Python 套件
COPY --from=builder /root/.local /home/sre/.local

# 複製應用程式代碼
COPY --chown=sre:sre . .

# 切換到非 root 使用者
USER sre

ENV PATH="/home/sre/.local/bin:${PATH}"

# 健康檢查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8688/health')" || exit 1

EXPOSE 8688

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8688", "--workers", "4"]
```

#### 建議的生產用 Frontend Dockerfile（多階段建構）

```dockerfile
# ── Stage 1: Build ─────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: Runtime (Nginx) ───────────────────────────────────
FROM nginx:1.27-alpine

# 複製建構產出
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx 設定（含 API 反向代理）
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 4.2 生產環境 docker-compose.prod.yml

> **注意**: 專案目前不包含 `docker-compose.prod.yml`，但部署腳本 (`scripts/deploy-linux.sh`, `scripts/deploy-windows.ps1`) 均引用它。以下為建議的生產環境設定範本。

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    container_name: v32-postgres-prod
    restart: always
    ports:
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_DB: v32_sre
      POSTGRES_USER: sre_app
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sre_app -d v32_sre"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

  redis:
    image: redis:7-alpine
    container_name: v32-redis-prod
    restart: always
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_prod_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 128M

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: v32-backend-prod
    restart: always
    ports:
      - "127.0.0.1:8688:8688"
    environment:
      DATABASE_URL: postgresql+asyncpg://sre_app:${DB_PASSWORD}@postgres:5432/v32_sre
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      APP_ENV: production
      APP_DEBUG: "false"
      LOG_LEVEL: INFO
      LOG_FORMAT: json
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
      DEV_DEFAULT_USER: ""
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 256M

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: v32-frontend-prod
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 64M

volumes:
  postgres_prod_data:
  redis_prod_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 4.3 生產環境部署步驟

```bash
# 步驟 1：產生密鑰
mkdir -p secrets
openssl rand -hex 64 > secrets/jwt_secret.txt
openssl rand -base64 32 > secrets/db_password.txt
# 產生 Fernet 加密金鑰
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > secrets/fernet_key.txt

# 步驟 2：設定權限
chmod 600 secrets/*.txt

# 步驟 3：設定環境變數
export JWT_SECRET_KEY=$(cat secrets/jwt_secret.txt)
export DB_PASSWORD=$(cat secrets/db_password.txt)
export ENCRYPTION_KEY=$(cat secrets/fernet_key.txt)
export CORS_ORIGINS="https://sre.example.com"

# 步驟 4：建構並啟動
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# 步驟 5：執行資料庫遷移
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 步驟 6：驗證部署
curl http://localhost:8688/health
curl http://localhost/  # 前端 Nginx
```

### 4.4 SSL/TLS 設定（使用 Nginx 反向代理）

```nginx
# /etc/nginx/sites-available/sre-platform (建議的獨立 Nginx 設定)
server {
    listen 80;
    server_name sre.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sre.example.com;

    ssl_certificate     /etc/ssl/certs/sre.example.com.crt;
    ssl_certificate_key /etc/ssl/private/sre.example.com.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # 前端靜態檔案
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 後端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8688;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8688;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4.5 Systemd 服務單元（不使用 Docker 的生產部署）

```ini
# /etc/systemd/system/sre-backend.service
[Unit]
Description=SRE Platform Backend (V3.2)
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=sre
Group=sre
WorkingDirectory=/opt/sre-platform/backend
EnvironmentFile=/opt/sre-platform/.env
ExecStart=/opt/sre-platform/backend/.venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8688 \
    --workers 4 \
    --log-level info
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## 5. 本機開發環境部署

### 5.1 前置準備

```bash
# 驗證軟體版本
python --version    # 必須 >= 3.12
node --version      # 必須 >= 20
docker --version    # 必須 >= 24
git --version       # 必須 >= 2.30
```

### 5.2 Linux / macOS 本機部署

```bash
# ── 步驟 1：啟動基礎設施 ──────────────────────────────────
cd C:\cc\Inspection\v3.2
docker compose up -d postgres redis

# 等待服務就緒
sleep 10
docker compose ps  # 確認 postgres 和 redis 狀態為 healthy

# ── 步驟 2：後端設定 ───────────────────────────────────────
cd backend

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 安裝開發依賴（測試、lint、型別檢查）
pip install pytest pytest-asyncio pytest-cov mypy ruff

# 設定環境變數
export DATABASE_URL="postgresql+asyncpg://v32:v32_dev_password@localhost:5432/v32_sre"
export REDIS_URL="redis://localhost:6379/0"
export APP_ENV="development"
export DEBUG="true"
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="console"
export JWT_SECRET_KEY="dev-secret-key"
export DEV_DEFAULT_USER="dev-user"

# 執行資料庫遷移
alembic upgrade head

# 啟動後端伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8688

# ── 步驟 3：前端設定（新終端視窗）─────────────────────────
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器（埠號 3000）
npm run dev

# ── 步驟 4：存取服務 ───────────────────────────────────────
# 前端: http://localhost:3000
# 後端 API: http://localhost:8688
# API 文件: http://localhost:8688/docs
# API 替代文件: http://localhost:8688/redoc
```

### 5.3 Windows PowerShell 本機部署

```powershell
# ── 步驟 1：啟動基礎設施 ──────────────────────────────────
cd C:\cc\Inspection\v3.2
docker compose up -d postgres redis

# 等待服務就緒
Start-Sleep -Seconds 10
docker compose ps

# ── 步驟 2：後端設定 ───────────────────────────────────────
cd backend

# 建立虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安裝依賴
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov mypy ruff

# 設定環境變數
$env:DATABASE_URL = "postgresql+asyncpg://v32:v32_dev_password@localhost:5432/v32_sre"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:APP_ENV = "development"
$env:DEBUG = "true"
$env:LOG_LEVEL = "DEBUG"
$env:LOG_FORMAT = "console"
$env:JWT_SECRET_KEY = "dev-secret-key"
$env:DEV_DEFAULT_USER = "dev-user"

# 執行資料庫遷移
alembic upgrade head

# 啟動後端伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8688

# ── 步驟 3：前端設定（新 PowerShell 視窗）────────────────
cd frontend
npm install
npm run dev

# ── 步驟 4：存取服務 ───────────────────────────────────────
Start-Process "http://localhost:3000"
Start-Process "http://localhost:8688/docs"
```

### 5.4 使用 Makefile

`Makefile` 提供 16 個便捷目標，在專案根目錄執行：

```bash
# 顯示所有可用目標
make help

# 完整開發環境設定（Docker + 後端 + 前端）
make setup

# 啟動開發伺服器
make dev

# 執行所有測試
make test

# 僅執行後端測試
make test-backend

# 僅執行前端測試
make test-frontend

# 執行 E2E 測試
make test-e2e

# 執行後端 linter (ruff + mypy)
make lint

# 格式化代碼
make format

# 清理建構產物
make clean

# 執行資料庫遷移
make db-migrate

# 填充測試資料
make db-seed

# 完全重置資料庫
make db-reset

# 查看服務日誌
make logs

# 查看後端日誌
make logs-backend

# 查看前端日誌
make logs-frontend
```

Makefile 目標詳細說明：

| 目標 | 執行動作 |
|------|---------|
| `setup` | `docker compose up -d` + 後端 venv + pip install + npm install |
| `dev` | 啟動 postgres/redis 容器 + 背景執行 uvicorn + 前景執行 vite |
| `test` | 後端 pytest --cov + 前端 vitest + E2E playwright |
| `lint` | 後端 ruff check + mypy + 前端 eslint + tsc --noEmit |
| `format` | 後端 ruff format + 前端 npm run format |
| `clean` | 刪除 `__pycache__`, `.pytest_cache`, `node_modules`, `dist` |
| `db-migrate` | `cd backend && alembic upgrade head` |
| `db-seed` | `cd db/seeds && python generate_test_data.py` |
| `db-reset` | docker compose down -v + up + 遷移 + seed |
| `logs` | `docker compose logs -f` |

---

## 6. 資料庫初始化與遷移

### 6.1 資料庫 Schema 總覽

專案資料庫設計目標承載：**10,000+ 設備**、**100K+ 告警/月**、**10K+ 操作/月**。

| 表格名稱 | 說明 | 分區 | 索引數 | 估計承載 |
|----------|------|------|--------|---------|
| `users` | 使用者帳戶（含 AI Agent 服務帳戶） | 否 | 2 (UNIQUE) | 數百 |
| `platforms` | 平台轉接器設定（vCenter, OpenStack, K8s...） | 否 | 2 | 數十 |
| `assets` | 統一的資產登錄 | 否 | 12 | 10,000+ |
| `asset_relations` | 資產依賴關係 DAG | 否 | 3 | 50,000+ |
| `alerts` | 告警記錄（來自 Prometheus/vCenter 等） | **是 (按月)** | 7 | 100K+/月 |
| `operations` | 操作工單（檢查、變更、事件...） | 否 | 8 | 10K+/月 |
| `operation_steps` | 操作步驟細粒度追蹤 | 否 | 2 | 100K+/月 |
| `audit_logs` | 不可變審計追蹤 | **是 (按月)** | 5 | 50K+/月 |
| `asset_metrics` | 時序指標 (CPU/記憶體/磁碟/網路) | **是 (按月)** | 3 | 1M+/月 |
| `skills` | YAML 自動化技能定義 | 否 | 4 | 數百 |
| `conversations` | AI 對話歷史紀錄 | 否 | 4 | 數十K |

### 6.2 自訂 ENUM 型別

| ENUM 名稱 | 值 |
|-----------|-----|
| `asset_type` | `vm`, `physical_host`, `storage_device`, `network_device`, `container_host`, `cluster`, `datastore`, `load_balancer` |
| `asset_status` | `active`, `maintenance`, `decommissioned`, `unknown`, `provisioning`, `error` |
| `platform_type` | `vmware_vsphere`, `openstack`, `kubernetes`, `physical`, `fusion_sphere`, `storage_array`, `network` |
| `alert_severity` | `critical`, `high`, `medium`, `low`, `info` |
| `alert_status` | `firing`, `acknowledged`, `resolved`, `silenced`, `expired` |
| `operation_type` | `inspection`, `change_request`, `incident`, `maintenance`, `remediation`, `audit` |
| `risk_level` | `critical`, `high`, `medium`, `low`, `none` |
| `operation_status` | `draft`, `pending_approval`, `approved`, `executing`, `completed`, `failed`, `cancelled`, `rolled_back` |
| `step_status` | `pending`, `running`, `completed`, `failed`, `skipped`, `rolled_back` |
| `audit_action` | `create`, `read`, `update`, `delete`, `execute`, `login`, `logout`, `export`, `import`, `approve`, `reject` |
| `user_role` | `admin`, `operator`, `viewer`, `auditor`, `ai_agent` |
| `conversation_status` | `active`, `archived`, `deleted` |
| `skill_status` | `active`, `disabled`, `draft`, `deprecated` |

> **關鍵 Schema ENUM 不一致警告**: 資料庫 `platform_type` 使用 `vmware_vsphere`，但應用程式代碼 (CLAUDE.md 明確定義) 使用 `vsphere`。這可能導致查詢和 API 回應不一致。建議在應用層使用 `vsphere` 並在資料庫層進行映射，或統一為 `vsphere`。

### 6.3 資料庫擴充功能

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- UUID 產生
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- 三元圖索引（LIKE/%text% 搜尋）
CREATE EXTENSION IF NOT EXISTS "btree_gin";        -- GIN 索引（純量欄位）
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- SQL 查詢效能監控
```

### 6.4 分區策略

三個高吞吐量表格使用 PostgreSQL 宣告式分區（按月）：

| 表格 | 分區鍵 | 保留期限 | 說明 |
|------|--------|---------|------|
| `alerts` | `created_at` | 12 個月 | 告警分區；每月一個分區 + default |
| `audit_logs` | `created_at` | 24 個月 | 審計分區；每月一個分區 + default |
| `asset_metrics` | `recorded_at` | 6 個月 | 指標分區；每月一個分區 + default |

目前預先建立的分區：**2026-01 至 2027-06**（共 18 個月）。

#### 分區維護函數

```sql
-- 建立未來 N 個月的分區
SELECT create_monthly_partitions('alerts', 3);
SELECT create_monthly_partitions('audit_logs', 3);
SELECT create_monthly_partitions('asset_metrics', 3);

-- 刪除過期分區
SELECT drop_old_partitions('asset_metrics', 6);   -- 保留 6 個月
SELECT drop_old_partitions('alerts', 12);          -- 保留 1 年
SELECT drop_old_partitions('audit_logs', 24);      -- 保留 2 年
```

建議透過 `pg_cron` 每月自動執行分區維護。

### 6.5 遷移 (Alembic)

#### 重要提醒

> **已知問題**: 專案 `requirements.txt` 包含 `alembic==1.15.2`，且 `db/migrations/001_initial.py` 存在 (667 行完整遷移腳本)，但**專案根目錄中未找到 `alembic.ini` 設定檔**。部署前必須手動初始化 Alembic 或建立對應的 `alembic.ini`。

#### 初始化 Alembic（如尚未設定）

```bash
cd backend

# 初始化 Alembic（若尚無 alembic.ini）
alembic init migrations

# 編輯 alembic.ini，設定資料庫 URL
# sqlalchemy.url = postgresql+asyncpg://v32:v32_dev_password@localhost:5432/v32_sre

# 編輯 migrations/env.py 以支援非同步引擎
```

#### 建議的 `alembic.ini` 設定

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://v32:v32_dev_password@localhost:5432/v32_sre

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### 遷移命令

```bash
# 產生新的遷移腳本
cd backend
alembic revision --autogenerate -m "描述變更"

# 套用所有待處理的遷移
alembic upgrade head

# 回滾最近一次遷移
alembic downgrade -1

# 查看當前版本
alembic current

# 查看遷移歷史
alembic history

# 產生 SQL 腳本（不直接執行）
alembic upgrade head --sql > migration.sql
```

### 6.6 資料庫角色與權限

Schema 中定義了兩個應用程式角色：

| 角色 | 密碼 | 權限 |
|------|------|------|
| `sre_app` | `CHANGE_ME_IN_PRODUCTION` | SELECT, INSERT, UPDATE, DELETE (所有表格) + EXECUTE |
| `sre_readonly` | `CHANGE_ME_IN_PRODUCTION` | SELECT (所有表格) |

> **重要**: 部署前必須修改預設密碼。使用以下命令變更：
> ```sql
> ALTER ROLE sre_app PASSWORD 'new_secure_password';
> ALTER ROLE sre_readonly PASSWORD 'new_secure_password';
> ```

### 6.7 種子資料

```bash
# 產生並匯入測試資料
cd db/seeds
python generate_test_data.py
```

Makefile 中也提供快捷方式：
```bash
make db-seed
```

### 6.8 效能建議設定

推薦的 `postgresql.conf` 參數（假設 16 GB 伺服器）：

```ini
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
random_page_cost = 1.1          # SSD 儲存
effective_io_concurrency = 200  # SSD
wal_buffers = 64MB
max_wal_size = 4GB
checkpoint_completion_target = 0.9
autovacuum_max_workers = 4
autovacuum_naptime = 30s
shared_preload_libraries = 'pg_stat_statements'
```

---

## 7. 設定檔對照表

### 7.1 設定檔位置總覽

| 檔案 | 路徑 | 用途 | 行數 |
|------|------|------|------|
| `.env.example` | 專案根目錄 | 主要環境變數範本 | 31 |
| `backend/.env.example` | backend/ | 後端完整環境變數範本 | 62 |
| `frontend/.env.example` | frontend/ | 前端環境變數範本 | 3 |
| `docker-compose.yml` | 專案根目錄 | 開發環境容器編排 | 85 |
| `backend/Dockerfile` | backend/ | 後端容器映像 | 22 |
| `frontend/Dockerfile` | frontend/ | 前端容器映像 | 16 |
| `backend/pyproject.toml` | backend/ | Python 專案設定 | 58 |
| `frontend/package.json` | frontend/ | Node 專案設定 | 44 |
| `frontend/vite.config.ts` | frontend/ | Vite 建構設定 | 25 |
| `frontend/tsconfig.json` | frontend/ | TypeScript 編譯設定 | 28 |
| `frontend/tailwind.config.js` | frontend/ | Tailwind CSS 設定 | 56 |
| `db/schema.sql` | db/ | 資料庫結構定義 | 819 |
| `db/migrations/001_initial.py` | db/migrations/ | Alembic 初始遷移 | 667 |
| `Makefile` | 專案根目錄 | 開發工作流程 | 64 |
| `scripts/deploy-linux.sh` | scripts/ | Linux 部署腳本 | 282 |
| `scripts/deploy-windows.ps1` | scripts/ | Windows 部署腳本 | 333 |
| `scripts/verify-deployment.sh` | scripts/ | 部署驗證腳本 | 139 |

### 7.2 變數對照矩陣

以下表格對照 `.env.example`（根目錄）、`backend/.env.example`、`docker-compose.yml`（backend 服務）中的變數：

| 變數名稱 | `.env.example` (根) | `backend/.env.example` | `docker-compose.yml` (backend) |
|----------|--------------------|----------------------|------------------------------|
| `APP_NAME` | `Engineer Assist` | `Engineer Assist` | (未定義，使用預設) |
| `APP_VERSION` | `3.2.0` | `3.2.0` | (未定義，使用預設) |
| `APP_ENV` | `development` | `development` | `development` |
| `APP_DEBUG` | `true` | (使用 `DEBUG`) | `true` (使用 `APP_DEBUG`) |
| `DEBUG` | (未定義) | `false` | (未定義) |
| `API_V1_PREFIX` | (未定義) | `/api/v1` | (未定義) |
| `DATABASE_URL` | `postgresql+asyncpg://v32:v32_dev_password@localhost:5432/v32_sre` | `postgresql://postgres:postgres@localhost:5432/engineer_assist` | `postgresql+asyncpg://v32:...@postgres:5432/v32_sre` |
| `DB_ECHO` | (未定義) | `false` | (未定義) |
| `DB_POOL_SIZE` | `20` | `20` | (未定義) |
| `DB_MAX_OVERFLOW` | `10` | `10` | (未定義) |
| `REDIS_URL` | `redis://localhost:6379/0` | `redis://localhost:6379/0` | `redis://redis:6379/0` |
| `JWT_SECRET_KEY` | `dev-secret-key-change-in-production` | (空字串) | `${JWT_SECRET_KEY:-dev-secret-key}` |
| `JWT_ALGORITHM` | `HS256` | `HS256` | (未定義) |
| `JWT_ACCESS_EXPIRE_MINUTES` | `30` | `30` | (未定義) |
| `JWT_REFRESH_EXPIRE_DAYS` | (未定義) | `7` | (未定義) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | `http://localhost:3000,http://localhost:5173` | (未定義) |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `DEBUG` |
| `LOG_FORMAT` | `console` | `json` | (未定義) |
| `RATE_LIMIT_PER_MINUTE` | (未定義) | `60` | (未定義) |
| `ENCRYPTION_KEY` | (未定義) | (空) | (未定義) |
| `DEV_DEFAULT_USER` | `dev-user` | (空) | `dev-user` |
| `KVM_DEFAULT_PORT` | (未定義) | `22` | (未定義) |
| `FUSIONSPHERE_DEFAULT_PORT` | (未定義) | `7443` | (未定義) |

> **注意**: `backend/.env.example` 是**最完整的**環境變數檔案 (62 行)。`.env.example` (根目錄) 是其子集 (31 行)。建議以 `backend/.env.example` 為主要參考來源。

### 7.3 版本號碼不一致總覽

| 位置 | 版本號 | 內容 |
|------|--------|------|
| `README.md` | 3.2.0 | 文件標題 |
| `frontend/package.json` | 3.2.0 | `"version": "3.2.0"` |
| `backend/pyproject.toml` | **3.1.0** | `version = "3.1.0"` |
| `backend/app/config.py` 預設值 | **3.1.0** | `APP_VERSION: str = "3.1.0"` |
| `.env.example` (根) | 3.2.0 | `APP_VERSION=3.2.0` |
| `backend/.env.example` | 3.2.0 | `APP_VERSION=3.2.0` |
| `scripts/deploy-linux.sh` | **3.1.0** | 標頭和 .env 產生 |
| `scripts/deploy-windows.ps1` | **3.1.0** | 標頭和 .env 產生 |
| `scripts/verify-deployment.sh` | **3.1.0** | 標頭 |
| `db/schema.sql` | **V3.1** | SQL 檔案註解 |
| `db/migrations/001_initial.py` | **V3.1** | 遷移腳本註解 |
| `docs/DEPLOYMENT.md` | **V3.1** | 文件標題 |
| `docs/DEPLOYMENT_GUIDE.md` | **3.1.0** | 文件標題 |
| 部署腳本產生 .env | **3.1.0 / v31 資料庫** | `APP_VERSION=3.1.0`, `DATABASE_URL=...v31...` |

> **影響**: 部署腳本 (`deploy-linux.sh`, `deploy-windows.ps1`) 產生的 `.env` 仍使用 `APP_VERSION=3.1.0` 及資料庫前綴 `v31`。**手動部署時必須修改為 `3.2.0` 和 `v32`**，或直接使用專案中的 `.env.example` 作為基礎。

---

## 8. 安全性設定要點

### 8.1 JWT 密鑰管理

```bash
# 產生安全的 HS256 密鑰（256-bit = 32 bytes hex = 64 chars）
openssl rand -hex 64

# 範例輸出: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4

# 設定為環境變數
export JWT_SECRET_KEY="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4"
```

> **安全注意事項**:
> - 開發環境中，若 `JWT_SECRET_KEY` 為空且 `APP_ENV != production`，系統會自動產生隨機密鑰（`secrets.token_hex(32)`），並輸出警告日誌。
> - 生產環境中，`JWT_SECRET_KEY` **必須**被設定，否則應用程式將拋出 `ValueError` 並無法啟動。
> - JWT Token 簽章後包含 `iat`（簽發時間）、`exp`（過期時間）、`type`（access/refresh）等聲明。

### 8.2 Fernet 加密密鑰

用於加密儲存在資料庫中的平台認證資訊（vCenter 密碼等）。

```bash
# 產生 Fernet 密鑰
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 設定為環境變數
export ENCRYPTION_KEY="產生的密鑰"
```

> 對應 `backend/app/config.py` 中的 `ENCRYPTION_KEY`，`backend/.env.example` 第 33 行已預留。

### 8.3 密碼雜湊

| 元件 | 演算法 | 函式庫 |
|------|--------|--------|
| 使用者密碼 | bcrypt (自動 rounds) | passlib[bcrypt] + bcrypt 4.3.0 |
| JWT 簽章 | HMAC-SHA256 | python-jose[cryptography] 3.4.0 |
| 平台密碼儲存 | Fernet (對稱加密) | cryptography (Fernet) |

### 8.4 CORS 設定

```python
# backend/app/config.py 中的解析邏輯
CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

@property
def cors_origin_list(self) -> list[str]:
    return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
```

**生產環境建議設定**:
```bash
# 單一網域
CORS_ORIGINS=https://sre.example.com

# 多網域（含內部測試）
CORS_ORIGINS=https://sre.example.com,https://sre-staging.example.com
```

### 8.5 Dockerfile 安全性強化

當前 Dockerfile 的安全性缺失及對策：

| 缺失 | 風險 | 建議方案 |
|------|------|---------|
| 以 root 執行 | 容器逃逸風險 | 加入 `RUN groupadd -r sre && useradd -r -g sre sre` 及 `USER sre` |
| 無 HEALTHCHECK | 無法自動偵測故障 | 加入 `HEALTHCHECK` 指令 |
| 無 `.dockerignore` | 可能洩漏 .env、.git 等敏感檔案 | 建立 `.dockerignore` 排除不必要檔案 |
| 未固定基礎映像版本 | 不可重複建構 | 使用 `FROM python:3.12-slim@sha256:...` |

建議的 `.dockerignore` 內容：

```
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.mypy_cache/
.pytest_cache/
.ruff_cache/

# Node
node_modules/
dist/

# Environment
.env
.env.*
!.env.example

# Git
.git/
.gitignore

# IDE
.idea/
.vscode/

# Test
coverage/
test-results/

# Docs
docs/
*.md
!README.md

# CI/CD
.github/
```

### 8.6 資料庫安全

- 生產環境中使用 Docker Secrets 管理密碼（非環境變數）
- 應用程式角色 `sre_app` 以最小權限原則授予（CRUD 所有表格）
- 唯讀角色 `sre_readonly` 僅供儀表板和報表使用
- 審計日誌 (`audit_logs`) 為不可變設計（應用層不提供 UPDATE/DELETE）
- Row-Level Security (RLS) 支援多租戶部署（Schema 中已預留，未啟用）

### 8.7 速率限制

```python
# backend/app/config.py
RATE_LIMIT_PER_MINUTE: int = 60  # 每個客戶端每分鐘最大 API 請求數
```

### 8.8 網路安全清單

| 檢查項目 | 開發 | 生產 |
|----------|------|------|
| PostgreSQL 僅綁定 localhost | 否 (0.0.0.0:5432) | **必須** (127.0.0.1:5432) |
| Redis 密碼認證 | 否 | **必須** (`requirepass`) |
| HTTPS/TLS 終止 | 否 | **必須** |
| API 速率限制 | 60/min | 依容量調整 |
| CORS 限制 | localhost only | **必須** (指定網域) |
| 非 root 容器 | 否 | **必須** |
| Docker Secrets | 否 | **必須** |
| 審計日誌 | 啟用 | 啟用 |
| Fernet 平台密碼加密 | 建議 | **必須** |

---

## 9. 監控與健康檢查

### 9.1 健康檢查端點

所有端點由 `backend/app/api/v1/health.py` 提供，註冊於根層級（不含 `/api` 前綴）：

| 端點 | 方法 | 說明 | 成功回應 | Kubernetes 用途 |
|------|------|------|---------|----------------|
| `/health` | GET | 活躍探測 (Liveness) | `200 {"status":"healthy","version":"3.1.0"}` | 決定是否重啟容器 |
| `/ready` | GET | 就緒探測 (Readiness) | `200` 或 `503` | 決定是否路由流量 |
| `/health/db` | GET | 資料庫連線檢查 | `200` 或 `503` | 獨立檢查 |
| `/health/redis` | GET | Redis 連線檢查 | `200` 或 `503` | 獨立檢查 |

#### `/ready` 回應範例

```json
// 所有依賴正常 (HTTP 200)
{
  "status": "ready",
  "version": "3.2.0",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.34
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 0.87,
      "pong": true
    }
  }
}

// 部分依賴異常 (HTTP 503)
{
  "status": "degraded",
  "version": "3.2.0",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.12
    },
    "redis": {
      "status": "unhealthy",
      "latency_ms": 5001.45,
      "error": "Connection timeout"
    }
  }
}
```

### 9.2 Docker Compose 健康檢查

| 服務 | 檢查命令 | 間隔 | 逾時 | 重試次數 |
|------|---------|------|------|---------|
| PostgreSQL | `pg_isready -U v32 -d v32_sre` | 10s | 5s | 5 |
| Redis | `redis-cli ping` | 10s | 5s | 5 |
| Backend | **未設定** | N/A | N/A | N/A |
| Frontend | **未設定** | N/A | N/A | N/A |

> **問題**: Backend 和 Frontend 的 Dockerfile 及 docker-compose.yml 中均未設定健康檢查。對於生產環境，建議在 Dockerfile 中加入 `HEALTHCHECK` 指令。

### 9.3 日誌設定

後端使用 **structlog** 進行結構化日誌處理：

| 環境 | LOG_FORMAT | 輸出格式 | LOG_LEVEL |
|------|-----------|---------|-----------|
| 開發 | `console` | 人類可讀（彩色） | `DEBUG` |
| 測試 | `json` | 結構化 JSON | `INFO` |
| 生產 | `json` | 結構化 JSON | `INFO` |

**structlog 處理器管線**:

```python
processors = [
    structlog.contextvars.merge_contextvars,    # 合併上下文變數
    structlog.stdlib.add_log_level,             # 加入日誌級別
    structlog.stdlib.add_logger_name,           # 加入 logger 名稱
    structlog.processors.TimeStamper(fmt="iso"), # ISO 8601 時間戳
    structlog.processors.StackInfoRenderer(),    # 堆疊資訊
    structlog.processors.format_exc_info,        # 例外資訊格式化
    # 根據 LOG_FORMAT 選用：
    # structlog.processors.JSONRenderer()        # JSON 輸出
    # structlog.dev.ConsoleRenderer()            # 人類可讀輸出
]
```

### 9.4 日誌查看命令

```bash
# Docker Compose 日誌
docker compose logs -f                    # 所有服務
docker compose logs -f backend            # 僅後端
docker compose logs -f frontend           # 僅前端
docker compose logs --tail=100 backend    # 最近 100 行
docker compose logs backend | grep ERROR  # 錯誤日誌

# 本機開發日誌（後端）
# uvicorn 會將日誌輸出到 stdout；structlog 處理 JSON/console 格式

# Systemd 日誌（生產）
journalctl -u sre-backend -f              # 跟隨
journalctl -u sre-backend --since "1 hour ago"  # 最近一小時
```

### 9.5 驗證腳本

```bash
# 使用自動化驗證腳本
./scripts/verify-deployment.sh http://localhost:8688 http://localhost:3000

# 預期輸出範例:
# ==========================================
#  V3.1 SRE Platform — Deployment Verification
# ==========================================
#
# Health Checks:
#   Backend health... PASS (HTTP 200)
#   Backend ready... PASS (HTTP 200)
#   Backend liveness... PASS (HTTP 200)
#
# API Endpoints:
#   GET /api/v1/assets... PASS (HTTP 200)
#   GET /api/v1/alerts... PASS (HTTP 200)
#   GET /api/v1/operations... PASS (HTTP 200)
#   ...
#
#  Results: 18 passed, 0 failed, 0 warnings
```

---

## 10. 備份與災難恢復

### 10.1 資料庫備份

#### Docker 環境

```bash
# 建立備份
docker compose exec postgres pg_dump -U v32 -d v32_sre \
    -F c \                               # 自訂格式（可壓縮）
    -f /tmp/backup_$(date +%Y%m%d_%H%M%S).dump

# 從容器複製到主機
docker cp v32-postgres:/tmp/backup_20260601_120000.dump ./backup/

# 從主機複製到容器並恢復
docker cp ./backup/backup_20260601_120000.dump v32-postgres:/tmp/
docker compose exec postgres pg_restore -U v32 -d v32_sre \
    -c \                                 # 清除已存在的物件
    /tmp/backup_20260601_120000.dump
```

#### 本機 PostgreSQL

```bash
# 備份
pg_dump -U v32 -d v32_sre -F c -f backup_$(date +%Y%m%d).dump

# 恢復
pg_restore -U v32 -d v32_sre -c backup_20260601.dump
```

### 10.2 自動化備份腳本

```bash
#!/bin/bash
# /opt/sre-platform/scripts/backup-db.sh
# 建議透過 crontab 每日執行

BACKUP_DIR="/opt/sre-platform/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Docker 環境備份
docker compose -f /opt/sre-platform/docker-compose.prod.yml \
    exec -T postgres pg_dump -U sre_app -d v32_sre -F c \
    > "$BACKUP_DIR/backup_$TIMESTAMP.dump"

# 壓縮
gzip "$BACKUP_DIR/backup_$TIMESTAMP.dump"

# 清除過期備份
find "$BACKUP_DIR" -name "backup_*.dump.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: backup_$TIMESTAMP.dump.gz"
```

**Crontab 設定**:
```cron
# 每日凌晨 2:00 執行備份
0 2 * * * /opt/sre-platform/scripts/backup-db.sh >> /var/log/sre-backup.log 2>&1
```

### 10.3 Redis 持久化

```bash
# Redis 已啟用 AOF (Append Only File)
# docker-compose.prod.yml 中包含: command: redis-server --appendonly yes
# 資料持久化於 redis_prod_data 卷

# 手動觸發 Redis 快照
docker compose exec redis redis-cli BGSAVE
```

### 10.4 設定檔備份

```bash
# 備份關鍵設定
cp .env .env.backup.$(date +%Y%m%d)
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d)
cp -r secrets/ secrets.backup.$(date +%Y%m%d)/
```

### 10.5 災難恢復流程

```
┌─────────────────────────────────────────────────────────┐
│                  災難恢復檢查清單                          │
├─────────────────────────────────────────────────────────┤
│ □ 1. 確認備份檔案完整性 (pg_restore --list)               │
│ □ 2. 建立全新 PostgreSQL 16 執行個體                       │
│ □ 3. 執行 schema.sql 初始化或 alembic upgrade head        │
│ □ 4. 使用 pg_restore 恢復資料                             │
│ □ 5. 設定資料庫角色和密碼                                  │
│ □ 6. 重新產生 JWT 和 Fernet 密鑰                          │
│ □ 7. 設定 .env 生產環境變數                                │
│ □ 8. 部署應用程式容器                                      │
│ □ 9. 執行健康檢查驗證                                      │
│ □ 10. 切換 DNS / 負載平衡器指向新執行個體                   │
└─────────────────────────────────────────────────────────┘
```

#### 災難恢復命令序列

```bash
# 1. 驗證備份
pg_restore --list backup_20260601.dump | head -20

# 2. 初始化新資料庫
docker compose -f docker-compose.prod.yml up -d postgres
sleep 10

# 3. 恢復資料
docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_restore -U sre_app -d v32_sre -c < backup_20260601.dump

# 4. 執行遷移（確保 Schema 最新）
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. 重新啟動應用程式
docker compose -f docker-compose.prod.yml up -d

# 6. 驗證
curl http://localhost:8688/ready
```

---

## 11. 常見問題排查

### 11.1 服務啟動問題

| 問題 | 症狀 | 可能原因 | 解決方案 |
|------|------|---------|---------|
| 後端無法啟動 | `connection refused` | PostgreSQL 未就緒 | `docker compose ps` 確認 postgres 狀態；等待健康檢查通過 |
| 前端白屏 | 瀏覽器空白頁 | API 代理設定錯誤 | 檢查 `vite.config.ts` 的 proxy 設定 |
| 埠號衝突 | `port is already allocated` | 其他程式佔用埠號 | `netstat -ano \| findstr :8688` (Win) / `lsof -i :8688` (Linux) |
| 資料庫驗證失敗 | `password authentication failed` | 密碼不匹配 | 檢查 .env 與 docker-compose.yml 密碼一致性 |
| JWT 驗證失敗 | `401 Unauthorized` | 密鑰變更或 Token 過期 | 檢查 JWT_SECRET_KEY 或重新登入 |
| 容器無法連線 | `Could not resolve host` | Docker 網路問題 | 確認服務名稱正確（docker compose 內使用服務名） |

### 11.2 資料庫問題

```bash
# 檢查 PostgreSQL 狀態
docker compose ps postgres
# 期望: Up (healthy)

# 測試資料庫連線
docker compose exec postgres psql -U v32 -d v32_sre -c "SELECT 1"
# 期望: ?column? = 1

# 查看資料庫日誌
docker compose logs postgres | grep -i error

# 檢查連線數
docker compose exec postgres psql -U v32 -d v32_sre \
    -c "SELECT count(*) FROM pg_stat_activity;"

# 檢查表格是否存在
docker compose exec postgres psql -U v32 -d v32_sre \
    -c "\dt"

# 手動連線測試
docker compose exec backend python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    engine = create_async_engine('postgresql+asyncpg://v32:v32_dev_password@postgres:5432/v32_sre')
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Database OK:', result.scalar())
    await engine.dispose()
asyncio.run(test())
"
```

### 11.3 前端開發問題

```bash
# 清除 node_modules 並重新安裝
cd frontend
rm -rf node_modules package-lock.json
npm install

# 型別檢查
npx tsc --noEmit

# 檢查 Vite 代理是否正常
curl http://localhost:3000/api/v1/health
# 應回傳: {"status":"healthy","version":"3.1.0"}

# 清除 Vite 快取
rm -rf node_modules/.vite
npm run dev
```

### 11.4 後端開發問題

```bash
# 清除 Python 快取
cd backend
find . -type d -name __pycache__ -exec rm -rf {} +

# 重新安裝依賴
pip install -r requirements.txt --force-reinstall

# 驗證匯入
python -c "from app.main import app; print('Import OK')"

# 執行 lint
ruff check app/
mypy app/

# 執行測試
pytest tests/ -v
```

### 11.5 Docker 問題

```bash
# 完全清理 Docker 資源
docker compose down -v          # 停止並移除卷
docker system prune -a --volumes -f  # 清理未使用資源

# 查看容器資源使用
docker stats

# 重建特定服務（無快取）
docker compose build --no-cache backend
docker compose up -d backend

# 檢查 Docker 磁碟使用
docker system df
```

### 11.6 Alembic 遷移問題

```bash
# 檢查當前遷移狀態
cd backend
alembic current

# 查看未套用的遷移
alembic history --indicate-current

# 創建新的遷移
alembic revision --autogenerate -m "描述變更"

# 手動標記版本（跳過特定遷移）
alembic stamp head

# 回滾到特定版本
alembic downgrade <revision_id>
```

### 11.7 部署腳本問題

> **已知問題**: `deploy-linux.sh` 和 `deploy-windows.ps1` 參考 `docker-compose.prod.yml`，但專案中似乎不存在此檔案。部署腳本內部使用 `v31` 前綴（`v31_sre`、`v31_dev_password`），而非本專案的 `v32` 前綴。

```bash
# 若部署腳本失敗，手動執行以下步驟：
# 1. 確保使用正確的 .env
cp backend/.env.example .env

# 2. 編輯 .env 以符合本機設定
# DATABASE_URL=postgresql+asyncpg://v32:v32_dev_password@localhost:5432/v32_sre

# 3. 手動啟動
docker compose up -d postgres redis
docker compose up -d backend frontend
```

---

## 12. 已知問題與風險

### 12.1 關鍵問題摘要

| # | 問題 | 分類 | 嚴重程度 | 建議處理 |
|---|------|------|---------|---------|
| 1 | **版本不一致**: README v3.2, pyproject.toml v3.1.0, DB 參考 v31 | 設定 | **高** | 統一為 v3.2.0 |
| 2 | **埠號不一致**: vite.config 使用 3000，Docker 使用 5173 | 設定 | **高** | 統一或文件化差異 |
| 3 | **前端 Dockerfile 僅開發伺服器**: 無 `npm run build` 多階段建構 | 部署 | **高** | 加入生產建構階段 |
| 4 | **Python 版本混淆**: README 宣稱 3.14.5，實際使用 3.12 | 文件 | **高** | 修正 README 或升級基礎映像 |
| 5 | **無 alembic.ini**: requirements 包含 alembic，但專案未初始化 | 部署 | **高** | 建立 alembic.ini 設定檔 |
| 6 | **缺少平台 SDK**: pyvmomi、libvirt-python 未在 requirements.txt | 相依性 | **中** | 加入對應套件 |
| 7 | **無 ESLint**: package.json lint 腳本參考 eslint 但未安裝 | 相依性 | **中** | 安裝 eslint 或修改 lint 腳本 |
| 8 | **Schema ENUM 不一致**: DB `vmware_vsphere` vs 應用 `vsphere` | 相容性 | **中** | 統一命名或加入映射層 |
| 9 | **Dockerfile 以 root 執行**: 兩者均無 `USER` 指令 | 安全 | **中** | 加入非 root 使用者 |
| 10 | **無 Dockerfile HEALTHCHECK**: 後端和前端均缺少 | 維運 | **中** | 加入 HEALTHCHECK 指令 |
| 11 | **部署腳本使用 v31 前綴**: deploy-linux.sh/ps1 參考 v31_sre 而非 v32_sre | 部署 | **高** | 更新部署腳本 |
| 12 | **缺少 docker-compose.prod.yml**: 部署腳本參考但檔案不存在 | 部署 | **高** | 建立生產用 compose 檔案 |
| 13 | **config.py 預設 APP_VERSION 為 3.1.0**: pydantic-settings 預設值過期 | 設定 | **低** | 更新為 3.2.0 |

### 12.2 版本不一致修復指引

```bash
# 1. 更新 backend/pyproject.toml
# 將 version = "3.1.0" 改為 version = "3.2.0"

# 2. 更新 backend/app/config.py
# 將 APP_VERSION: str = "3.1.0" 改為 APP_VERSION: str = "3.2.0"

# 3. 更新部署腳本中產生的 .env
# 將 APP_VERSION=3.1.0 改為 APP_VERSION=3.2.0
# 將 v31_sre 改為 v32_sre
# 將 v31_dev_password 改為 v32_dev_password
```

### 12.3 相依性缺失修復

```bash
# 安裝缺失的前端 ESLint 依賴
cd frontend
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# 加入平台 SDK (後端)
cd backend
pip install pyvmomi libvirt-python
# 並將它們加入 requirements.txt
```

---

## 13. 附錄：完整目錄結構

```
v3.2/
├── .env.example                          # 根層級環境變數範本 (31 行)
├── .gitignore                            # Git 忽略規則 (53 行)
├── CLAUDE.md                             # Claude Code 專案指引
├── LICENSE                               # MIT 授權
├── Makefile                              # 開發工作流程 (16 目標)
├── README.md                             # 專案說明
├── docker-compose.yml                    # 開發環境容器編排 (85 行)
│
├── backend/                              # Python FastAPI 後端
│   ├── Dockerfile                        # 容器映像 (python:3.12-slim)
│   ├── .env.example                      # 後端環境變數範本 (62 行)
│   ├── requirements.txt                  # Python 依賴 (16 個固定版本)
│   ├── pyproject.toml                    # Python 專案設定 (hatchling)
│   └── app/
│       ├── __init__.py
│       ├── main.py                       # FastAPI 應用工廠 (127 行)
│       ├── config.py                     # pydantic-settings 設定 (194 行)
│       ├── exceptions.py                 # 自訂例外類別
│       ├── api/
│       │   ├── router.py                 # 主要 API 路由器
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── alerts.py             # 告警 API
│       │       ├── assets.py             # 資產 API
│       │       ├── atomics.py            # 原子操作 API
│       │       ├── chat.py               # AI 聊天 API
│       │       ├── dashboard.py          # 儀表板 API
│       │       ├── health.py             # 健康檢查端點
│       │       ├── migration.py          # 遷移管理 API
│       │       ├── operations.py         # 操作 API
│       │       └── platforms.py          # 平台 API
│       ├── core/
│       │   ├── __init__.py
│       │   ├── database.py               # SQLAlchemy 非同步引擎
│       │   ├── security.py               # JWT + 密碼雜湊 (91 行)
│       │   └── registry.py               # 操作登錄
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── audit.py                  # 審計中介層
│       │   ├── error_handler.py          # 錯誤處理中介層
│       │   └── request_id.py             # 請求 ID 中介層
│       ├── models/
│       │   ├── __init__.py
│       │   ├── alert.py                  # 告警 ORM
│       │   ├── asset.py                  # (可能合併於其他檔案)
│       │   ├── audit_log.py              # 審計日誌 ORM
│       │   ├── base.py                   # 基礎 ORM
│       │   ├── conversation.py           # 對話 ORM
│       │   └── operation.py              # 操作 ORM
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── alert_repo.py
│       │   ├── base.py
│       │   └── operation_repo.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── alert.py                  # Pydantic 告警 Schema
│       │   ├── asset.py                  # Pydantic 資產 Schema
│       │   ├── chat.py                   # Pydantic 聊天 Schema
│       │   ├── dashboard.py              # Pydantic 儀表板 Schema
│       │   └── operation.py              # Pydantic 操作 Schema
│       ├── services/
│       │   ├── __init__.py
│       │   ├── alert_service.py
│       │   ├── chat_service.py
│       │   └── operation_service.py
│       ├── platforms/
│       │   ├── __init__.py
│       │   ├── kvm/                      # KVM/QEMU 轉接器
│       │   │   └── __init__.py
│       │   ├── vsphere/                  # VMware vSphere 轉接器
│       │   │   └── __init__.py
│       │   └── fusionsphere/             # Huawei FusionSphere 轉接器
│       │       └── __init__.py
│       └── migration/                    # VM 遷移引擎
│           └── __init__.py
│
├── frontend/                             # React TypeScript 前端
│   ├── Dockerfile                        # 容器映像 (node:20-alpine, 開發)
│   ├── .env.example                      # 前端環境變數 (3 行)
│   ├── package.json                      # Node 專案設定 (44 行)
│   ├── vite.config.ts                    # Vite 建構設定
│   ├── tsconfig.json                     # TypeScript 設定 (strict)
│   ├── tsconfig.node.json                # Node 端 TypeScript 設定
│   ├── tailwind.config.js                # Tailwind CSS 暗色主題設定
│   ├── postcss.config.js                 # PostCSS 設定
│   ├── index.html                        # HTML 入口
│   └── src/
│       ├── app/
│       │   ├── App.tsx                   # 應用程式根組件
│       │   ├── router.tsx                # React Router 路由
│       │   └── providers.tsx             # Context Providers
│       ├── api/
│       │   └── index.ts                  # HTTP 客戶端 (基於 /api/v1)
│       ├── components/
│       │   ├── alerts/
│       │   │   ├── AlertCard.tsx
│       │   │   └── AlertFilters.tsx
│       │   ├── chat/
│       │   │   ├── ConfirmDialog.tsx
│       │   │   ├── MessageBubble.tsx
│       │   │   ├── QuickActions.tsx
│       │   │   └── StepProgress.tsx
│       │   ├── dashboard/
│       │   │   ├── AlertDistribution.tsx
│       │   │   ├── AlertSummary.tsx
│       │   │   ├── RecentOperations.tsx
│       │   │   ├── ResourceUsage.tsx
│       │   │   ├── StatCards.tsx
│       │   │   └── TrendChart.tsx
│       │   ├── layout/
│       │   │   ├── AppLayout.tsx
│       │   │   ├── Header.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── StatusBar.tsx
│       │   ├── operations/
│       │   │   ├── OperationCard.tsx
│       │   │   └── OperationDetail.tsx
│       │   ├── resources/
│       │   │   ├── AssetTable.tsx
│       │   │   ├── BatchActions.tsx
│       │   │   └── DetailPanel.tsx
│       │   └── ui/
│       │       ├── Badge.tsx
│       │       ├── Button.tsx
│       │       ├── Card.tsx
│       │       ├── CommandPalette.tsx
│       │       ├── EmptyState.tsx
│       │       ├── ErrorBoundary.tsx
│       │       ├── FilterBar.tsx
│       │       ├── LoadingSpinner.tsx
│       │       ├── Modal.tsx
│       │       ├── Skeleton.tsx
│       │       ├── StatusDot.tsx
│       │       ├── Tabs.tsx
│       │       ├── Toast.tsx
│       │       └── index.ts
│       ├── hooks/
│       │   └── useAlerts.ts
│       ├── stores/                       # Zustand 狀態管理
│       ├── types/                        # TypeScript 型別定義
│       ├── lib/                          # 工具函式
│       ├── utils/                        # 向後相容 re-export
│       └── __tests__/                    # 前端單元測試 (Vitest)
│
├── db/                                   # 資料庫
│   ├── schema.sql                        # 完整 SQL Schema (819 行)
│   ├── migrations/
│   │   └── 001_initial.py               # Alembic 初始遷移 (667 行)
│   └── seeds/
│       └── generate_test_data.py         # 測試資料產生器
│
├── docs/                                 # 文件
│   ├── DEPLOYMENT.md                     # 部署簡要說明
│   ├── DEPLOYMENT_GUIDE.md               # 部署指南 (464 行)
│   ├── TEST_ENVIRONMENT_SETUP.md         # 測試環境設定
│   ├── V3.1_DEVELOPMENT_PLAN.md          # 開發計畫
│   ├── PLATFORM_SDK_RESEARCH.md          # SDK 研究
│   ├── PLATFORM_INTEGRATION_PLAN.md      # 平台整合方案
│   └── ARCHITECTURE_CRITIQUE.html        # 架構審查
│
├── scripts/                              # 部署與維運腳本
│   ├── deploy-linux.sh                  # Linux 部署 (282 行)
│   ├── deploy-windows.ps1               # Windows 部署 (333 行)
│   └── verify-deployment.sh             # 部署驗證 (139 行)
│
├── tests/                                # E2E 測試
│   └── e2e/                              # Playwright 測試
│
├── DSreport/                             # 部署設定報告
│   └── DEPLOYMENT_CONFIGURATION_GUIDE.md # 本文件
│
└── secrets/                              # 生產密鑰 (git ignored)
    ├── db_password.txt
    ├── jwt_secret.txt
    └── fernet_key.txt
```

---

## 附錄 A：快速參考卡片

### 預設連線資訊

| 服務 | 位址 | 認證 |
|------|------|------|
| 後端 API | `http://localhost:8688` | JWT Bearer Token |
| API 文件 | `http://localhost:8688/docs` | 無 |
| API 替代文件 | `http://localhost:8688/redoc` | 無 |
| 前端 (Vite) | `http://localhost:3000` | JWT Bearer Token |
| 前端 (Docker) | `http://localhost:5173` | JWT Bearer Token |
| PostgreSQL | `localhost:5432` | `v32` / `v32_dev_password` |
| Redis | `localhost:6379` | 無（開發） |

### 常用命令速查

```bash
# 開發環境一鍵啟動
docker compose up -d

# 執行所有測試
make test

# 執行後端 lint
cd backend && ruff check app/ && mypy app/

# 執行前端型別檢查
cd frontend && npx tsc --noEmit

# 資料庫遷移
cd backend && alembic upgrade head

# 備份資料庫
docker compose exec postgres pg_dump -U v32 -d v32_sre -F c -f /tmp/backup.dump

# 查看日誌
docker compose logs -f backend

# 完全重置
docker compose down -v && docker compose up -d
```

### API 端點一覽

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 活躍探測 |
| GET | `/ready` | 就緒探測 |
| GET | `/health/db` | 資料庫健康檢查 |
| GET | `/health/redis` | Redis 健康檢查 |
| GET | `/api/v1/assets` | 資產列表 |
| GET | `/api/v1/alerts` | 告警列表 |
| GET | `/api/v1/operations` | 操作列表 |
| POST | `/api/v1/chat` | AI 聊天 |
| GET | `/api/v1/dashboard/summary` | 儀表板摘要 |
| GET | `/api/v1/dashboard/trends` | 趨勢資料 |
| GET | `/api/v1/atomics` | 原子操作列表 |
| GET | `/api/v1/platforms` | 平台列表 |
| POST | `/api/v1/platforms` | 新增平台 |
| POST | `/api/v1/platforms/{id}/test` | 測試平台連線 |
| POST | `/api/v1/platforms/{id}/sync` | 同步平台設備 |
| POST | `/api/v1/migration/plan` | 產生遷移計畫 |
| POST | `/api/v1/migration/execute` | 執行遷移 |
| GET | `/api/v1/migration/{id}` | 查詢遷移狀態 |

### 依賴版本摘要

| 類別 | 套件 | 版本 |
|------|------|------|
| **後端核心** | | |
| Web 框架 | fastapi | 0.115.12 |
| ASGI 伺服器 | uvicorn[standard] | 0.34.3 |
| ORM | sqlalchemy[asyncio] | 2.0.41 |
| 非同步 PostgreSQL | asyncpg | 0.30.0 |
| 資料驗證 | pydantic | 2.11.3 |
| 設定管理 | pydantic-settings | 2.9.1 |
| **認證** | | |
| JWT | python-jose[cryptography] | 3.4.0 |
| 密碼雜湊 | passlib[bcrypt] | 1.7.4 |
| 密碼雜湊 | bcrypt | 4.3.0 |
| **資料** | | |
| Redis 客戶端 | redis | 5.3.0 |
| HTTP 客戶端 | httpx | 0.28.1 |
| **日誌** | | |
| 結構化日誌 | structlog | 25.4.0 |
| **遷移** | | |
| 資料庫遷移 | alembic | 1.15.2 |
| **前端核心** | | |
| UI 框架 | react | 18.3.1 |
| 型別系統 | typescript | 5.6.3 |
| 建構工具 | vite | 6.0.0 |
| 狀態管理 | zustand | 5.0.0 |
| 資料獲取 | @tanstack/react-query | 5.60.0 |
| 路由 | react-router-dom | 6.28.0 |
| CSS 框架 | tailwindcss | 3.4.15 |
| 圖表 | recharts | 2.13.0 |
| 圖示 | lucide-react | 0.460.0 |

---

> **本文件由 Qoder 依據 Inspection V3.2 代碼庫實際分析產生**  
> 分析範圍包含：docker-compose.yml、Dockerfile、.env.example、requirements.txt、package.json、pyproject.toml、vite.config.ts、database schema、migrations、deployment scripts、Makefile、source code (config.py, main.py, security.py, health.py)  
> 最後更新：2026-06-01
