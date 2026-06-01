"""Operation and OperationStep models.

Represents change operations with an approval workflow:
  pending -> approved -> executing -> completed/failed
  pending -> rejected
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class OperationStatus(str, PyEnum):
    """Operation lifecycle states."""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Operation(Base, TimestampMixin):
    """A high-level operation (e.g. 'Diagnose web-01 connectivity')."""

    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[OperationStatus] = mapped_column(
        Enum(OperationStatus, native_enum=False, length=20),
        nullable=False,
        default=OperationStatus.PENDING,
        index=True,
    )
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asset_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    steps: Mapped[list[OperationStep]] = relationship(
        back_populates="operation", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_operations_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Operation(id={self.id}, status={self.status})>"


class StepStatus(str, PyEnum):
    """Individual step execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class OperationStep(Base, TimestampMixin):
    """A single atomic step within an operation."""

    __tablename__ = "operation_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("operations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus, native_enum=False, length=20),
        nullable=False,
        default=StepStatus.PENDING,
    )
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    operation: Mapped[Operation] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<OperationStep(id={self.id}, step={self.step_number}, status={self.status})>"
