# V3.2 操作手册

> **版本**: 3.2.0 | **更新**: 2026-06-01

---

## 1. 平台管理操作

### 1.1 添加平台

**操作步骤**:

1. 登录系统 → 侧边栏 → 设置 → 平台管理
2. 点击右上角 "添加平台" 按钮
3. 选择平台类型:
   - VMware vSphere
   - KVM/QEMU
   - Huawei FusionSphere
4. 填写连接信息:
   - 平台名称 (自定义)
   - 主机地址
   - 端口
   - 用户名
   - 密码
   - SSL 验证 (可选)
5. 点击 "测试连接" 验证配置
6. 连接成功后点击 "保存"

**API 调用**:
```bash
POST /api/v1/platforms
{
  "name": "生产 vCenter",
  "platform_type": "vsphere",
  "host": "vcenter.example.com",
  "port": 443,
  "username": "admin@vsphere.local",
  "password": "******",
  "verify_ssl": false
}
```

### 1.2 测试平台连接

**操作步骤**:

1. 平台列表 → 找到目标平台
2. 点击 "测试连接" 按钮
3. 等待测试结果:
   - ✅ 成功: 显示版本、延迟、设备数量
   - ❌ 失败: 显示错误信息

**API 调用**:
```bash
POST /api/v1/platforms/{platform_id}/test
```

**响应示例**:
```json
{
  "success": true,
  "latency_ms": 45,
  "version": "7.0.3",
  "details": {
    "datacenter": "DC01",
    "clusters": 3,
    "hosts": 16,
    "vms": 1284
  }
}
```

### 1.3 同步设备

**操作步骤**:

1. 平台列表 → 找到目标平台
2. 点击 "同步" 按钮
3. 等待同步完成
4. 查看同步结果:
   - 新增设备数
   - 更新设备数
   - 删除设备数

**API 调用**:
```bash
POST /api/v1/platforms/{platform_id}/sync
```

### 1.4 编辑平台

**操作步骤**:

1. 平台列表 → 找到目标平台
2. 点击 "编辑" 按钮
3. 修改配置信息
4. 点击 "测试连接" 验证
5. 点击 "保存"

**API 调用**:
```bash
PUT /api/v1/platforms/{platform_id}
{
  "name": "更新后的名称",
  "host": "new-host.example.com"
}
```

### 1.5 删除平台

**操作步骤**:

1. 平台列表 → 找到目标平台
2. 点击 "删除" 按钮
3. 确认删除
4. 系统自动断开连接并删除配置

**API 调用**:
```bash
DELETE /api/v1/platforms/{platform_id}
```

---

## 2. 设备管理操作

### 2.1 查看设备列表

**操作步骤**:

1. 侧边栏 → 资源管理
2. 选择设备类型:
   - 虚拟机
   - 物理机
   - 存储
3. 使用筛选条件:
   - 平台筛选
   - 状态筛选
   - 搜索框

**API 调用**:
```bash
GET /api/v1/assets?type=vm&platform=vsphere&status=running&page=1&limit=50
```

### 2.2 查看设备详情

**操作步骤**:

1. 设备列表 → 点击目标设备
2. 查看详细信息:
   - 基本信息 (名称、IP、平台)
   - 资源使用 (CPU、内存、磁盘)
   - 操作历史
   - 快照列表

**API 调用**:
```bash
GET /api/v1/assets/{asset_id}
```

### 2.3 执行设备操作

**操作步骤**:

1. 设备详情 → 点击操作按钮
2. 选择操作类型:
   - 开机
   - 关机
   - 重启
   - 创建快照
3. 确认操作
4. 查看操作结果

**API 调用**:
```bash
POST /api/v1/assets/{asset_id}/actions
{
  "action": "restart",
  "params": {"graceful": true}
}
```

---

## 3. 告警管理操作

### 3.1 查看告警

**操作步骤**:

1. 侧边栏 → 告警中心
2. 查看告警列表:
   - 按严重级别筛选 (P0-P4)
   - 按状态筛选 (活跃/已确认/已解决)
   - 按时间范围筛选

**API 调用**:
```bash
GET /api/v1/alerts?severity=P0&status=active&page=1&limit=20
```

### 3.2 确认告警

**操作步骤**:

1. 告警列表 → 找到目标告警
2. 点击 "确认" 按钮
3. 填写确认备注 (可选)
4. 确认操作

**API 调用**:
```bash
PUT /api/v1/alerts/{alert_id}/acknowledge
{
  "notes": "已确认，正在排查"
}
```

### 3.3 解决告警

**操作步骤**:

1. 告警列表 → 找到目标告警
2. 点击 "解决" 按钮
3. 填写解决方案
4. 确认操作

**API 调用**:
```bash
PUT /api/v1/alerts/{alert_id}/resolve
{
  "resolution": "已重启服务，问题解决"
}
```

---

## 4. 迁移操作

### 4.1 生成迁移计划

**操作步骤**:

1. 侧边栏 → 迁移管理
2. 点击 "新建迁移"
3. 选择源虚拟机
4. 选择目标平台
5. 点击 "生成计划"
6. 查看迁移计划:
   - 迁移工具
   - 执行步骤
   - 预计时间
   - 风险提示

**API 调用**:
```bash
POST /api/v1/migration/plan
{
  "vm_id": "vm-123",
  "source_platform": "vsphere",
  "target_platform": "kvm"
}
```

**响应示例**:
```json
{
  "id": "plan-uuid",
  "source_vm": {
    "id": "vm-123",
    "name": "web-01",
    "platform": "vsphere"
  },
  "target_platform": "kvm",
  "tool": {
    "name": "virt-v2v",
    "description": "Red Hat 官方迁移工具"
  },
  "steps": [
    {"step": 1, "description": "预检查", "estimated_seconds": 60},
    {"step": 2, "description": "源 VM 快照", "estimated_seconds": 120},
    {"step": 3, "description": "磁盘导出", "estimated_seconds": 300},
    {"step": 4, "description": "格式转换", "estimated_seconds": 600},
    {"step": 5, "description": "目标导入", "estimated_seconds": 300},
    {"step": 6, "description": "启动验证", "estimated_seconds": 120}
  ],
  "risks": [
    "需要关闭源 VM",
    "网络配置需要手动调整"
  ],
  "estimated_time_seconds": 1500
}
```

### 4.2 执行迁移

**操作步骤**:

1. 迁移计划页面 → 确认计划无误
2. 点击 "执行迁移"
3. 确认执行
4. 查看执行进度:
   - 当前步骤
   - 完成百分比
   - 预计剩余时间
5. 等待完成
6. 验证结果

**API 调用**:
```bash
POST /api/v1/migration/execute
{
  "plan_id": "plan-uuid"
}
```

### 4.3 查看迁移状态

**操作步骤**:

1. 迁移管理 → 迁移历史
2. 找到目标迁移
3. 查看详细状态:
   - 当前步骤
   - 进度百分比
   - 错误信息 (如有)

**API 调用**:
```bash
GET /api/v1/migration/{migration_id}
```

### 4.4 回滚迁移

**操作步骤**:

1. 迁移历史 → 找到目标迁移
2. 点击 "回滚" 按钮
3. 确认回滚
4. 等待回滚完成
5. 验证源 VM 恢复

**API 调用**:
```bash
POST /api/v1/migration/{migration_id}/rollback
```

---

## 5. AI 助手操作

### 5.1 发送消息

**操作步骤**:

1. 侧边栏 → AI 助手
2. 在输入框输入自然语言指令
3. 按 Enter 或点击发送
4. 查看 Agent 回复

**示例指令**:
- "查看集群资源使用情况"
- "web-01 连接超时了"
- "重启 db-01"
- "查看告警"
- "帮助"

**API 调用**:
```bash
POST /api/v1/chat
{
  "message": "web-01 连接超时了"
}
```

### 5.2 确认操作

**操作步骤**:

1. Agent 推荐操作后，显示确认按钮
2. 点击 "确认执行"
3. 查看执行结果

### 5.3 使用快捷指令

**操作步骤**:

1. AI 助手页面 → 底部快捷按钮
2. 点击快捷指令:
   - 查看集群
   - 查看告警
   - 帮助
   - 主机列表

---

## 6. 仪表盘操作

### 6.1 查看仪表盘

**操作步骤**:

1. 侧边栏 → 仪表盘
2. 查看统计卡片:
   - 虚拟机总数
   - 主机数量
   - 活跃告警
   - 集群数量
3. 查看图表:
   - 资源使用率
   - 告警分布
   - 趋势图

### 6.2 刷新数据

**操作步骤**:

1. 仪表盘页面 → 点击 "刷新" 按钮
2. 等待数据更新

---

## 7. 批量操作

### 7.1 批量选择

**操作步骤**:

1. 资源列表 → 勾选多个设备
2. 底部显示批量操作栏
3. 显示已选数量

### 7.2 批量操作

**操作步骤**:

1. 批量操作栏 → 选择操作:
   - 批量开机
   - 批量关机
   - 批量重启
   - 批量迁移
2. 确认操作
3. 查看执行结果

---

## 8. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+K` | 打开命令面板 |
| `Esc` | 关闭弹窗 |
| `/` | 聚焦 AI 助手输入框 |
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行 |

---

## 9. 常见问题

### 9.1 平台连接失败

**问题**: 测试连接显示失败

**解决**:
1. 检查网络连通性
2. 验证账号密码
3. 检查防火墙规则
4. 查看后端日志

### 9.2 设备同步失败

**问题**: 同步设备显示失败

**解决**:
1. 先测试平台连接
2. 检查平台权限
3. 查看后端日志

### 9.3 迁移失败

**问题**: 迁移执行失败

**解决**:
1. 查看迁移状态详情
2. 检查源 VM 状态
3. 检查目标平台资源
4. 尝试回滚

### 9.4 AI 助手无响应

**问题**: 发送消息后无回复

**解决**:
1. 检查后端服务状态
2. 查看后端日志
3. 刷新页面重试
