# V3.2 测试环境部署指南

> **版本**: 3.2.0 | **更新**: 2026-06-01

---

## 1. 环境要求

### 1.1 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB SSD | 50 GB SSD |
| 网络 | 100 Mbps | 1 Gbps |

### 1.2 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Docker | 24+ | 容器引擎 |
| Docker Compose | 2.20+ | 容器编排 |
| Python | 3.14.5 | 后端运行时 |
| Node.js | 22 LTS | 前端构建 |
| PostgreSQL | 16 | 数据库 |
| Redis | 7 | 缓存 |

### 1.3 网络要求

| 端口 | 服务 | 说明 |
|------|------|------|
| 3000 | Frontend | React 开发服务器 |
| 8688 | Backend | FastAPI API 服务 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存 |

---

## 2. 快速部署

### 2.1 使用 Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone <repository-url> v3.2
cd v3.2

# 2. 创建环境配置
cp .env.example .env
# 编辑 .env 文件配置数据库密码等

# 3. 启动所有服务
docker compose up -d

# 4. 验证服务状态
docker compose ps

# 5. 访问应用
# Frontend: http://localhost:3000
# Backend: http://localhost:8688
# API Docs: http://localhost:8688/docs
```

### 2.2 手动部署

```bash
# 1. 启动数据库
docker compose up -d postgres redis

# 2. 后端部署
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8688

# 3. 前端部署 (新终端)
cd frontend
npm install
npm run dev

# 4. 访问
# http://localhost:3000
```

---

## 3. 环境变量配置

### 3.1 后端配置 (.env)

```bash
# ===== 应用配置 =====
APP_NAME=Engineer Assist
APP_VERSION=3.2.0
APP_ENV=development
APP_DEBUG=true

# ===== 数据库配置 =====
DATABASE_URL=postgresql+asyncpg://v32:your_password@localhost:5432/v32_sre
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ===== Redis 配置 =====
REDIS_URL=redis://localhost:6379/0

# ===== JWT 配置 =====
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=30

# ===== CORS 配置 =====
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ===== 日志配置 =====
LOG_LEVEL=DEBUG
LOG_FORMAT=console

# ===== 开发配置 =====
DEV_DEFAULT_USER=dev-user
```

### 3.2 前端配置 (.env)

```bash
VITE_API_BASE_URL=/api/v1
VITE_WS_URL=ws://localhost:8688/ws
```

---

## 4. 平台接入配置

### 4.1 VMware vSphere 接入

**前置条件**:
- vCenter Server 或 ESXi 主机地址
- 管理员账号密码
- 网络可达 (端口 443)

**配置步骤**:

1. 访问 http://localhost:3000/settings/platforms
2. 点击 "添加平台"
3. 选择 "VMware vSphere"
4. 填写配置:
   - 名称: 生产 vCenter
   - 主机: vcenter.example.com
   - 端口: 443
   - 用户名: admin@vsphere.local
   - 密码: ******
   - SSL 验证: 根据环境选择
5. 点击 "测试连接"
6. 确认连接成功后保存

**API 方式**:
```bash
curl -X POST http://localhost:8688/api/v1/platforms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "生产 vCenter",
    "platform_type": "vsphere",
    "host": "vcenter.example.com",
    "port": 443,
    "username": "admin@vsphere.local",
    "password": "your_password",
    "verify_ssl": false
  }'
```

### 4.2 KVM/QEMU 接入

**前置条件**:
- KVM 主机地址
- SSH 访问权限 (root 或 sudo)
- libvirtd 服务运行中

**配置步骤**:

1. 访问 http://localhost:3000/settings/platforms
2. 点击 "添加平台"
3. 选择 "KVM/QEMU"
4. 填写配置:
   - 名称: 生产 KVM
   - 主机: kvm-host.example.com
   - 端口: 22
   - 用户名: root
   - 密码: ******
5. 点击 "测试连接"
6. 确认连接成功后保存

**API 方式**:
```bash
curl -X POST http://localhost:8688/api/v1/platforms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "生产 KVM",
    "platform_type": "kvm",
    "host": "kvm-host.example.com",
    "port": 22,
    "username": "root",
    "password": "your_password"
  }'
```

### 4.3 Huawei FusionSphere 接入

**前置条件**:
- FusionCompute VRM 地址
- 管理员账号密码
- 网络可达 (端口 443)

**配置步骤**:

1. 访问 http://localhost:3000/settings/platforms
2. 点击 "添加平台"
3. 选择 "Huawei FusionSphere"
4. 填写配置:
   - 名称: 生产 FusionSphere
   - 主机: fusionsphere.example.com
   - 端口: 443
   - 用户名: admin
   - 密码: ******
5. 点击 "测试连接"
6. 确认连接成功后保存

**API 方式**:
```bash
curl -X POST http://localhost:8688/api/v1/platforms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "生产 FusionSphere",
    "platform_type": "fusionsphere",
    "host": "fusionsphere.example.com",
    "port": 443,
    "username": "admin",
    "password": "your_password"
  }'
```

---

## 5. 功能验证

### 5.1 平台连接测试

```bash
# 测试平台连接
curl -X POST http://localhost:8688/api/v1/platforms/{platform_id}/test

# 期望响应:
# {
#   "success": true,
#   "latency_ms": 45,
#   "version": "7.0.3",
#   "details": {
#     "datacenter": "DC01",
#     "clusters": 3,
#     "hosts": 16,
#     "vms": 1284
#   }
# }
```

### 5.2 设备同步测试

```bash
# 同步设备
curl -X POST http://localhost:8688/api/v1/platforms/{platform_id}/sync

# 查看设备列表
curl http://localhost:8688/api/v1/platforms/{platform_id}/devices
```

### 5.3 迁移测试

```bash
# 生成迁移计划
curl -X POST http://localhost:8688/api/v1/migration/plan \
  -H "Content-Type: application/json" \
  -d '{
    "vm_id": "vm-123",
    "source_platform": "vsphere",
    "target_platform": "kvm"
  }'

# 执行迁移
curl -X POST http://localhost:8688/api/v1/migration/execute \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "plan-uuid"}'

# 查看迁移状态
curl http://localhost:8688/api/v1/migration/{migration_id}
```

### 5.4 E2E 测试

```bash
cd tests/e2e
npm install
npx playwright test

# 期望结果: 23 passed
```

---

## 6. 故障排查

### 6.1 连接失败

**问题**: 平台连接测试失败

**排查步骤**:
```bash
# 1. 检查网络连通性
ping vcenter.example.com

# 2. 检查端口可达性
telnet vcenter.example.com 443

# 3. 检查后端日志
docker compose logs backend | grep -i error

# 4. 检查平台配置
curl http://localhost:8688/api/v1/platforms/{id}
```

### 6.2 数据库连接失败

**问题**: 后端无法连接数据库

**排查步骤**:
```bash
# 1. 检查数据库状态
docker compose ps postgres

# 2. 测试数据库连接
docker compose exec postgres psql -U v32 -d v32_sre -c "SELECT 1"

# 3. 检查环境变量
echo $DATABASE_URL

# 4. 检查后端日志
docker compose logs backend | grep -i database
```

### 6.3 前端白屏

**问题**: 前端页面白屏

**排查步骤**:
```bash
# 1. 检查前端服务
curl http://localhost:3000

# 2. 检查浏览器控制台 (F12)

# 3. 检查 API 代理
curl http://localhost:3000/api/v1/health

# 4. 检查前端日志
docker compose logs frontend
```

---

## 7. 监控与日志

### 7.1 查看日志

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

### 7.2 健康检查

```bash
# 后端健康检查
curl http://localhost:8688/health

# 就绪检查
curl http://localhost:8688/ready

# 数据库检查
curl http://localhost:8688/health/db
```

---

## 8. 备份与恢复

### 8.1 数据库备份

```bash
# 备份数据库
docker compose exec postgres pg_dump -U v32 -d v32_sre -F c -f /tmp/backup.dump
docker cp v32-postgres:/tmp/backup.dump ./backup/

# 恢复数据库
docker cp ./backup/backup.dump v32-postgres:/tmp/
docker compose exec postgres pg_restore -U v32 -d v32_sre -c /tmp/backup.dump
```

### 8.2 配置备份

```bash
# 备份配置
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```
