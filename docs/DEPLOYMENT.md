# V3.1 部署指南

## 环境变量

### 后端 (`backend/.env`)

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://v31:password@localhost:5432/v31_sre
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# 应用
APP_NAME=V3.1 SRE Platform
APP_ENV=development          # development | staging | production
APP_DEBUG=true
LOG_LEVEL=DEBUG              # DEBUG | INFO | WARNING | ERROR

# 安全
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480       # 8 hours

# AI (可选)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### 前端 (`frontend/.env`)

```bash
VITE_API_BASE_URL=/api/v1
VITE_WS_URL=ws://localhost:8688/ws
```

## Docker 部署

### 开发环境

```bash
# 一键启动
docker compose up -d

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 停止
docker compose down
```

### 生产环境

```bash
# 构建镜像
docker compose -f docker-compose.prod.yml build

# 启动
docker compose -f docker-compose.prod.yml up -d

# 数据库迁移
docker compose exec backend alembic upgrade head
```

## 数据库维护

### 备份

```bash
# 每日备份
pg_dump -U v31 -d v31_sre -F c -f backup_$(date +%Y%m%d).dump

# 恢复
pg_restore -U v31 -d v31_sre backup_20260530.dump
```

### 分区维护

```bash
# 创建新月份分区 (alerts, audit_logs)
psql -U v31 -d v31_sre -c "SELECT create_monthly_partition('alerts', '2026-07-01');"
psql -U v31 -d v31_sre -c "SELECT create_monthly_partition('audit_logs', '2026-07-01');"

# 清理过期分区
psql -U v31 -d v31_sre -c "SELECT drop_expired_partitions('alerts', 365);"
psql -U v31 -d v31_sre -c "SELECT drop_expired_partitions('audit_logs', 180);"
```

## 监控

### 健康检查

```bash
# 后端健康
curl http://localhost:8688/api/v1/health

# 就绪检查
curl http://localhost:8688/api/v1/health/ready

# 数据库连接
curl http://localhost:8688/api/v1/health/db
```

### Prometheus 指标

```
http://localhost:8688/metrics
```

关键指标:
- `http_request_duration_seconds` — API 响应时间
- `database_pool_size` — 数据库连接池使用
- `active_operations` — 当前执行中的操作数
- `alert_count_by_severity` — 按严重级别统计的告警数
