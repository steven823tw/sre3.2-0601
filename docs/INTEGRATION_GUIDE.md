# V3.1 集成指南

## 前后端集成

### API 代理配置

前端 Vite 开发服务器已配置 API 代理：

```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8688',
        changeOrigin: true,
      },
    },
  },
});
```

### 启动流程

```bash
# 终端 1: 启动数据库
docker compose up -d postgres redis

# 终端 2: 启动后端
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8688

# 终端 3: 启动前端
cd frontend
npm install
npm run dev

# 终端 4: 运行测试
cd backend && pytest
cd frontend && npm run test
```

### 验证集成

```bash
# 1. 检查后端健康
curl http://localhost:8688/api/v1/health

# 2. 检查前端代理
curl http://localhost:5173/api/v1/health

# 3. 测试 Chat API
curl -X POST http://localhost:8688/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "查看告警"}'

# 4. 测试 Assets API
curl http://localhost:8688/api/v1/assets?type=vm&limit=10

# 5. 测试 Alerts API
curl http://localhost:8688/api/v1/alerts?severity=P0&status=active
```

## 数据库集成

### 运行迁移

```bash
cd backend
alembic upgrade head
```

### 生成种子数据

```bash
cd db/seeds
python generate_test_data.py --output seed.sql
psql -U v31 -d v31_sre -f seed.sql
```

### 验证数据

```sql
-- 检查资产数量
SELECT asset_type, COUNT(*) FROM assets GROUP BY asset_type;

-- 检查告警分布
SELECT severity, status, COUNT(*) FROM alerts GROUP BY severity, status;

-- 检查操作记录
SELECT operation_type, status, COUNT(*) FROM operations GROUP BY operation_type, status;
```

## 环境变量

### 后端 (.env)

```bash
DATABASE_URL=postgresql+asyncpg://v31:password@localhost:5432/v31_sre
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=DEBUG
JWT_SECRET_KEY=dev-secret-key
```

### 前端 (.env)

```bash
VITE_API_BASE_URL=/api/v1
VITE_WS_URL=ws://localhost:8688/ws
```

## 常见问题

### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker compose ps

# 检查连接
psql -U v31 -d v31_sre -c "SELECT 1"

# 检查环境变量
echo $DATABASE_URL
```

### 2. 前端 API 调用失败

```bash
# 检查后端是否运行
curl http://localhost:8688/api/v1/health

# 检查代理配置
cat frontend/vite.config.ts

# 检查浏览器控制台错误
```

### 3. 测试失败

```bash
# 后端测试
cd backend && pytest -v --tb=short

# 前端测试
cd frontend && npm run test -- --reporter=verbose

# 检查测试数据库
psql -U v31 -d v31_sre_test -c "SELECT 1"
```

### 4. 类型错误

```bash
# 后端类型检查
cd backend && mypy app/

# 前端类型检查
cd frontend && npx tsc --noEmit
```
