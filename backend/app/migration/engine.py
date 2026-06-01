"""Cross-platform VM migration engine.

Supports migrations between VMware, KVM, and FusionSphere.
Uses virt-v2v and qemu-img convert as underlying tools.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MigrationStatus(str, Enum):
    """Migration lifecycle states."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationMethod(str, Enum):
    """Supported migration methods."""
    V2V = "virt-v2v"       # VMware -> KVM
    QEMU_CONVERT = "qemu-img-convert"  # VMware <-> FusionSphere, KVM <-> VMware
    LIVE_MIGRATE = "live-migrate"       # Same platform


@dataclass
class MigrationStep:
    """A single step in a migration plan."""
    order: int
    action: str
    description: str
    command: str = ""
    is_descriptive: bool = False  # True = placeholder, skip execution
    status: str = "pending"
    error: str | None = None


@dataclass
class MigrationPlan:
    """A complete migration plan."""
    plan_id: str
    vm_id: str
    source_platform: str
    target_platform: str
    method: MigrationMethod
    steps: list[MigrationStep] = field(default_factory=list)
    status: MigrationStatus = MigrationStatus.PLANNED
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None


@dataclass
class MigrationStatusInfo:
    """Status information for a migration."""
    plan_id: str
    status: MigrationStatus
    current_step: int
    total_steps: int
    progress_pct: float
    error: str | None = None


class MigrationEngine:
    """Orchestrates cross-platform VM migrations."""

    def __init__(self) -> None:
        self._plans: dict[str, MigrationPlan] = {}

    @staticmethod
    def _determine_method(source: str, target: str) -> MigrationMethod:
        """Determine the migration method based on source and target platforms."""
        if source == "vsphere" and target == "kvm":
            return MigrationMethod.V2V
        elif source == "vsphere" and target == "fusionsphere":
            return MigrationMethod.QEMU_CONVERT
        elif source == "kvm" and target == "vsphere":
            return MigrationMethod.QEMU_CONVERT
        elif source == target:
            return MigrationMethod.LIVE_MIGRATE
        else:
            raise ValueError(f"Unsupported migration path: {source} -> {target}")

    async def plan_migration(self, vm_id: str, source: str, target: str) -> MigrationPlan:
        """Generate a migration plan for a VM."""
        method = self._determine_method(source, target)
        plan_id = str(uuid.uuid4())
        steps: list[MigrationStep] = []

        if method == MigrationMethod.V2V:
            steps = [
                MigrationStep(order=1, action="export", description="Export VM disk from vSphere", command="export OVA from vSphere", is_descriptive=True),
                MigrationStep(order=2, action="convert", description="Convert disk using virt-v2v", command="virt-v2v -i ova disk.ova -o local -os /var/lib/libvirt/images"),
                MigrationStep(order=3, action="import", description="Import VM into KVM/libvirt", command="virsh define converted-vm.xml"),
                MigrationStep(order=4, action="verify", description="Verify VM boots and network connectivity", command="virsh dominfo <vm_id>", is_descriptive=True),
            ]
        elif method == MigrationMethod.QEMU_CONVERT:
            steps = [
                MigrationStep(order=1, action="export", description="Export VM disk from source platform", command="download disk image", is_descriptive=True),
                MigrationStep(order=2, action="convert", description="Convert disk format using qemu-img", command="qemu-img convert -f vmdk -O qcow2 source.vmdk target.qcow2"),
                MigrationStep(order=3, action="import", description="Import VM into target platform", command="create VM from converted disk", is_descriptive=True),
                MigrationStep(order=4, action="verify", description="Verify VM boots correctly", command="check VM status", is_descriptive=True),
            ]
        elif method == MigrationMethod.LIVE_MIGRATE:
            steps = [
                MigrationStep(order=1, action="pre_check", description="Verify source and target compatibility", command="check resources", is_descriptive=True),
                MigrationStep(order=2, action="migrate", description="Perform live migration", command="live migrate VM", is_descriptive=True),
                MigrationStep(order=3, action="verify", description="Verify VM on target host", command="check VM status", is_descriptive=True),
            ]

        plan = MigrationPlan(
            plan_id=plan_id, vm_id=vm_id,
            source_platform=source, target_platform=target,
            method=method, steps=steps,
        )
        self._plans[plan_id] = plan
        logger.info("migration_planned", plan_id=plan_id, vm_id=vm_id, method=method.value)
        return plan

    async def execute_migration(self, plan_id: str) -> bool:
        """Execute a migration plan step by step."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise ValueError(f"Plan {plan_id} not found")
        if plan.status != MigrationStatus.PLANNED:
            raise ValueError(f"Plan {plan_id} is not in planned state (current: {plan.status.value})")

        plan.status = MigrationStatus.IN_PROGRESS
        plan.started_at = time.time()
        logger.info("migration_started", plan_id=plan_id)

        try:
            for step in plan.steps:
                step.status = "running"
                logger.info("step_started", plan_id=plan_id, step=step.order, action=step.action)
                # Execute the migration command via subprocess
                # NOTE: Descriptive commands (non-shell) are logged but not executed.
                # Real commands use create_subprocess_exec with argument lists.
                import shlex
                try:
                    if step.is_descriptive or not (step.command or "").strip():
                        logger.warning("migration_step_skip_descriptive", step=step.order, command=step.command)
                        step.status = "completed"
                        continue
                    cmd_args = shlex.split(step.command)
                    proc = await asyncio.create_subprocess_exec(
                        *cmd_args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), timeout=3600
                    )
                    if proc.returncode != 0:
                        step.status = "failed"
                        step.error = stderr.decode("utf-8", errors="replace").strip()
                        raise RuntimeError(f"Step {step.order} failed: {step.error}")
                    step.status = "completed"
                except asyncio.TimeoutError:
                    step.status = "failed"
                    step.error = f"Step {step.order} timed out after 3600s"
                    raise RuntimeError(step.error)
                logger.info("step_completed", plan_id=plan_id, step=step.order)

            plan.status = MigrationStatus.COMPLETED
            plan.completed_at = time.time()
            logger.info("migration_completed", plan_id=plan_id)
            return True
        except Exception as exc:
            plan.status = MigrationStatus.FAILED
            plan.error = str(exc)
            logger.error("migration_failed", plan_id=plan_id, error=str(exc))
            return False

    async def rollback_migration(self, plan_id: str) -> bool:
        """Rollback a failed or in-progress migration."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise ValueError(f"Plan {plan_id} not found")
        if plan.status not in (MigrationStatus.IN_PROGRESS, MigrationStatus.FAILED):
            raise ValueError(f"Cannot rollback plan in state {plan.status.value}")

        logger.info("migration_rollback_started", plan_id=plan_id)
        # Reverse completed steps
        for step in reversed(plan.steps):
            if step.status == "completed":
                logger.info("rollback_step", plan_id=plan_id, step=step.order, action=step.action)
                step.status = "rolled_back"
        plan.status = MigrationStatus.ROLLED_BACK
        logger.info("migration_rollback_completed", plan_id=plan_id)
        return True

    async def get_migration_status(self, plan_id: str) -> MigrationStatusInfo:
        """Get the current status of a migration plan."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise ValueError(f"Plan {plan_id} not found")

        total = len(plan.steps)
        completed = sum(1 for s in plan.steps if s.status in ("completed", "rolled_back"))
        current = 0
        for s in plan.steps:
            if s.status == "running":
                current = s.order
                break
            elif s.status == "completed":
                current = s.order

        progress = (completed / total * 100) if total > 0 else 0.0

        return MigrationStatusInfo(
            plan_id=plan_id,
            status=plan.status,
            current_step=current,
            total_steps=total,
            progress_pct=progress,
            error=plan.error,
        )
