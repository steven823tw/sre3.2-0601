# V3.2 — Engineer Assist SRE Platform

> **版本**: 3.2.0 | **Python**: 3.14.5 | **PostgreSQL**: 16

---

## 平台纳管与迁移

V3.2 新增真实虚拟化平台接入和跨平台迁移能力。

### 支持平台

| 平台 | SDK | 版本 | 操作 |
|------|-----|------|------|
| VMware vSphere | pyVmomi | 8.0.3 | VM 管理、快照、vMotion |
| KVM/QEMU | libvirt-python | 12.x | VM 管理、快照、迁移 |
| Huawei FusionSphere | httpx (REST) | 8.0 | VM 管理、快照 |

### 迁移场景

| 源 | 目标 | 工具 |
|----|------|------|
| VMware | KVM | virt-v2v |
| VMware | FusionSphere | qemu-img |
| KVM | VMware | qemu-img |

---

## 快速开始

```bash
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8688

# 3. 前端
cd frontend
npm install
npm run dev

# 4. 访问
open http://localhost:5173
```

## API 端点

### 平台管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/platforms | 平台列表 |
| POST | /api/v1/platforms | 添加平台 |
| POST | /api/v1/platforms/{id}/test | 测试连接 |
| POST | /api/v1/platforms/{id}/sync | 同步设备 |

### 迁移管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/migration/plan | 生成迁移计划 |
| POST | /api/v1/migration/execute | 执行迁移 |
| GET | /api/v1/migration/{id} | 迁移状态 |

## 文档

| 文档 | 说明 |
|------|------|
| docs/V3.1_DEVELOPMENT_PLAN.md | 开发计划 |
| docs/PLATFORM_SDK_RESEARCH.md | SDK 研究报告 |
| docs/PLATFORM_INTEGRATION_PLAN.md | 纳管方案 |
