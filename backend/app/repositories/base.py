"""Generic CRUD repository base class.

Provides reusable async database operations for any SQLAlchemy model.
Subclasses only need to specify the model class.
"""
from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async CRUD repository.

    Type parameter ModelT must be an SQLAlchemy ORM model inheriting from Base.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: int) -> ModelT | None:
        """Fetch a single record by primary key."""
        return await self._session.get(self.model, id_)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Any | None = None,
    ) -> Sequence[ModelT]:
        """Return a paginated list of records."""
        stmt: Select = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.id.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Return total record count."""
        stmt = select(func.count()).select_from(self.model)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, obj: ModelT) -> ModelT:
        """Persist a new model instance."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def update(self, obj: ModelT) -> ModelT:
        """Persist changes to an existing model instance."""
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Remove a model instance."""
        await self._session.delete(obj)
        await self._session.flush()
