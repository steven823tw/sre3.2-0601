# V3.2 SRE Platform — 部署指南

> **版本**: 3.2.0 | **更新**: 2026-05-31

---

## 目录

1. [环境要求](#1-环境要求)
2. [快速部署](#2-快速部署)
3. [Windows 部署](#3-windows-部署)
4. [Linux 部署](#4-linux-部署)
5. [生产部署](#5-生产部署)
6. [配置说明](#6-配置说明)
7. [验证部署](#7-验证部署)
8. [故障排查](#8-故障排查)

---

## 1. 环境要求

### 1.1 硬件要求

| 环境 | CPU | 内存 | 磁盘 | 网络 |
|------|-----|------|------|------|
| 开发 | 2 核 | 4 GB | 20 GB SSD | 任意 |
| 测试 | 4 核 | 8 GB | 50 GB SSD | 内网 |
| 生产 | 8 核 | 16 GB | 200 GB SSD | 千兆网络 |

### 1.2 软件要求

**必须安装**:
- Docker 24+ & Docker Compose 2.20+
- Git 2.30+

**可选安装** (本地开发):
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (如不用 Docker)

### 1.3 端口要求

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | React 开发服务器 |
| Backend | 8688 | FastAPI API 服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存/队列 |

---

## 2. 快速部署

### 2.1 一键部署 (推荐)

```bash
# 1. 克隆项目
git clone <repository-url> v3.2
cd v3.2

# 2. 运行部署脚本
# Linux/Mac:
./scripts/deploy-linux.sh dev

# Windows PowerShell:
.\scripts\deploy-windows.ps1 -Env dev

# 3. 访问
# Frontend: http://localhost:3000
# Backend: http://localhost:8688
# API Docs: http://localhost:8688/docs
```

### 2.2 手动部署

```bash
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 等待服务就绪
sleep 10

# 3. 验证服务
docker compose ps

# 4. 访问应用
# Frontend: http://localhost:3000
# Backend: http://localhost:8688
```

---

## 3. Windows 部署

### 3.1 使用 PowerShell 脚本

```powershell
# 开发环境
.\scripts\deploy-windows.ps1 -Env dev

# 生产环境
.\scripts\deploy-windows.ps1 -Env prod

# 本地部署 (不用 Docker)
.\scripts\deploy-windows.ps1 -Local

# 查看帮助
.\scripts\deploy-windows.ps1 -Help
```

### 3.2 手动部署 (Windows)

```powershell
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 等待服务就绪
Start-Sleep -Seconds 10

# 3. 验证服务
docker compose ps

# 4. 访问应用
Start-Process "http://localhost:3000"
```

### 3.3 本地开发 (Windows)

```powershell
# 1. 启动数据库
docker compose up -d postgres redis

# 2. 后端
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8688

# 3. 前端 (新终端)
cd frontend
npm install
npm run dev
```

---

## 4. Linux 部署

### 4.1 使用 Bash 脚本

```bash
# 开发环境
./scripts/deploy-linux.sh dev

# 生产环境
./scripts/deploy-linux.sh prod

# 本地部署
./scripts/deploy-linux.sh local
```

### 4.2 手动部署 (Linux)

```bash
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 等待服务就绪
sleep 10

# 3. 验证服务
docker compose ps

# 4. 访问应用
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8688"
```

### 4.3 Systemd 服务 (生产)

```bash
# /etc/systemd/system/sre-backend.service
[Unit]
Description=SRE Platform Backend
After=network.target postgres.service redis.service

[Service]
Type=simple
User=sre
WorkingDirectory=/opt/v3.2/backend
ExecStart=/opt/v3.2/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8688
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 5. 生产部署

### 5.1 前置准备

```bash
# 1. 生成密钥
mkdir -p secrets
openssl rand -hex 64 > secrets/jwt_secret.txt
openssl rand -base64 32 > secrets/db_password.txt
chmod 600 secrets/*.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置生产配置

# 3. 准备 SSL 证书
mkdir -p ssl
# 复制证书文件到 ssl/ 目录
```

### 5.2 Docker Compose 生产部署

```bash
# 1. 构建镜像
docker compose -f docker-compose.prod.yml build

# 2. 启动服务
docker compose -f docker-compose.prod.yml up -d

# 3. 运行迁移
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. 验证
curl -k https://sre.example.com/health
```

### 5.3 Kubernetes 部署

```bash
# 1. 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 2. 创建配置
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. 部署服务
kubectl apply -f k8s/deployment-backend.yaml
kubectl apply -f k8s/service-backend.yaml
kubectl apply -f k8s/deployment-frontend.yaml
kubectl apply -f k8s/service-frontend.yaml

# 4. 部署 Ingress
kubectl apply -f k8s/ingress.yaml

# 5. 验证
kubectl get pods -n sre-platform
```

---

## 6. 配置说明

### 6.1 环境变量

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `APP_NAME` | 应用名称 | Engineer Assist | 否 |
| `APP_VERSION` | 版本**: 3.2.0 | 否 |
| `APP_ENV` | 环境 | development | 否 |
| `DEBUG` | 调试模式 | false | 否 |
| `DATABASE_URL` | 数据库连接 | (空=SQLite) | 生产必填 |
| `DB_POOL_SIZE` | 连接池大小 | 20 | 否 |
| `DB_MAX_OVERFLOW` | 最大溢出 | 10 | 否 |
| `REDIS_URL` | Redis 连接 | redis://localhost:6379/0 | 否 |
| `JWT_SECRET_KEY` | JWT 密钥 | (自动生成) | 生产必填 |
| `CORS_ORIGINS` | CORS 域名 | localhost:3000,5173 | 生产必填 |
| `LOG_LEVEL` | 日志级别 | INFO | 否 |
| `LOG_FORMAT` | 日志格式 | json | 否 |
| `DEV_DEFAULT_USER` | 开发默认用户 | (空) | 否 |

### 6.2 Docker Compose 配置

**开发环境** (`docker-compose.yml`):
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Backend: localhost:8688
- Frontend: localhost:3000

**生产环境** (`docker-compose.prod.yml`):
- 使用 Docker Secrets 管理敏感信息
- 资源限制 (CPU/Memory)
- 健康检查
- 日志轮转
- 多副本部署

---

## 7. 验证部署

### 7.1 使用验证脚本

```bash
# Linux/Mac
./scripts/verify-deployment.sh http://localhost:8688 http://localhost:3000

# Windows
curl http://localhost:8688/health
curl http://localhost:8688/ready
```

### 7.2 手动验证

```bash
# 1. 健康检查
curl http://localhost:8688/health
# 期望: {"status":"ok","version":"3.2.0"}

# 2. 就绪检查
curl http://localhost:8688/ready
# 期望: {"status":"ok","ready":true}

# 3. API 测试
curl http://localhost:8688/api/v1/assets
curl http://localhost:8688/api/v1/alerts
curl http://localhost:8688/api/v1/operations

# 4. Chat 测试
curl -X POST http://localhost:8688/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"帮助"}'
# 期望: {"success":true,"intent":"help",...}

# 5. 前端访问
# 浏览器打开 http://localhost:3000
```

### 7.3 E2E 测试

```bash
cd tests/e2e
npm install
npx playwright install chromium
npx playwright test
# 期望: 23 passed
```

---

## 8. 故障排查

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 端口被占用 | 其他进程占用端口 | `netstat -ano \| findstr :8688` 找到并停止进程 |
| 数据库连接失败 | PostgreSQL 未启动 | `docker compose up -d postgres` |
| Redis 连接失败 | Redis 未启动 | `docker compose up -d redis` |
| JWT 认证失败 | 密钥不匹配 | 检查 .env 中的 JWT_SECRET_KEY |
| 前端白屏 | API 代理配置错误 | 检查 vite.config.ts 中的 proxy 配置 |
| 测试失败 | 测试数据库问题 | `docker compose down -v && docker compose up -d` |

### 8.2 日志查看

```bash
# 查看所有服务日志
docker compose logs -f

# 查看后端日志
docker compose logs -f backend

# 查看数据库日志
docker compose logs -f postgres

# 查看最近错误
docker compose logs --tail=100 backend | grep -i error
```

### 8.3 数据库操作

```bash
# 进入数据库
docker compose exec postgres psql -U v32 -d v32_sre

# 查看表
\dt

# 查看数据
SELECT count(*) FROM assets;
SELECT count(*) FROM alerts;
SELECT count(*) FROM operations;

# 运行迁移
cd backend && alembic upgrade head

# 回滚迁移
cd backend && alembic downgrade -1
```

### 8.4 重置环境

```bash
# 完全重置
docker compose down -v
rm -f .env
rm -rf secrets/

# 重新部署
./scripts/deploy-linux.sh dev
```

---

## 附录

### A. 文件结构

```
v3.2/
├── scripts/
│   ├── deploy-linux.sh      # Linux 部署脚本
│   ├── deploy-windows.ps1   # Windows 部署脚本
│   └── verify-deployment.sh # 部署验证脚本
├── backend/
│   ├── app/                 # FastAPI 应用
│   ├── tests/               # 测试
│   └── requirements.txt     # Python 依赖
├── frontend/
│   ├── src/                 # React 应用
│   └── package.json         # Node 依赖
├── db/
│   ├── schema.sql           # 数据库 Schema
│   ├── migrations/          # Alembic 迁移
│   └── seeds/               # 种子数据
├── docs/                    # 文档
├── tests/e2e/               # E2E 测试
├── docker-compose.yml       # 开发环境
├── docker-compose.prod.yml  # 生产环境
└── .env                     # 环境变量
```

### B. API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /ready | 就绪检查 |
| GET | /api/v1/assets | 资产列表 |
| GET | /api/v1/alerts | 告警列表 |
| GET | /api/v1/operations | 操作列表 |
| POST | /api/v1/chat | AI 聊天 |
| GET | /api/v1/dashboard/summary | 仪表盘汇总 |
| GET | /api/v1/atomics | 原子操作列表 |

### C. 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+K | 打开命令面板 |
| Esc | 关闭弹窗 |
| / | 聚焦聊天输入 |
