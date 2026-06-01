"""Asset service — business logic for asset management."""
from __future__ import annotations

from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException, ValidationException
from app.models.asset import Asset, AssetStatus, AssetType, Platform
from app.repositories.asset_repo import AssetRepository
from app.schemas.asset import AssetCreate, AssetUpdate

logger = structlog.get_logger(__name__)


class AssetService:
    """Business logic for asset CRUD and search operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AssetRepository(session)

    async def list_assets(
        self,
        *,
        asset_type: AssetType | None = None,
        platform: Platform | None = None,
        status: AssetStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[Sequence[Asset], int]:
        """List assets with optional filtering and pagination."""
        offset = (page - 1) * limit
        return await self._repo.search(
            asset_type=asset_type,
            platform=platform,
            status=status,
            search=search,
            offset=offset,
            limit=limit,
        )

    async def get_asset(self, asset_id: int) -> Asset:
        """Fetch a single asset by ID.

        Raises:
            NotFoundException: If the asset does not exist.
        """
        asset = await self._repo.get_by_id(asset_id)
        if asset is None:
            raise NotFoundException("Asset", asset_id)
        return asset

    async def create_asset(self, data: AssetCreate) -> Asset:
        """Create a new asset."""
        asset = Asset(**data.model_dump())
        created = await self._repo.create(asset)
        logger.info("asset_created", asset_id=created.id, name=created.name)
        return created

    async def update_asset(self, asset_id: int, data: AssetUpdate) -> Asset:
        """Partially update an existing asset.

        Raises:
            NotFoundException: If the asset does not exist.
        """
        asset = await self.get_asset(asset_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)
        updated = await self._repo.update(asset)
        logger.info("asset_updated", asset_id=updated.id)
        return updated

    async def delete_asset(self, asset_id: int) -> None:
        """Delete an asset.

        Raises:
            NotFoundException: If the asset does not exist.
        """
        asset = await self.get_asset(asset_id)
        await self._repo.delete(asset)
        logger.info("asset_deleted", asset_id=asset_id)

    async def execute_action(
        self, asset_id: int, action: str, confirm: bool = False
    ) -> dict:
        """Execute a quick action on an asset.

        Returns a dict describing the result.  Actual execution is
        delegated to the operation service in a real deployment.

        Raises:
            NotFoundException: If the asset does not exist.
            ValidationException: If the action is invalid.
        """
        asset = await self.get_asset(asset_id)

        valid_actions = {"boot", "shutdown", "restart"}
        if action not in valid_actions:
            raise ValidationException(
                f"Invalid action '{action}'. Valid actions: {', '.join(sorted(valid_actions))}"
            )

        if not confirm and action in {"shutdown", "restart"}:
            raise ValidationException(
                f"Action '{action}' requires confirmation. Set confirm=true."
            )

        logger.info("asset_action_executed", asset_id=asset_id, action=action)

        return {
            "success": True,
            "action": action,
            "message": f"Action '{action}' executed on asset '{asset.name}'",
            "operation_id": None,
        }

    async def count_by_type(self) -> list[dict]:
        """Return asset counts grouped by type."""
        return await self._repo.count_by_type()

    async def count_by_status(self) -> list[dict]:
        """Return asset counts grouped by status."""
        return await self._repo.count_by_status()
