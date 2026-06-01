"""Tests for AssetRepository — search, count_by_type, count_by_status."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetStatus, AssetType, Platform
from app.repositories.asset_repo import AssetRepository


@pytest.mark.asyncio
async def test_search_returns_all(db_session: AsyncSession, seed_assets):
    """search with no filters returns all assets."""
    repo = AssetRepository(db_session)
    assets, total = await repo.search()
    assert total == 3
    assert len(assets) == 3


@pytest.mark.asyncio
async def test_search_by_asset_type(db_session: AsyncSession, seed_assets):
    """search filtered by asset_type returns only matching assets."""
    repo = AssetRepository(db_session)
    assets, total = await repo.search(asset_type=AssetType.VM)
    assert total == 1
    assert assets[0].name == "web-01"


@pytest.mark.asyncio
async def test_search_by_status(db_session: AsyncSession, seed_assets):
    """search filtered by status returns only matching assets."""
    repo = AssetRepository(db_session)
    assets, total = await repo.search(status=AssetStatus.RUNNING)
    assert total == 3


@pytest.mark.asyncio
async def test_search_with_text(db_session: AsyncSession, seed_assets):
    """search with text filter performs LIKE matching on name/hostname."""
    repo = AssetRepository(db_session)
    assets, total = await repo.search(search="web")
    assert total == 1
    assert assets[0].name == "web-01"


@pytest.mark.asyncio
async def test_search_with_text_no_match(db_session: AsyncSession, seed_assets):
    """search with non-matching text returns empty results."""
    repo = AssetRepository(db_session)
    assets, total = await repo.search(search="nonexistent-host")
    assert total == 0
    assert len(assets) == 0


@pytest.mark.asyncio
async def test_search_with_like_special_chars(db_session: AsyncSession):
    """search escapes SQL LIKE wildcards (% and _) in user input."""
    # Add an asset with a name containing LIKE-special characters
    asset = Asset(
        name="host%20_test",
        asset_type=AssetType.VM,
        platform=Platform.VSPHERE,
        status=AssetStatus.RUNNING,
    )
    db_session.add(asset)
    await db_session.flush()

    repo = AssetRepository(db_session)
    # Searching for literal % should not match everything
    assets, total = await repo.search(search="%20")
    assert total == 1
    assert assets[0].name == "host%20_test"


@pytest.mark.asyncio
async def test_search_pagination(db_session: AsyncSession, seed_assets):
    """search respects offset and limit parameters."""
    repo = AssetRepository(db_session)
    assets, total = await repo.search(offset=1, limit=1)
    assert total == 3
    assert len(assets) == 1


@pytest.mark.asyncio
async def test_count_by_type(db_session: AsyncSession, seed_assets):
    """count_by_type returns asset counts grouped by type."""
    repo = AssetRepository(db_session)
    result = await repo.count_by_type()
    result_dict = {r["asset_type"]: r["count"] for r in result}
    assert result_dict["vm"] == 1
    assert result_dict["database"] == 1
    assert result_dict["host"] == 1


@pytest.mark.asyncio
async def test_count_by_status(db_session: AsyncSession, seed_assets):
    """count_by_status returns asset counts grouped by status."""
    repo = AssetRepository(db_session)
    result = await repo.count_by_status()
    result_dict = {r["status"]: r["count"] for r in result}
    assert result_dict["running"] == 3


@pytest.mark.asyncio
async def test_count_by_type_empty(db_session: AsyncSession):
    """count_by_type with no assets returns empty list."""
    repo = AssetRepository(db_session)
    result = await repo.count_by_type()
    assert result == []
