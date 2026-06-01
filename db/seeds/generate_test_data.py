#!/usr/bin/env python3
"""V3.1 SRE Platform — Realistic test data generator.

Generates seed data for development and testing:
- 5 platform connections (2 vCenters, 1 OpenStack, 1 K8s, 1 storage)
- 100 VMs across 5 clusters
- 20 physical hosts
- 10 storage devices
- 5 network devices
- Asset relationships (host->VM, VM->datastore)
- 50 alerts (mixed severity/status)
- 20 operations (mixed type/status) with steps
- 100 audit log entries
- Asset metrics (CPU, memory, disk) for the last 24 hours
- 3 skill definitions
- 5 AI conversations

Usage:
    python generate_test_data.py                     # Print SQL to stdout
    python generate_test_data.py --output seed.sql   # Write to file
    python generate_test_data.py --execute           # Execute directly via psycopg2
    python generate_test_data.py --execute --dsn "postgresql://user:pass@host:5432/db"
"""
from __future__ import annotations

import argparse
import uuid
import random
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import TextIO

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CLUSTER_NAMES = [
    "cluster-prod-east-01",
    "cluster-prod-west-01",
    "cluster-staging-01",
    "cluster-dev-01",
    "cluster-dr-01",
]

DATACENTERS = ["dc-east", "dc-west", "dc-dr"]

HOST_PREFIXES = {
    "dc-east": "esxi-east",
    "dc-west": "esxi-west",
    "dc-dr": "esxi-dr",
}

VM_PREFIXES = [
    "web", "api", "db", "cache", "mq", "worker", "monitor", "log",
    "auth", "gateway", "scheduler", "backup", "dns", "proxy", "app",
]

OS_TYPES = ["linux", "windows"]
LINUX_DISTROS = ["Ubuntu 22.04", "CentOS 8", "RHEL 9", "Debian 12", "Rocky 9"]
WINDOWS_VERSIONS = ["Windows Server 2022", "Windows Server 2019"]

STORAGE_NAMES = [
    "PURE-FlashArray-01", "PURE-FlashArray-02", "NetApp-FAS-01",
    "NetApp-AFF-01", "Dell-PowerStore-01", "HPE-Nimble-01",
    "IBM-FlashSystem-01", "Hitachi-VSP-01", "Huawei-OceanStor-01",
    "Lenovo-DE-01",
]

NETWORK_NAMES = [
    "nexus-core-01", "nexus-core-02", "arista-spine-01", "juniper-fw-01", "cisco-lb-01",
]

METRIC_NAMES = ["cpu_usage_pct", "memory_usage_pct", "disk_usage_pct", "disk_read_mbps", "disk_write_mbps", "network_in_mbps", "network_out_mbps"]

SEVERITY_DIST = {"critical": 5, "high": 12, "medium": 18, "low": 10, "info": 5}
ALERT_SOURCES = ["prometheus", "grafana", "vcenter", "manual"]

# Pre-generated UUIDs for deterministic output
_user_ids: list[uuid.UUID] = []
_platform_ids: list[uuid.UUID] = []
_asset_ids: list[uuid.UUID] = []

random.seed(42)  # Deterministic for reproducibility


def new_id() -> uuid.UUID:
    return uuid.uuid4()


def rand_ip(cluster_idx: int, host_idx: int) -> str:
    return f"10.{cluster_idx + 1}.{host_idx + 1}.{random.randint(1, 254)}"


def rand_mac() -> str:
    return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))


def rand_past(days: int = 30) -> datetime:
    return datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def rand_recent(hours: int = 24) -> datetime:
    return datetime.now(timezone.utc) - timedelta(
        hours=random.randint(0, hours),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )


def esc(s: str) -> str:
    """Escape single quotes for SQL."""
    return s.replace("'", "''")


def jsonb(d: dict | list) -> str:
    """Convert dict/list to SQL JSONB literal."""
    return "'" + json.dumps(d, default=str).replace("'", "''") + "'::jsonb"


def array_pg(items: list[str], elem_type: str = "text") -> str:
    """Format as PostgreSQL array literal."""
    quoted = ", ".join(f"'{esc(i)}'" for i in items)
    return f"ARRAY[{quoted}]::{elem_type}[]"


def uuid_array(ids: list[uuid.UUID]) -> str:
    quoted = ", ".join(f"'{i}'" for i in ids)
    return f"ARRAY[{quoted}]::uuid[]"


# ---------------------------------------------------------------------------
# SQL Generation
# ---------------------------------------------------------------------------

def gen_users(out: TextIO) -> list[uuid.UUID]:
    """Generate 5 users (admin, 2 operators, viewer, ai_agent)."""
    users = [
        ("admin", "admin@sre-platform.local", "System Admin", "admin", True),
        ("operator1", "op1@sre-platform.local", "Zhang Wei", "operator", True),
        ("operator2", "op2@sre-platform.local", "Li Ming", "operator", True),
        ("viewer1", "viewer@sre-platform.local", "Wang Fang", "viewer", True),
        ("ai-agent", "ai@sre-platform.local", "SRE AI Agent", "ai_agent", True),
    ]
    out.write("-- ===== Users =====\n")
    out.write("INSERT INTO users (id, username, email, display_name, role, is_active) VALUES\n")
    rows = []
    ids = []
    for username, email, display, role, active in users:
        uid = new_id()
        ids.append(uid)
        rows.append(
            f"('{uid}', '{esc(username)}', '{esc(email)}', '{esc(display)}', "
            f"'{role}', {str(active).upper()})"
        )
    out.write(",\n".join(rows) + ";\n\n")
    return ids


def gen_platforms(out: TextIO, created_by: uuid.UUID) -> list[uuid.UUID]:
    """Generate 5 platform connections."""
    platforms = [
        ("Prod vCenter East", "vmware_vsphere", "https://vcenter-east.corp.local/sdk"),
        ("Prod vCenter West", "vmware_vsphere", "https://vcenter-west.corp.local/sdk"),
        ("Prod OpenStack", "openstack", "https://openstack.corp.local:5000/v3"),
        ("Prod Kubernetes", "kubernetes", "https://k8s-api.corp.local:6443"),
        ("Storage Array Farm", "storage_array", "https://storage-mgmt.corp.local/api"),
    ]
    out.write("-- ===== Platforms =====\n")
    out.write("INSERT INTO platforms (id, name, platform_type, endpoint, config, is_active, created_by) VALUES\n")
    rows = []
    ids = []
    for name, ptype, endpoint in platforms:
        pid = new_id()
        ids.append(pid)
        config = jsonb({"verify_ssl": False, "timeout": 30})
        rows.append(
            f"('{pid}', '{esc(name)}', '{ptype}', '{esc(endpoint)}', "
            f"{config}, TRUE, '{created_by}')"
        )
    out.write(",\n".join(rows) + ";\n\n")
    return ids


def gen_assets(out: TextIO, platform_ids: list[uuid.UUID]) -> tuple[list[uuid.UUID], list[uuid.UUID], list[uuid.UUID]]:
    """Generate 135 assets: 100 VMs, 20 hosts, 10 storage, 5 network."""
    out.write("-- ===== Assets =====\n")
    out.write("INSERT INTO assets (id, external_id, name, asset_type, platform_id, platform_type, status, "
              "ip_addresses, mac_addresses, cluster_name, datacenter, cpu_cores, memory_mb, disk_gb, "
              "os_type, os_version, metadata) VALUES\n")

    rows = []
    vm_ids = []
    host_ids = []
    storage_ids = []

    # -- 20 Physical Hosts --
    host_idx = 0
    for dc_idx, dc in enumerate(DATACENTERS):
        prefix = HOST_PREFIXES[dc]
        hosts_in_dc = 8 if dc != "dc-dr" else 4
        for i in range(hosts_in_dc):
            hid = new_id()
            host_ids.append(hid)
            name = f"{prefix}-{i + 1:03d}"
            cluster = CLUSTER_NAMES[dc_idx if dc_idx < len(CLUSTER_NAMES) else 0]
            ip = rand_ip(dc_idx, i + 100)
            cpu = random.choice([32, 48, 64, 96, 128])
            mem = random.choice([256, 512, 768, 1024]) * 1024  # in MB
            disk = random.choice([2000, 4000, 8000, 16000])
            ext_id = f"host-{random.randint(10000, 99999)}"
            meta = jsonb({
                "vendor": random.choice(["Dell", "HPE", "Lenovo", "Inspur"]),
                "model": f"PowerEdge R{random.choice([650, 750, 760])}",
                "serial": f"SN{random.randint(100000, 999999)}",
            })
            rows.append(
                f"('{hid}', '{esc(ext_id)}', '{esc(name)}', 'physical_host', "
                f"'{platform_ids[0]}', 'physical', "
                f"'active', ARRAY['{ip}']::text[], ARRAY['{rand_mac()}']::text[], "
                f"'{esc(cluster)}', '{dc}', {cpu}, {mem}, {disk}, "
                f"'linux', 'ESXi 8.0', {meta})"
            )
            host_idx += 1

    # -- 100 VMs --
    for vm_i in range(100):
        vid = new_id()
        vm_ids.append(vid)
        cluster_idx = vm_i % len(CLUSTER_NAMES)
        cluster = CLUSTER_NAMES[cluster_idx]
        dc = DATACENTERS[cluster_idx % len(DATACENTERS)]
        prefix = random.choice(VM_PREFIXES)
        name = f"{prefix}-{cluster_idx}-{vm_i:03d}"
        ext_id = f"vm-{random.randint(100000, 999999)}"

        os_type = random.choice(OS_TYPES)
        if os_type == "linux":
            os_ver = random.choice(LINUX_DISTROS)
        else:
            os_ver = random.choice(WINDOWS_VERSIONS)

        cpu = random.choice([2, 4, 8, 16, 32])
        mem = random.choice([4, 8, 16, 32, 64]) * 1024
        disk = random.choice([50, 100, 200, 500, 1000])
        ip = rand_ip(cluster_idx, vm_i)
        status = random.choices(
            ["active", "active", "active", "active", "maintenance", "decommissioned", "error"],
            weights=[70, 10, 5, 5, 5, 3, 2],
        )[0]

        # Pick the platform for this cluster
        if cluster_idx < 2:
            plat_id = platform_ids[0] if cluster_idx == 0 else platform_ids[1]
            plat_type = "vmware_vsphere"
        elif cluster_idx == 2:
            plat_id = platform_ids[2]
            plat_type = "openstack"
        else:
            plat_id = platform_ids[3]
            plat_type = "kubernetes"

        meta = jsonb({
            "annotation": f"VM for {prefix} workload",
            "tags": [cluster, dc, prefix],
        })
        rows.append(
            f"('{vid}', '{esc(ext_id)}', '{esc(name)}', 'vm', "
            f"'{plat_id}', '{plat_type}', "
            f"'{status}', ARRAY['{ip}']::text[], ARRAY['{rand_mac()}']::text[], "
            f"'{esc(cluster)}', '{dc}', {cpu}, {mem}, {disk}, "
            f"'{os_type}', '{esc(os_ver)}', {meta})"
        )

    # -- 10 Storage Devices --
    for si, sname in enumerate(STORAGE_NAMES):
        sid = new_id()
        storage_ids.append(sid)
        ext_id = f"storage-{random.randint(1000, 9999)}"
        ip = f"10.100.{si + 1}.1"
        total_tb = random.choice([50, 100, 200, 500])
        meta = jsonb({
            "vendor": sname.split("-")[0],
            "total_tb": total_tb,
            "protocol": random.choice(["FC", "iSCSI", "NFS"]),
        })
        rows.append(
            f"('{sid}', '{esc(ext_id)}', '{esc(sname)}', 'storage_device', "
            f"'{platform_ids[4]}', 'storage_array', "
            f"'active', ARRAY['{ip}']::text[], ARRAY[]::text[], "
            f"NULL, 'dc-east', NULL, NULL, {total_tb * 1024}, "
            f"'other', 'StorageOS 3.0', {meta})"
        )

    # -- 5 Network Devices --
    for ni, nname in enumerate(NETWORK_NAMES):
        nid = new_id()
        ext_id = f"net-{random.randint(1000, 9999)}"
        ip = f"10.200.{ni + 1}.1"
        meta = jsonb({"ports": random.choice([24, 48, 96]), "role": "core" if ni < 2 else "access"})
        rows.append(
            f"('{nid}', '{esc(ext_id)}', '{esc(nname)}', 'network_device', "
            f"NULL, 'network', "
            f"'active', ARRAY['{ip}']::text[], ARRAY[]::text[], "
            f"NULL, '{random.choice(DATACENTERS)}', NULL, NULL, NULL, "
            f"'other', 'NX-OS 10.2', {meta})"
        )

    out.write(",\n".join(rows) + ";\n\n")
    return vm_ids, host_ids, storage_ids


def gen_asset_relations(out: TextIO, vm_ids: list[uuid.UUID], host_ids: list[uuid.UUID],
                        storage_ids: list[uuid.UUID]) -> None:
    """Generate host->VM and VM->datastore relationships."""
    out.write("-- ===== Asset Relations =====\n")
    out.write("INSERT INTO asset_relations (source_asset_id, target_asset_id, relation_type) VALUES\n")
    rows = []

    # Each VM runs on a random host
    for vid in vm_ids:
        hid = random.choice(host_ids)
        rows.append(f"('{vid}', '{hid}', 'runs_on')")

    # Each VM uses a random storage device
    for vid in vm_ids:
        sid = random.choice(storage_ids)
        rows.append(f"('{vid}', '{sid}', 'uses')")

    out.write(",\n".join(rows) + ";\n\n")


def gen_alerts(out: TextIO, asset_ids: list[uuid.UUID], user_ids: list[uuid.UUID]) -> None:
    """Generate 50 alerts with mixed severity/status."""
    out.write("-- ===== Alerts =====\n")

    alert_templates = [
        ("critical", "Host CPU usage above 95%", "CPU usage on {name} is {val}%"),
        ("critical", "Host memory exhausted", "Available memory on {name} below 5%"),
        ("high", "Disk usage above 90%", "Disk usage on {name} is {val}%"),
        ("high", "Host connection lost", "Cannot reach {name} for 5 minutes"),
        ("medium", "CPU usage above 80%", "CPU usage on {name} is {val}%"),
        ("medium", "Memory usage above 85%", "Memory usage on {name} is {val}%"),
        ("medium", "Network latency high", "Ping to {name} is {val}ms"),
        ("low", "Certificate expiring soon", "TLS cert on {name} expires in 30 days"),
        ("low", "Disk usage above 70%", "Disk usage on {name} is {val}%"),
        ("info", "VM snapshot older than 7 days", "Snapshot on {name} is {val} days old"),
    ]

    rows = []
    for i in range(50):
        aid = new_id()
        severity, title_tpl, desc_tpl = random.choice(alert_templates)
        asset_id = random.choice(asset_ids) if asset_ids else None
        source = random.choice(ALERT_SOURCES)
        ext_id = f"alert-{random.randint(10000, 99999)}"

        status = random.choices(
            ["firing", "acknowledged", "resolved", "silenced"],
            weights=[40, 20, 30, 10],
        )[0]

        firing_at = rand_past(30)
        ack_at = None
        ack_by = None
        resolved_at = None
        resolved_by = None

        if status in ("acknowledged", "resolved", "silenced"):
            ack_at = (firing_at + timedelta(minutes=random.randint(5, 120))).isoformat()
            ack_by = random.choice(user_ids[:3])  # operators/admin
        if status == "resolved":
            resolved_at = (firing_at + timedelta(hours=random.randint(1, 24))).isoformat()
            resolved_by = random.choice(user_ids[:3])

        val = round(random.uniform(50, 99), 1)
        title = title_tpl
        desc = desc_tpl.format(name=f"asset-{i}", val=val)

        labels = jsonb({"severity": severity, "instance": f"10.1.{i}.1:9100"})
        annotations = jsonb({"description": desc, "runbook": f"https://wiki/runbook/{i}"})

        def nullable(v):
            return 'NULL' if v is None else f"'{v}'"

        rows.append(
            f"('{aid}', '{esc(ext_id)}', '{esc(source)}', '{esc(title)}', "
            f"'{esc(desc)}', '{severity}', '{status}', "
            f"{nullable(asset_id)}, "
            f"'asset-{i}', 'vm', "
            f"{labels}, {annotations}, {val}, {val - 10}, "
            f"'{firing_at.isoformat()}', "
            f"{nullable(ack_at)}, "
            f"{nullable(ack_by)}, "
            f"{nullable(resolved_at)}, "
            f"{nullable(resolved_by)}, "
            f"'{firing_at.isoformat()}')"
        )

    out.write("INSERT INTO alerts (id, external_id, source, title, description, severity, status, "
              "asset_id, resource_name, resource_type, labels, annotations, value, threshold, "
              "firing_at, acknowledged_at, acknowledged_by, resolved_at, resolved_by, created_at) VALUES\n")
    out.write(",\n".join(rows) + ";\n\n")


def gen_operations(out: TextIO, user_ids: list[uuid.UUID], platform_ids: list[uuid.UUID]) -> None:
    """Generate 20 operations with steps."""
    out.write("-- ===== Operations =====\n")

    op_types = ["inspection", "change_request", "incident", "maintenance", "remediation", "audit"]
    risk_levels = ["critical", "high", "medium", "low", "none"]
    statuses = ["draft", "pending_approval", "approved", "executing", "completed", "failed", "cancelled"]

    op_rows = []
    step_rows = []
    op_ids = []

    for i in range(20):
        oid = new_id()
        op_ids.append(oid)
        op_type = random.choice(op_types)
        risk = random.choice(risk_levels)
        status = random.choice(statuses)

        titles = {
            "inspection": f"Scheduled health inspection #{i + 1}",
            "change_request": f"Firmware upgrade batch #{i + 1}",
            "incident": f"Incident response: service degradation #{i + 1}",
            "maintenance": f"Planned maintenance window #{i + 1}",
            "remediation": f"Auto-remediation: disk cleanup #{i + 1}",
            "audit": f"Compliance audit check #{i + 1}",
        }
        title = titles[op_type]
        created_by = random.choice(user_ids[:3])
        plat_id = random.choice(platform_ids)

        created_at = rand_past(60)
        started_at = None
        completed_at = None
        if status in ("executing", "completed", "failed"):
            started_at = (created_at + timedelta(hours=random.randint(1, 24))).isoformat()
        if status in ("completed", "failed"):
            completed_at = (
                datetime.fromisoformat(started_at) + timedelta(hours=random.randint(1, 8))
            ).isoformat() if started_at else None

        params = jsonb({"target_count": random.randint(1, 20), "dry_run": random.choice([True, False])})
        result = jsonb({"success_count": random.randint(0, 20), "error_count": random.randint(0, 3)}) if status == "completed" else jsonb({})

        def nullable(v):
            return 'NULL' if v is None else f"'{v}'"

        scheduled_at = None
        if random.random() < 0.3:
            scheduled_at = (created_at + timedelta(days=random.randint(1, 7))).isoformat()

        error_msg = "'Error: timeout after 300s'" if status == 'failed' else 'NULL'
        op_rows.append(
            f"('{oid}', '{esc(title)}', '{esc(f'Description for {op_type} operation {i + 1}')}', "
            f"'{op_type}', '{risk}', '{status}', "
            f"{uuid_array([])}, '{plat_id}', NULL, "
            f"{params}, {result}, "
            f"{error_msg}, "
            f"{nullable(started_at)}, "
            f"{nullable(scheduled_at)}, "
            f"{nullable(completed_at)}, "
            f"'{created_by}', NULL, NULL, NULL, "
            f"'{created_at.isoformat()}')"
        )

        # Generate 2-5 steps per operation
        num_steps = random.randint(2, 5)
        for si in range(num_steps):
            step_id = new_id()
            step_status = "pending"
            if status == "completed":
                step_status = "completed"
            elif status == "failed":
                step_status = "completed" if si < num_steps - 1 else "failed"
            elif status == "executing":
                step_status = "completed" if si < num_steps - 1 else "running"

            step_names = {
                "inspection": ["Connect to platform", "Collect metrics", "Analyze results", "Generate report"],
                "change_request": ["Validate pre-conditions", "Execute change", "Verify post-conditions", "Update CMDB"],
                "incident": ["Assess impact", "Apply workaround", "Root cause analysis", "Permanent fix"],
                "maintenance": ["Notify stakeholders", "Enable maintenance mode", "Perform maintenance", "Verify health"],
                "remediation": ["Diagnose issue", "Apply remediation", "Verify fix", "Update runbook"],
                "audit": ["Collect evidence", "Check compliance", "Generate findings", "File report"],
            }
            sname = step_names.get(op_type, [f"Step {j + 1}" for j in range(4)])[si % 4]
            cmd = f"sre-cli {op_type} --step {si + 1} --target batch-{i}"

            def step_nullable(v):
                return 'NULL' if v is None else f"'{v}'"

            step_output = None if step_status == 'pending' else f"Step {si + 1} output OK"
            step_error = None if step_status != 'failed' else "Step failed: timeout"
            step_started = None if step_status == 'pending' else rand_recent(48).isoformat()
            step_completed = None if step_status in ('pending', 'running') else rand_recent(24).isoformat()
            step_duration = None if step_status == 'pending' else random.randint(100, 30000)

            step_rows.append(
                f"('{step_id}', '{oid}', {si + 1}, '{esc(sname)}', "
                f"'Execute {esc(sname)} for operation {i + 1}', '{step_status}', "
                f"'{esc(cmd)}', "
                f"{step_nullable(step_output)}, "
                f"{step_nullable(step_error)}, "
                f"{step_nullable(step_started)}, "
                f"{step_nullable(step_completed)}, "
                f"{'NULL' if step_duration is None else step_duration}, "
                f"{jsonb({})})"
            )

    out.write("INSERT INTO operations (id, title, description, operation_type, risk_level, status, "
              "target_assets, platform_id, skill_id, parameters, result, error_message, "
              "started_at, scheduled_at, completed_at, created_by, approved_by, approved_at, "
              "conversation_id, created_at) VALUES\n")
    out.write(",\n".join(op_rows) + ";\n\n")

    out.write("-- ===== Operation Steps =====\n")
    out.write("INSERT INTO operation_steps (id, operation_id, step_number, name, description, status, "
              "command, output, error_output, started_at, completed_at, duration_ms, metadata) VALUES\n")
    out.write(",\n".join(step_rows) + ";\n\n")


def gen_audit_logs(out: TextIO, user_ids: list[uuid.UUID], asset_ids: list[uuid.UUID]) -> None:
    """Generate 100 audit log entries."""
    out.write("-- ===== Audit Logs =====\n")

    actions = ["create", "read", "update", "delete", "execute", "login", "logout", "export", "approve"]
    resource_types = ["asset", "alert", "operation", "user", "platform", "skill"]

    rows = []
    for i in range(100):
        alid = new_id()
        uid = random.choice(user_ids)
        action = random.choice(actions)
        res_type = random.choice(resource_types)
        res_id = random.choice(asset_ids) if res_type == "asset" else None
        success = random.random() > 0.05  # 95% success rate

        created_at = rand_past(30)
        old_vals = None
        new_vals = None
        if action == "update":
            old_vals = jsonb({"status": "active"})
            new_vals = jsonb({"status": "maintenance"})
        elif action == "create":
            new_vals = jsonb({"name": f"new-{res_type}-{i}"})

        def audit_nullable(v):
            return 'NULL' if v is None else f"'{v}'"

        error_msg = "'Permission denied'" if not success else 'NULL'
        rows.append(
            f"('{alid}', '{uid}', NULL, '{action}', '{res_type}', "
            f"{audit_nullable(res_id)}, "
            f"'{res_type}-{i}', "
            f"{old_vals if old_vals else 'NULL'}, "
            f"{new_vals if new_vals else 'NULL'}, "
            f"'{rand_ip(0, i % 254)}'::inet, 'Mozilla/5.0 SRE-Client/1.0', "
            f"'{new_id()}', "
            f"{'TRUE' if success else 'FALSE'}, "
            f"{error_msg}, "
            f"{random.randint(1, 5000)}, "
            f"'{created_at.isoformat()}')"
        )

    out.write("INSERT INTO audit_logs (id, user_id, username, action, resource_type, resource_id, "
              "resource_name, old_values, new_values, ip_address, user_agent, request_id, "
              "success, error_message, duration_ms, created_at) VALUES\n")
    out.write(",\n".join(rows) + ";\n\n")


def gen_asset_metrics(out: TextIO, asset_ids: list[uuid.UUID]) -> None:
    """Generate 24 hours of metrics for a subset of assets (5 assets x 7 metrics x 24 points)."""
    out.write("-- ===== Asset Metrics (sample: 5 assets, last 24h) =====\n")

    sample_assets = random.sample(asset_ids[:100], min(5, len(asset_ids)))
    rows = []
    now = datetime.now(timezone.utc)

    for asset_id in sample_assets:
        base_cpu = random.uniform(20, 80)
        base_mem = random.uniform(30, 90)
        base_disk = random.uniform(40, 85)

        for hour in range(24):
            ts = now - timedelta(hours=23 - hour, minutes=random.randint(0, 59))

            metrics = {
                "cpu_usage_pct": (base_cpu + random.uniform(-15, 15), "%"),
                "memory_usage_pct": (base_mem + random.uniform(-5, 5), "%"),
                "disk_usage_pct": (base_disk + random.uniform(-2, 2), "%"),
                "disk_read_mbps": (random.uniform(10, 500), "MBps"),
                "disk_write_mbps": (random.uniform(5, 300), "MBps"),
                "network_in_mbps": (random.uniform(100, 2000), "Mbps"),
                "network_out_mbps": (random.uniform(50, 1500), "Mbps"),
            }

            for mname, (mval, munit) in metrics.items():
                mid = new_id()
                mval = max(0, round(mval, 2))
                rows.append(
                    f"('{mid}', '{asset_id}', '{mname}', {mval}, '{munit}', "
                    f"{jsonb({})}, '{ts.isoformat()}')"
                )

    out.write("INSERT INTO asset_metrics (id, asset_id, metric_name, value, unit, labels, recorded_at) VALUES\n")
    out.write(",\n".join(rows) + ";\n\n")


def gen_skills(out: TextIO, user_ids: list[uuid.UUID]) -> None:
    """Generate 3 sample skill definitions."""
    out.write("-- ===== Skills =====\n")

    skills = [
        {
            "name": "vm-health-inspection",
            "display_name": "VM Health Inspection",
            "description": "Comprehensive health check for virtual machines",
            "category": "inspection",
            "yaml": (
                "name: vm-health-inspection\n"
                "version: 1.0.0\n"
                "steps:\n"
                "  - name: check_cpu\n"
                "    command: check_cpu_usage\n"
                "    threshold: 90\n"
                "  - name: check_memory\n"
                "    command: check_memory_usage\n"
                "    threshold: 85\n"
                "  - name: check_disk\n"
                "    command: check_disk_usage\n"
                "    threshold: 80\n"
            ),
            "risk": "low",
            "platforms": ["vmware_vsphere", "openstack"],
        },
        {
            "name": "disk-cleanup-remediation",
            "display_name": "Disk Cleanup Remediation",
            "description": "Automated disk cleanup when usage exceeds threshold",
            "category": "remediation",
            "yaml": (
                "name: disk-cleanup-remediation\n"
                "version: 1.0.0\n"
                "requires_approval: true\n"
                "steps:\n"
                "  - name: identify_large_files\n"
                "    command: find_large_files\n"
                "  - name: clean_temp\n"
                "    command: rm -rf /tmp/sre-*\n"
                "  - name: rotate_logs\n"
                "    command: logrotate -f /etc/logrotate.d/app\n"
                "rollback:\n"
                "  - name: restore_files\n"
                "    command: restore_from_backup\n"
            ),
            "risk": "medium",
            "platforms": ["vmware_vsphere", "openstack", "kubernetes"],
        },
        {
            "name": "compliance-audit-check",
            "display_name": "Compliance Audit Check",
            "description": "Verify infrastructure compliance against security baseline",
            "category": "audit",
            "yaml": (
                "name: compliance-audit-check\n"
                "version: 1.0.0\n"
                "steps:\n"
                "  - name: check_firewall_rules\n"
                "    command: verify_firewall\n"
                "  - name: check_password_policy\n"
                "    command: verify_password_policy\n"
                "  - name: check_tls_version\n"
                "    command: verify_tls_min_version\n"
            ),
            "risk": "none",
            "platforms": ["vmware_vsphere", "openstack", "kubernetes", "physical"],
        },
    ]

    rows = []
    for skill in skills:
        sid = new_id()
        created_by = user_ids[0]  # admin
        plat_arr = ", ".join(f"'{p}'" for p in skill["platforms"])
        yaml_escaped = esc(skill["yaml"])
        rows.append(
            f"('{sid}', '{esc(skill['name'])}', '{esc(skill['display_name'])}', "
            f"'{esc(skill['description'])}', '{esc(skill['category'])}', '1.0.0', 'active', "
            f"'{yaml_escaped}', {jsonb({})}, {jsonb({})}, "
            f"300, 0, FALSE, '{skill['risk']}', "
            f"'SRE Team', ARRAY[]::text[], "
            f"ARRAY[{plat_arr}]::platform_type[], "
            f"'{created_by}')"
        )

    out.write("INSERT INTO skills (id, name, display_name, description, category, version, status, "
              "yaml_content, parameters, output_schema, timeout_seconds, max_retries, "
              "requires_approval, risk_level, author, tags, platform_types, created_by) VALUES\n")
    out.write(",\n".join(rows) + ";\n\n")


def gen_conversations(out: TextIO, user_ids: list[uuid.UUID], asset_ids: list[uuid.UUID]) -> None:
    """Generate 5 sample AI conversations."""
    out.write("-- ===== Conversations =====\n")

    convos = [
        {"title": "Investigate high CPU on cluster-prod-east-01", "msgs": 6, "model": "claude-3.5-sonnet"},
        {"title": "Plan firmware upgrade for esxi hosts", "msgs": 4, "model": "gpt-4"},
        {"title": "Analyze disk usage trend on storage array", "msgs": 8, "model": "claude-3.5-sonnet"},
        {"title": "Review compliance audit findings", "msgs": 3, "model": "claude-3.5-sonnet"},
        {"title": "Troubleshoot network latency spike", "msgs": 10, "model": "gpt-4"},
    ]

    rows = []
    for convo in convos:
        cid = new_id()
        uid = random.choice(user_ids[:3])  # human users
        messages = []
        for mi in range(convo["msgs"]):
            role = "user" if mi % 2 == 0 else "assistant"
            content = f"Message {mi + 1} from {role}: sample conversation content for testing."
            messages.append({"role": role, "content": content, "timestamp": rand_recent(7).isoformat(), "tokens": random.randint(50, 500)})

        msg_json = json.dumps(messages, default=str).replace("'", "''")
        total_tokens = sum(m["tokens"] for m in messages)
        target = random.sample(asset_ids[:10], min(3, len(asset_ids)))

        rows.append(
            f"('{cid}', '{esc(convo['title'])}', '{uid}', 'active', "
            f"NULL, {uuid_array(target)}, NULL, "
            f"'{msg_json}'::jsonb, {len(messages)}, {total_tokens}, "
            f"'{convo['model']}', 'You are an SRE assistant.', {jsonb({})})"
        )

    out.write("INSERT INTO conversations (id, title, user_id, status, platform_id, "
              "target_assets, operation_id, messages, message_count, total_tokens, "
              "model_id, system_prompt, metadata) VALUES\n")
    out.write(",\n".join(rows) + ";\n\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_all(out: TextIO) -> None:
    """Generate complete seed SQL."""
    out.write("-- ============================================================================\n")
    out.write("-- V3.1 SRE Platform — Seed Data\n")
    out.write(f"-- Generated: {datetime.now(timezone.utc).isoformat()}\n")
    out.write("-- ============================================================================\n\n")
    out.write("BEGIN;\n\n")

    user_ids = gen_users(out)
    platform_ids = gen_platforms(out, user_ids[0])
    vm_ids, host_ids, storage_ids = gen_assets(out, platform_ids)
    gen_asset_relations(out, vm_ids, host_ids, storage_ids)

    all_asset_ids = vm_ids + host_ids + storage_ids
    gen_alerts(out, all_asset_ids, user_ids)
    gen_operations(out, user_ids, platform_ids)
    gen_audit_logs(out, user_ids, all_asset_ids)
    gen_asset_metrics(out, all_asset_ids)
    gen_skills(out, user_ids)
    gen_conversations(out, user_ids, all_asset_ids)

    out.write("COMMIT;\n\n")
    out.write("-- Seed data generation complete.\n")
    out.write(f"-- Total assets: {len(all_asset_ids)} ({len(vm_ids)} VMs, {len(host_ids)} hosts, {len(storage_ids)} storage)\n")


def main():
    parser = argparse.ArgumentParser(description="Generate V3.1 SRE Platform seed data")
    parser.add_argument("--output", "-o", help="Output SQL file path")
    parser.add_argument("--execute", action="store_true", help="Execute directly against database")
    parser.add_argument("--dsn", default="postgresql://sre_app:CHANGE_ME_IN_PRODUCTION@localhost:5432/sre_platform",
                        help="PostgreSQL connection string (for --execute)")
    args = parser.parse_args()

    if args.execute:
        try:
            import psycopg2
        except ImportError:
            print("ERROR: psycopg2 required for --execute. Install with: pip install psycopg2-binary", file=sys.stderr)
            sys.exit(1)

        import io
        buf = io.StringIO()
        generate_all(buf)
        conn = psycopg2.connect(args.dsn)
        try:
            with conn.cursor() as cur:
                cur.execute(buf.getvalue())
            conn.commit()
            print("Seed data inserted successfully.")
        except Exception as e:
            conn.rollback()
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            conn.close()
    else:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                generate_all(f)
            print(f"Seed SQL written to {args.output}")
        else:
            generate_all(sys.stdout)


if __name__ == "__main__":
    main()
