# V3.1 平台纳管与迁移实施方案

> **版本**: 1.0 | **日期**: 2026-05-31 | **状态**: 规划中

---

## 目录

1. [需求分析](#1-需求分析)
2. [平台纳管架构](#2-平台纳管架构)
3. [平台适配器设计](#3-平台适配器设计)
4. [纳管 UI 设计](#4-纳管-ui-设计)
5. [跨平台迁移方案](#5-跨平台迁移方案)
6. [软件版本优化](#6-软件版本优化)
7. [实施路线图](#7-实施路线图)

---

## 1. 需求分析

### 1.1 工程师反馈

| # | 反馈 | 优先级 | 影响 |
|---|------|--------|------|
| 1 | 平台接入是模拟的，需要真实 API/SDK 集成 | P0 | 核心功能不可用 |
| 2 | 需要图形化的平台纳管配置界面 | P1 | 用户体验 |
| 3 | 需要跨平台 VM 迁移能力 | P1 | 业务价值 |
| 4 | 软件版本需要更新到最新 | P2 | 性能和安全 |

### 1.2 目标平台

| 平台 | 类型 | API/SDK | 优先级 |
|------|------|---------|--------|
| VMware vSphere | 商业虚拟化 | pyVmomi / vSphere Automation SDK | P0 |
| Huawei FusionSphere | 国产虚拟化 | FusionCompute REST API | P0 |
| KVM/QEMU (libvirt) | 开源虚拟化 | libvirt-python | P0 |
| OpenStack | 私有云 | openstacksdk | P1 |
| Kubernetes | 容器平台 | kubernetes-client | P1 |

---

## 2. 平台纳管架构

### 2.1 分层设计

```
┌─────────────────────────────────────────────────────────────┐
│                    平台纳管 UI (Frontend)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 添加平台  │  │ 测试连接 │  │ 设备导入  │  │ 状态监控  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    平台管理 API (Backend)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ CRUD     │  │ 连接测试 │  │ 设备同步  │  │ 健康检查  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    适配器层 (Adapter Layer)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ vSphere  │  │ FusionSphere │ libvirt │  │ OpenStack│   │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    平台连接层 (Connection Layer)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ pyVmomi  │  │ REST API │  │ libvirt  │  │ openstack│   │
│  │ SDK      │  │ Client   │  │ python   │  │ sdk      │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心接口

```python
# backend/app/platforms/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class PlatformType(str, Enum):
    VSPHERE = "vsphere"
    FUSIONSPHERE = "fusionsphere"
    KVM = "kvm"
    OPENSTACK = "openstack"
    KUBERNETES = "kubernetes"

@dataclass
class PlatformConfig:
    """平台连接配置"""
    platform_type: PlatformType
    host: str
    port: int = 443
    username: str = ""
    password: str = ""
    verify_ssl: bool = True
    extra: dict = None

@dataclass
class ConnectionTestResult:
    """连接测试结果"""
    success: bool
    latency_ms: int
    version: str
    details: dict
    error: str = None

@dataclass
class DeviceInfo:
    """设备信息"""
    id: str
    name: str
    device_type: str  # vm, host, storage, network
    status: str
    ip_address: str
    platform: str
    metadata: dict

class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    platform_type: PlatformType
    
    @abstractmethod
    async def connect(self, config: PlatformConfig) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """测试连接"""
        pass
    
    @abstractmethod
    async def list_vms(self) -> list[DeviceInfo]:
        """列出所有虚拟机"""
        pass
    
    @abstractmethod
    async def list_hosts(self) -> list[DeviceInfo]:
        """列出所有主机"""
        pass
    
    @abstractmethod
    async def get_vm_status(self, vm_id: str) -> DeviceInfo:
        """获取虚拟机状态"""
        pass
    
    @abstractmethod
    async def power_on(self, vm_id: str) -> bool:
        """开机"""
        pass
    
    @abstractmethod
    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """关机"""
        pass
    
    @abstractmethod
    async def reboot(self, vm_id: str, graceful: bool = True) -> bool:
        """重启"""
        pass
    
    @abstractmethod
    async def create_snapshot(self, vm_id: str, name: str, description: str = "") -> str:
        """创建快照，返回快照 ID"""
        pass
    
    @abstractmethod
    async def list_snapshots(self, vm_id: str) -> list[dict]:
        """列出快照"""
        pass
    
    @abstractmethod
    async def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        """还原快照"""
        pass
    
    @abstractmethod
    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        """删除快照"""
        pass
    
    @abstractmethod
    async def migrate(self, vm_id: str, target_host: str = None, 
                      target_storage: str = None) -> bool:
        """迁移虚拟机"""
        pass
    
    @abstractmethod
    async def get_metrics(self, vm_id: str) -> dict:
        """获取监控指标 (CPU, Memory, Disk, Network)"""
        pass
```

---

## 3. 平台适配器设计

### 3.1 VMware vSphere 适配器

```python
# backend/app/platforms/vsphere/adapter.py
"""
VMware vSphere 平台适配器

使用 pyVmomi SDK 连接 vCenter/ESXi，执行虚拟机管理操作。

依赖: pyvmomi >= 8.0
文档: https://github.com/vmware/pyvmomi
"""

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import ssl

class VSphereAdapter(PlatformAdapter):
    """VMware vSphere 适配器"""
    
    platform_type = PlatformType.VSPHERE
    
    def __init__(self):
        self._si = None  # ServiceInstance
        self._content = None
        self._config = None
    
    async def connect(self, config: PlatformConfig) -> bool:
        """连接到 vCenter/ESXi"""
        context = ssl.create_default_context()
        if not config.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        self._si = SmartConnect(
            host=config.host,
            user=config.username,
            pwd=config.password,
            port=config.port,
            sslContext=context,
        )
        self._content = self._si.RetrieveContent()
        self._config = config
        return True
    
    async def test_connection(self) -> ConnectionTestResult:
        """测试连接并返回 vCenter 信息"""
        import time
        start = time.time()
        
        try:
            about = self._content.about
            latency = int((time.time() - start) * 1000)
            
            return ConnectionTestResult(
                success=True,
                latency_ms=latency,
                version=about.version,
                details={
                    "fullName": about.fullName,
                    "vendor": about.vendor,
                    "instanceUuid": about.instanceUuid,
                    "datacenter": self._get_datacenter_count(),
                    "clusters": self._get_cluster_count(),
                    "hosts": self._get_host_count(),
                    "vms": self._get_vm_count(),
                },
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                latency_ms=0,
                version="",
                details={},
                error=str(e),
            )
    
    async def list_vms(self) -> list[DeviceInfo]:
        """列出所有虚拟机"""
        container = self._content.viewManager.CreateContainerView(
            self._content.rootFolder, [vim.VirtualMachine], True
        )
        
        vms = []
        for vm in container.view:
            vms.append(DeviceInfo(
                id=vm._moId,
                name=vm.name,
                device_type="vm",
                status=self._get_vm_status(vm),
                ip_address=vm.guest.ipAddress if vm.guest else "",
                platform="vSphere",
                metadata={
                    "cpu": vm.config.hardware.numCPU if vm.config else 0,
                    "memory_mb": vm.config.hardware.memoryMB if vm.config else 0,
                    "guest_os": vm.config.guestFullName if vm.config else "",
                    "host": vm.runtime.host.name if vm.runtime.host else "",
                    "cluster": vm.runtime.host.parent.name if vm.runtime.host and hasattr(vm.runtime.host.parent, 'name') else "",
                },
            ))
        
        container.Destroy()
        return vms
    
    async def power_on(self, vm_id: str) -> bool:
        """开机"""
        vm = self._get_vm_by_id(vm_id)
        task = vm.PowerOnVM_Task()
        return await self._wait_task(task)
    
    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """关机"""
        vm = self._get_vm_by_id(vm_id)
        if graceful:
            task = vm.ShutdownGuest()
        else:
            task = vm.PowerOffVM_Task()
        return True
    
    async def create_snapshot(self, vm_id: str, name: str, 
                              description: str = "") -> str:
        """创建快照"""
        vm = self._get_vm_by_id(vm_id)
        task = vm.CreateSnapshot_Task(
            name=name,
            description=description,
            memory=False,
            quiesce=True,
        )
        result = await self._wait_task(task)
        return result if result else ""
    
    async def migrate(self, vm_id: str, target_host: str = None,
                      target_storage: str = None) -> bool:
        """迁移虚拟机 (vMotion / Storage vMotion)"""
        vm = self._get_vm_by_id(vm_id)
        
        if target_host and target_storage:
            # 冷迁移 (计算 + 存储)
            host = self._get_host_by_name(target_host)
            ds = self._get_datastore_by_name(target_storage)
            spec = vim.vm.RelocateSpec(
                host=host,
                datastore=ds,
            )
        elif target_host:
            # vMotion (仅计算)
            host = self._get_host_by_name(target_host)
            spec = vim.vm.RelocateSpec(host=host)
        elif target_storage:
            # Storage vMotion (仅存储)
            ds = self._get_datastore_by_name(target_storage)
            spec = vim.vm.RelocateSpec(datastore=ds)
        else:
            return False
        
        task = vm.Relocate_Task(spec=spec)
        return await self._wait_task(task)
```

### 3.2 Huawei FusionSphere 适配器

```python
# backend/app/platforms/fusionsphere/adapter.py
"""
Huawei FusionSphere / FusionCompute 平台适配器

使用 FusionCompute REST API 进行虚拟机管理。

API 文档: https://support.huawei.com/enterprise/zh/doc/EDOC1100266502
认证: Token-based (POST /service/sessions)
"""

import httpx

class FusionSphereAdapter(PlatformAdapter):
    """Huawei FusionSphere 适配器"""
    
    platform_type = PlatformType.FUSIONSPHERE
    
    def __init__(self):
        self._client = None
        self._token = None
        self._config = None
    
    async def connect(self, config: PlatformConfig) -> bool:
        """连接到 FusionCompute"""
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=f"https://{config.host}:{config.port}/service",
            verify=config.verify_ssl,
            timeout=30.0,
        )
        
        # 获取 Token
        response = await self._client.post("/sessions", json={
            "username": config.username,
            "password": config.password,
        })
        response.raise_for_status()
        self._token = response.json().get("token")
        
        # 设置默认 Header
        self._client.headers["X-Auth-Token"] = self._token
        return True
    
    async def test_connection(self) -> ConnectionTestResult:
        """测试连接"""
        import time
        start = time.time()
        
        try:
            response = await self._client.get("/clusters")
            latency = int((time.time() - start) * 1000)
            clusters = response.json().get("clusters", [])
            
            return ConnectionTestResult(
                success=True,
                latency_ms=latency,
                version="FusionCompute",
                details={
                    "clusters": len(clusters),
                    "token_valid": bool(self._token),
                },
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                latency_ms=0,
                version="",
                details={},
                error=str(e),
            )
    
    async def list_vms(self) -> list[DeviceInfo]:
        """列出所有虚拟机"""
        response = await self._client.get("/vms")
        response.raise_for_status()
        vms_data = response.json().get("vms", [])
        
        vms = []
        for vm in vms_data:
            vms.append(DeviceInfo(
                id=vm.get("vmId", ""),
                name=vm.get("name", ""),
                device_type="vm",
                status=vm.get("status", "unknown"),
                ip_address=vm.get("ip", ""),
                platform="FusionSphere",
                metadata={
                    "cpu": vm.get("cpuNum", 0),
                    "memory_mb": vm.get("memorySizeMB", 0),
                    "guest_os": vm.get("osType", ""),
                    "cluster": vm.get("clusterName", ""),
                },
            ))
        return vms
    
    async def power_on(self, vm_id: str) -> bool:
        """开机"""
        response = await self._client.post(f"/vms/{vm_id}/action/start")
        return response.status_code == 200
    
    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """关机"""
        action = "stop" if graceful else "force-stop"
        response = await self._client.post(f"/vms/{vm_id}/action/{action}")
        return response.status_code == 200
    
    async def create_snapshot(self, vm_id: str, name: str,
                              description: str = "") -> str:
        """创建快照"""
        response = await self._client.post(f"/vms/{vm_id}/snapshots", json={
            "name": name,
            "description": description,
        })
        response.raise_for_status()
        return response.json().get("snapshotId", "")
```

### 3.3 KVM/libvirt 适配器

```python
# backend/app/platforms/kvm/adapter.py
"""
KVM/QEMU (libvirt) 平台适配器

使用 libvirt-python 连接 KVM 主机，执行虚拟机管理操作。

依赖: libvirt-python >= 9.0
文档: https://libvirt.org/docs/libvirt-appdev-guide-python.html
"""

import libvirt

class KVMAdapter(PlatformAdapter):
    """KVM/libvirt 适配器"""
    
    platform_type = PlatformType.KVM
    
    def __init__(self):
        self._conn = None
        self._config = None
    
    async def connect(self, config: PlatformConfig) -> bool:
        """连接到 KVM 主机"""
        uri = f"qemu+ssh://{config.username}@{config.host}/system"
        if not config.verify_ssl:
            uri += "?no_verify=1"
        
        self._conn = libvirt.open(uri)
        if self._conn is None:
            raise ConnectionError(f"Failed to connect to {config.host}")
        
        self._config = config
        return True
    
    async def test_connection(self) -> ConnectionTestResult:
        """测试连接"""
        import time
        start = time.time()
        
        try:
            hostname = self._conn.getHostname()
            version = self._conn.getVersion()
            latency = int((time.time() - start) * 1000)
            
            # 获取主机信息
            node_info = self._conn.getInfo()
            
            return ConnectionTestResult(
                success=True,
                latency_ms=latency,
                version=f"libvirt {version}",
                details={
                    "hostname": hostname,
                    "cpu_model": node_info[0],
                    "cpu_cores": node_info[2],
                    "memory_mb": node_info[1],
                    "active_domains": self._conn.numOfDomains(),
                },
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                latency_ms=0,
                version="",
                details={},
                error=str(e),
            )
    
    async def list_vms(self) -> list[DeviceInfo]:
        """列出所有虚拟机"""
        domains = self._conn.listAllDomains()
        
        vms = []
        for dom in domains:
            # 获取 IP 地址 (从 DHCP lease 或 guest agent)
            ip_address = self._get_domain_ip(dom)
            
            vms.append(DeviceInfo(
                id=str(dom.UUIDString()),
                name=dom.name(),
                device_type="vm",
                status="running" if dom.isActive() else "stopped",
                ip_address=ip_address,
                platform="KVM",
                metadata={
                    "cpu": dom.maxVcpus(),
                    "memory_mb": dom.maxMemory() // 1024,
                    "os_type": dom.OSType(),
                    "autostart": dom.autostart(),
                },
            ))
        return vms
    
    async def power_on(self, vm_id: str) -> bool:
        """开机"""
        dom = self._conn.lookupByUUIDString(vm_id)
        dom.create()
        return True
    
    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """关机"""
        dom = self._conn.lookupByUUIDString(vm_id)
        if graceful:
            dom.shutdown()
        else:
            dom.destroy()
        return True
    
    async def create_snapshot(self, vm_id: str, name: str,
                              description: str = "") -> str:
        """创建快照"""
        dom = self._conn.lookupByUUIDString(vm_id)
        snapshot_xml = f"""
        <domainsnapshot>
            <name>{name}</name>
            <description>{description}</description>
        </domainsnapshot>
        """
        snapshot = dom.snapshotCreateXML(snapshot_xml)
        return snapshot.getName()
    
    async def migrate(self, vm_id: str, target_host: str = None,
                      target_storage: str = None) -> bool:
        """迁移虚拟机"""
        dom = self._conn.lookupByUUIDString(vm_id)
        
        if target_host:
            # 远程迁移
            uri = f"qemu+ssh://{self._config.username}@{target_host}/system"
            dest_conn = libvirt.open(uri)
            dom.migrate(dest_conn, libvirt.VIR_MIGRATE_LIVE)
            dest_conn.close()
        
        return True
```

---

## 4. 纳管 UI 设计

### 4.1 页面结构

```
设置 → 平台管理
├── 平台列表
│   ├── 卡片视图 (每个平台一张卡片)
│   │   ├── 平台图标 + 名称
│   │   ├── 连接状态 (在线/离线/测试中)
│   │   ├── 设备统计 (VM/主机/存储数量)
│   │   ├── 最后同步时间
│   │   └── 操作按钮 (编辑/测试/同步/删除)
│   └── 列表视图 (表格形式)
│
├── 添加平台向导
│   ├── 步骤 1: 选择平台类型
│   │   └── 平台卡片选择 (vSphere/FusionSphere/KVM/OpenStack/K8s)
│   ├── 步骤 2: 配置连接信息
│   │   ├── 主机地址 + 端口
│   │   ├── 认证方式 (用户名密码/Token/SSH密钥)
│   │   ├── SSL 验证选项
│   │   └── [测试连接] 按钮
│   ├── 步骤 3: 配置同步选项
│   │   ├── 自动同步间隔
│   │   ├── 同步范围 (全部/指定集群/指定资源池)
│   │   └── 设备过滤规则
│   └── 步骤 4: 确认并保存
│
├── 设备导入
│   ├── 从平台同步 (自动发现)
│   ├── CSV/Excel 导入
│   │   ├── 上传文件
│   │   ├── 字段映射
│   │   ├── 数据预览
│   │   └── 确认导入
│   └── 手动添加
│       ├── 设备类型选择
│       ├── 基本信息填写
│       └── 关联平台选择
│
└── 平台健康监控
    ├── 连接状态历史
    ├── API 响应时间图表
    ├── 同步状态
    └── 错误日志
```

### 4.2 前端组件

```typescript
// frontend/src/components/platforms/PlatformManager.tsx

interface Platform {
  id: string;
  name: string;
  type: 'vsphere' | 'fusionsphere' | 'kvm' | 'openstack' | 'kubernetes';
  host: string;
  port: number;
  status: 'connected' | 'disconnected' | 'testing' | 'error';
  device_count: {
    vms: number;
    hosts: number;
    storage: number;
  };
  last_sync: string;
  created_at: string;
}

interface PlatformTestResult {
  success: boolean;
  latency_ms: number;
  version: string;
  details: Record<string, any>;
  error?: string;
}

export function PlatformManager() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [showWizard, setShowWizard] = useState(false);
  const [showImport, setShowImport] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1>平台管理</h1>
        <div className="flex gap-2">
          <Button onClick={() => setShowImport(true)}>
            <Upload size={16} /> 导入设备
          </Button>
          <Button onClick={() => setShowWizard(true)}>
            <Plus size={16} /> 添加平台
          </Button>
        </div>
      </div>

      {/* Platform Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {platforms.map(platform => (
          <PlatformCard key={platform.id} platform={platform} />
        ))}
      </div>

      {/* Add Platform Wizard */}
      {showWizard && (
        <PlatformWizard onClose={() => setShowWizard(false)} />
      )}

      {/* Device Import Dialog */}
      {showImport && (
        <DeviceImportDialog onClose={() => setShowImport(false)} />
      )}
    </div>
  );
}

function PlatformCard({ platform }: { platform: Platform }) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<PlatformTestResult | null>(null);

  const handleTest = async () => {
    setTesting(true);
    try {
      const result = await testPlatformConnection(platform.id);
      setTestResult(result);
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card className="p-4">
      <div className="flex items-center gap-3 mb-3">
        <PlatformIcon type={platform.type} />
        <div>
          <h3 className="font-semibold">{platform.name}</h3>
          <p className="text-sm text-text-secondary">{platform.host}</p>
        </div>
        <StatusBadge status={platform.status} />
      </div>

      {/* Device Stats */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <StatItem label="VM" value={platform.device_count.vms} />
        <StatItem label="主机" value={platform.device_count.hosts} />
        <StatItem label="存储" value={platform.device_count.storage} />
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button size="sm" onClick={handleTest} disabled={testing}>
          {testing ? '测试中...' : '测试连接'}
        </Button>
        <Button size="sm" variant="secondary">编辑</Button>
        <Button size="sm" variant="secondary">同步</Button>
      </div>

      {/* Test Result */}
      {testResult && (
        <TestResultPanel result={testResult} />
      )}
    </Card>
  );
}
```

### 4.3 添加平台向导

```typescript
// frontend/src/components/platforms/PlatformWizard.tsx

const PLATFORM_TYPES = [
  {
    type: 'vsphere',
    name: 'VMware vSphere',
    icon: '🔵',
    description: 'vCenter / ESXi 主机',
    fields: ['host', 'port', 'username', 'password', 'verify_ssl'],
  },
  {
    type: 'fusionsphere',
    name: 'Huawei FusionSphere',
    icon: '🔴',
    description: 'FusionCompute 管理节点',
    fields: ['host', 'port', 'username', 'password'],
  },
  {
    type: 'kvm',
    name: 'KVM/QEMU (libvirt)',
    icon: '🟢',
    description: 'KVM 主机 (libvirt)',
    fields: ['host', 'username', 'ssh_key'],
  },
  {
    type: 'openstack',
    name: 'OpenStack',
    icon: '🟣',
    description: 'Keystone 认证',
    fields: ['auth_url', 'project', 'username', 'password', 'region'],
  },
];

export function PlatformWizard({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(1);
  const [platformType, setPlatformType] = useState<string>('');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<PlatformTestResult | null>(null);

  return (
    <Modal isOpen onClose={onClose} title="添加平台" size="lg">
      {/* Step Indicator */}
      <Steps current={step} total={4} />

      {step === 1 && (
        <PlatformTypeSelector onSelect={setPlatformType} />
      )}

      {step === 2 && (
        <PlatformConfigForm
          type={platformType}
          config={config}
          onChange={setConfig}
          onTest={handleTest}
          testResult={testResult}
        />
      )}

      {step === 3 && (
        <SyncOptionsForm
          config={config}
          onChange={setConfig}
        />
      )}

      {step === 4 && (
        <ConfirmAndSave
          type={platformType}
          config={config}
          onSave={handleSave}
        />
      )}
    </Modal>
  );
}
```

### 4.4 设备导入

```typescript
// frontend/src/components/platforms/DeviceImportDialog.tsx

export function DeviceImportDialog({ onClose }: { onClose: () => void }) {
  const [importMethod, setImportMethod] = useState<'sync' | 'csv' | 'manual'>('sync');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any[]>([]);

  return (
    <Modal isOpen onClose={onClose} title="导入设备" size="lg">
      {/* Import Method Selector */}
      <Tabs value={importMethod} onChange={setImportMethod}>
        <Tab value="sync">从平台同步</Tab>
        <Tab value="csv">CSV/Excel 导入</Tab>
        <Tab value="manual">手动添加</Tab>
      </Tabs>

      {importMethod === 'sync' && (
        <PlatformSyncPanel />
      )}

      {importMethod === 'csv' && (
        <CSVImportPanel
          file={file}
          onFileChange={setFile}
          preview={preview}
          onPreview={setPreview}
        />
      )}

      {importMethod === 'manual' && (
        <ManualAddPanel />
      )}
    </Modal>
  );
}

function CSVImportPanel({ file, onFileChange, preview, onPreview }) {
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    onFileChange(file);

    // Parse CSV and show preview
    const text = await file.text();
    const rows = parseCSV(text);
    onPreview(rows.slice(0, 10)); // Show first 10 rows
  };

  return (
    <div className="space-y-4">
      {/* File Upload */}
      <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
        <Upload size={32} className="mx-auto mb-2 text-text-secondary" />
        <p>拖拽文件到此处，或点击上传</p>
        <input type="file" accept=".csv,.xlsx" onChange={handleUpload} />
      </div>

      {/* Field Mapping */}
      {preview.length > 0 && (
        <>
          <h3>字段映射</h3>
          <FieldMapping
            sourceFields={Object.keys(preview[0])}
            targetFields={['name', 'ip_address', 'type', 'platform', 'cluster']}
          />

          <h3>数据预览</h3>
          <DataTable data={preview} />
        </>
      )}
    </div>
  );
}
```

---

## 5. 跨平台迁移方案

### 5.1 迁移场景矩阵

| 源平台 | 目标平台 | 工具 | 复杂度 | 风险 |
|--------|----------|------|--------|------|
| VMware | KVM | virt-v2v / qemu-img | 中 | 驱动兼容 |
| VMware | OpenStack | Glance Import / OVF | 中 | 网络配置 |
| VMware | FusionSphere | 华为迁移工具 | 高 | 兼容性 |
| KVM | VMware | qemu-img / StarWind | 中 | 磁盘格式 |
| OpenStack | VMware | OVF Export / Veeam | 高 | 存储迁移 |

### 5.2 迁移工作流

```python
# backend/app/services/migration_service.py

class MigrationService:
    """跨平台虚拟机迁移服务"""
    
    async def plan_migration(self, vm_id: str, source_platform: str,
                             target_platform: str) -> MigrationPlan:
        """规划迁移方案"""
        
        # 1. 获取源 VM 信息
        source_vm = await self._get_vm_info(vm_id, source_platform)
        
        # 2. 分析兼容性
        compatibility = self._analyze_compatibility(
            source_vm, source_platform, target_platform
        )
        
        # 3. 选择迁移工具
        migration_tool = self._select_migration_tool(
            source_platform, target_platform, source_vm
        )
        
        # 4. 生成迁移计划
        return MigrationPlan(
            source_vm=source_vm,
            target_platform=target_platform,
            tool=migration_tool,
            steps=self._generate_steps(source_vm, migration_tool),
            estimated_time=self._estimate_time(source_vm, migration_tool),
            risks=compatibility.risks,
            prerequisites=compatibility.prerequisites,
        )
    
    def _select_migration_tool(self, source: str, target: str,
                               vm_info: dict) -> MigrationTool:
        """选择最佳迁移工具"""
        
        if source == "vsphere" and target == "kvm":
            # virt-v2v: 最成熟的 VMware → KVM 迁移工具
            return MigrationTool(
                name="virt-v2v",
                command="virt-v2v -i vmx -it vddk vm://...",
                description="Red Hat 官方工具，支持驱动注入",
            )
        
        elif source == "vsphere" and target == "openstack":
            # OVF 导入到 Glance
            return MigrationTool(
                name="ovf-import",
                command="openstack image create --import ...",
                description="通过 OVF 格式导入到 OpenStack Glance",
            )
        
        elif source == "kvm" and target == "vsphere":
            # qemu-img 转换 + StarWind V2V
            return MigrationTool(
                name="qemu-img + StarWind",
                command="qemu-img convert -f qcow2 -O vmdk ...",
                description="磁盘格式转换后导入 vSphere",
            )
```

### 5.3 迁移 UI

```typescript
// frontend/src/components/migration/MigrationWizard.tsx

export function MigrationWizard() {
  const [sourceVm, setSourceVm] = useState<string>('');
  const [targetPlatform, setTargetPlatform] = useState<string>('');
  const [migrationPlan, setMigrationPlan] = useState<MigrationPlan | null>(null);

  return (
    <div className="space-y-6">
      <h1>跨平台迁移</h1>

      {/* Source Selection */}
      <Card>
        <h3>选择源虚拟机</h3>
        <VMSelector value={sourceVm} onChange={setSourceVm} />
      </Card>

      {/* Target Selection */}
      <Card>
        <h3>选择目标平台</h3>
        <PlatformSelector
          value={targetPlatform}
          onChange={setTargetPlatform}
          exclude={sourceVm ? [getSourcePlatform(sourceVm)] : []}
        />
      </Card>

      {/* Migration Plan */}
      {sourceVm && targetPlatform && (
        <MigrationPlanPanel
          sourceVm={sourceVm}
          targetPlatform={targetPlatform}
          plan={migrationPlan}
          onPlanGenerated={setMigrationPlan}
        />
      )}

      {/* Execute */}
      {migrationPlan && (
        <MigrationExecutionPanel plan={migrationPlan} />
      )}
    </div>
  );
}

function MigrationPlanPanel({ sourceVm, targetPlatform, plan, onPlanGenerated }) {
  useEffect(() => {
    // Fetch migration plan from backend
    fetchMigrationPlan(sourceVm, targetPlatform).then(onPlanGenerated);
  }, [sourceVm, targetPlatform]);

  if (!plan) return <Skeleton />;

  return (
    <Card>
      <h3>迁移计划</h3>
      
      {/* Tool Info */}
      <div className="mb-4 p-3 bg-bg-tertiary rounded-lg">
        <h4>迁移工具: {plan.tool.name}</h4>
        <p className="text-sm text-text-secondary">{plan.tool.description}</p>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {plan.steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3 p-2">
            <span className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center">
              {i + 1}
            </span>
            <span>{step.description}</span>
            <span className="text-xs text-text-secondary ml-auto">
              ~{step.estimated_seconds}s
            </span>
          </div>
        ))}
      </div>

      {/* Risks */}
      {plan.risks.length > 0 && (
        <div className="mt-4 p-3 bg-warning/10 rounded-lg">
          <h4 className="text-warning">⚠️ 风险提示</h4>
          <ul className="text-sm text-text-secondary">
            {plan.risks.map((risk, i) => (
              <li key={i}>• {risk}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        <Button onClick={handleDryRun}>模拟运行</Button>
        <Button variant="danger" onClick={handleExecute}>开始迁移</Button>
      </div>
    </Card>
  );
}
```

---

## 6. 软件版本优化

### 6.1 版本推荐

| 软件 | 当前版本 | 推荐版本 | 理由 |
|------|----------|----------|------|
| Python | 3.12 | **3.14** | 性能提升 10-15%，更好的 async 支持，PEP 703 (no-GIL) 预览 |
| Node.js | 20 LTS | **22 LTS** | 性能提升，更好的 ESM 支持，长期支持到 2027 |
| PostgreSQL | 16 | **17** | 查询性能提升 2x，JSONB 改进，逻辑复制增强 |
| Redis | 7.0 | **7.4** | 性能优化，新的数据类型，更好的集群支持 |
| FastAPI | 0.115 | **0.115+** | 保持最新，OpenAPI 3.1 支持 |
| SQLAlchemy | 2.0.30 | **2.0.35+** | Bug 修复，性能优化 |
| React | 18.3 | **18.3** | 保持 18.x 稳定版，等待 19.x 成熟 |
| Docker | 24 | **27** | Build 性能提升，安全增强 |

### 6.2 升级计划

```yaml
# 推荐的版本升级顺序
Phase 1 (低风险):
  - Python: 3.12 → 3.14 (语法兼容，性能提升)
  - Node.js: 20 → 22 LTS (稳定升级)
  - Redis: 7.0 → 7.4 (向后兼容)

Phase 2 (中风险):
  - PostgreSQL: 16 → 17 (需要迁移测试)
  - Docker: 24 → 27 (需要验证 Compose 兼容性)

Phase 3 (高风险):
  - SQLAlchemy: 2.0 → 2.1 (API 变化)
  - React: 18 → 19 (等待生态成熟)
```

---

## 7. 实施路线图

| 阶段 | 内容 | 预计时间 | 优先级 |
|------|------|----------|--------|
| **P1: vSphere 适配器** | 实现真实 vSphere API 集成 | 2 周 | P0 |
| **P2: 纳管 UI** | 平台添加/测试/同步界面 | 2 周 | P0 |
| **P3: FusionSphere 适配器** | 实现 FusionCompute API | 2 周 | P0 |
| **P4: KVM 适配器** | 实现 libvirt 集成 | 1 周 | P0 |
| **P5: 设备导入** | CSV 导入 + 平台同步 | 1 周 | P1 |
| **P6: 迁移工具** | VMware → KVM 迁移 | 2 周 | P1 |
| **P7: 版本升级** | Python 3.14 + PostgreSQL 17 | 1 周 | P2 |
| **P8: 迁移 UI** | 跨平台迁移向导 | 1 周 | P1 |

**总计**: 12 周

---

> 本文档为 V3.1 平台纳管与迁移的实施方案。
> 研究 agent 完成后会补充最新的 API/SDK 信息。
