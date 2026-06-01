"""Alert service — business logic for alert management."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.repositories.alert_repo import AlertRepository

logger = structlog.get_logger(__name__)


class AlertService:
    """Business logic for alert lifecycle management."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AlertRepository(session)

    async def list_alerts(
        self,
        *,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        asset_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Alert], int]:
        """List alerts with optional filtering and pagination."""
        offset = (page - 1) * limit
        return await self._repo.filter_alerts(
            severity=severity,
            status=status,
            asset_id=asset_id,
            offset=offset,
            limit=limit,
        )

    async def get_alert(self, alert_id: int) -> Alert:
        """Fetch a single alert by ID.

        Raises:
            NotFoundException: If the alert does not exist.
        """
        alert = await self._repo.get_by_id(alert_id)
        if alert is None:
            raise NotFoundException("Alert", alert_id)
        return alert

    async def acknowledge_alert(
        self, alert_id: int, user: str, notes: str | None = None
    ) -> Alert:
        """Acknowledge an alert.

        Raises:
            NotFoundException: If the alert does not exist.
            ConflictException: If the alert is not in 'active' status.
        """
        alert = await self.get_alert(alert_id)

        if alert.status != AlertStatus.ACTIVE:
            raise ConflictException(
                f"Cannot acknowledge alert in '{alert.status}' status. "
                f"Only 'active' alerts can be acknowledged."
            )

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user
        alert.acknowledged_at = datetime.now(timezone.utc)

        updated = await self._repo.update(alert)
        logger.info("alert_acknowledged", alert_id=alert_id, user=user)
        return updated

    async def resolve_alert(
        self, alert_id: int, user: str, resolution_notes: str
    ) -> Alert:
        """Resolve an alert.

        Raises:
            NotFoundException: If the alert does not exist.
            ValidationException: If resolution_notes is empty.
            ConflictException: If the alert is already resolved.
        """
        if not resolution_notes or not resolution_notes.strip():
            raise ValidationException("Resolution notes are required")

        alert = await self.get_alert(alert_id)

        if alert.status == AlertStatus.RESOLVED:
            raise ConflictException("Alert is already resolved")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = user
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolution_notes = resolution_notes

        updated = await self._repo.update(alert)
        logger.info("alert_resolved", alert_id=alert_id, user=user)
        return updated

    async def count_active(self) -> int:
        """Count active alerts."""
        return await self._repo.count_active()

    async def count_by_severity(self) -> list[dict]:
        """Return active alert counts grouped by severity."""
        return await self._repo.count_by_severity()
