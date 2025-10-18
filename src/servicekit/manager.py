"""Base classes for service layer managers with lifecycle hooks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from pydantic import BaseModel

from servicekit.repository import BaseRepository


class LifecycleHooks[ModelT, InSchemaT: BaseModel]:
    """Lifecycle hooks for entity operations."""

    def _should_assign_field(self, field: str, value: object) -> bool:
        """Determine if a field should be assigned during update."""
        return True

    async def pre_save(self, entity: ModelT, data: InSchemaT) -> None:
        """Hook called before saving a new entity."""
        pass

    async def post_save(self, entity: ModelT) -> None:
        """Hook called after saving a new entity."""
        pass

    async def pre_update(self, entity: ModelT, data: InSchemaT, old_values: dict[str, object]) -> None:
        """Hook called before updating an existing entity."""
        pass

    async def post_update(self, entity: ModelT, changes: dict[str, tuple[object, object]]) -> None:
        """Hook called after updating an existing entity."""
        pass

    async def pre_delete(self, entity: ModelT) -> None:
        """Hook called before deleting an entity."""
        pass

    async def post_delete(self, entity: ModelT) -> None:
        """Hook called after deleting an entity."""
        pass


class Manager[InSchemaT: BaseModel, OutSchemaT: BaseModel, IdT](ABC):
    """Abstract manager interface for business logic operations."""

    @abstractmethod
    async def save(self, data: InSchemaT) -> OutSchemaT:
        """Save an entity."""
        ...

    @abstractmethod
    async def save_all(self, items: Iterable[InSchemaT]) -> list[OutSchemaT]:
        """Save multiple entities."""
        ...

    @abstractmethod
    async def delete_by_id(self, id: IdT) -> None:
        """Delete an entity by its ID."""
        ...

    @abstractmethod
    async def delete_all(self) -> None:
        """Delete all entities."""
        ...

    @abstractmethod
    async def delete_all_by_id(self, ids: Sequence[IdT]) -> None:
        """Delete multiple entities by their IDs."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Count the number of entities."""
        ...

    @abstractmethod
    async def exists_by_id(self, id: IdT) -> bool:
        """Check if an entity exists by its ID."""
        ...

    @abstractmethod
    async def find_by_id(self, id: IdT) -> OutSchemaT | None:
        """Find an entity by its ID."""
        ...

    @abstractmethod
    async def find_all(self) -> list[OutSchemaT]:
        """Find all entities."""
        ...

    @abstractmethod
    async def find_paginated(self, page: int, size: int) -> tuple[list[OutSchemaT], int]:
        """Find entities with pagination."""
        ...

    @abstractmethod
    async def find_all_by_id(self, ids: Sequence[IdT]) -> list[OutSchemaT]:
        """Find entities by their IDs."""
        ...


class BaseManager[ModelT, InSchemaT: BaseModel, OutSchemaT: BaseModel, IdT](
    LifecycleHooks[ModelT, InSchemaT],
    Manager[InSchemaT, OutSchemaT, IdT],
):
    """Base manager implementation with CRUD operations and lifecycle hooks."""

    def __init__(
        self,
        repo: BaseRepository[ModelT, IdT],
        model_cls: type[ModelT],
        out_schema_cls: type[OutSchemaT],
    ) -> None:
        """Initialize manager with repository, model class, and output schema class."""
        self.repo = repo
        self.model_cls = model_cls
        self.out_schema_cls = out_schema_cls

    def _to_output_schema(self, entity: ModelT) -> OutSchemaT:
        """Convert ORM entity to output schema."""
        return self.out_schema_cls.model_validate(entity, from_attributes=True)

    async def save(self, data: InSchemaT) -> OutSchemaT:
        """Save an entity (create or update)."""
        data_dict = data.model_dump(exclude_none=True)
        entity_id = data_dict.get("id")
        existing: ModelT | None = None

        if entity_id is not None:
            existing = await self.repo.find_by_id(entity_id)

        if existing is None:
            if data_dict.get("id") is None:
                data_dict.pop("id", None)
            entity = self.model_cls(**data_dict)
            await self.pre_save(entity, data)
            await self.repo.save(entity)
            await self.repo.commit()
            await self.repo.refresh_many([entity])
            await self.post_save(entity)
            return self._to_output_schema(entity)

        tracked_fields = set(data_dict.keys())
        if hasattr(existing, "level"):  # pragma: no branch
            tracked_fields.add("level")
        old_values = {field: getattr(existing, field) for field in tracked_fields if hasattr(existing, field)}

        for key, value in data_dict.items():
            if key == "id":  # pragma: no branch
                continue
            if not self._should_assign_field(key, value):
                continue
            if hasattr(existing, key):
                setattr(existing, key, value)

        await self.pre_update(existing, data, old_values)

        changes: dict[str, tuple[object, object]] = {}
        for field in tracked_fields:
            if hasattr(existing, field):
                new_value = getattr(existing, field)
                old_value = old_values.get(field)
                if old_value != new_value:
                    changes[field] = (old_value, new_value)

        await self.repo.save(existing)
        await self.repo.commit()
        await self.repo.refresh_many([existing])
        await self.post_update(existing, changes)
        return self._to_output_schema(existing)

    async def save_all(self, items: Iterable[InSchemaT]) -> list[OutSchemaT]:
        entities_to_insert: list[ModelT] = []
        updates: list[tuple[ModelT, dict[str, tuple[object, object]]]] = []
        outputs: list[ModelT] = []

        for data in items:
            data_dict = data.model_dump(exclude_none=True)
            entity_id = data_dict.get("id")
            existing: ModelT | None = None
            if entity_id is not None:
                existing = await self.repo.find_by_id(entity_id)

            if existing is None:
                if data_dict.get("id") is None:
                    data_dict.pop("id", None)
                entity = self.model_cls(**data_dict)
                await self.pre_save(entity, data)
                entities_to_insert.append(entity)
                outputs.append(entity)
                continue

            tracked_fields = set(data_dict.keys())
            if hasattr(existing, "level"):  # pragma: no branch
                tracked_fields.add("level")
            old_values = {field: getattr(existing, field) for field in tracked_fields if hasattr(existing, field)}

            for key, value in data_dict.items():
                if key == "id":  # pragma: no branch
                    continue
                if not self._should_assign_field(key, value):
                    continue
                if hasattr(existing, key):
                    setattr(existing, key, value)

            await self.pre_update(existing, data, old_values)

            changes: dict[str, tuple[object, object]] = {}
            for field in tracked_fields:
                if hasattr(existing, field):
                    new_value = getattr(existing, field)
                    old_value = old_values.get(field)
                    if old_value != new_value:
                        changes[field] = (old_value, new_value)

            updates.append((existing, changes))
            outputs.append(existing)

        if entities_to_insert:  # pragma: no branch
            await self.repo.save_all(entities_to_insert)
        await self.repo.commit()
        if outputs:  # pragma: no branch
            await self.repo.refresh_many(outputs)

        for entity in entities_to_insert:
            await self.post_save(entity)
        for entity, changes in updates:
            await self.post_update(entity, changes)

        return [self._to_output_schema(entity) for entity in outputs]

    async def delete_by_id(self, id: IdT) -> None:
        """Delete an entity by its ID."""
        entity = await self.repo.find_by_id(id)
        if entity is None:
            return
        await self.pre_delete(entity)
        await self.repo.delete(entity)
        await self.repo.commit()
        await self.post_delete(entity)

    async def delete_all(self) -> None:
        """Delete all entities."""
        entities = await self.repo.find_all()
        for entity in entities:
            await self.pre_delete(entity)
        await self.repo.delete_all()
        await self.repo.commit()
        for entity in entities:
            await self.post_delete(entity)

    async def delete_all_by_id(self, ids: Sequence[IdT]) -> None:
        """Delete multiple entities by their IDs."""
        if not ids:
            return
        entities = await self.repo.find_all_by_id(ids)
        for entity in entities:
            await self.pre_delete(entity)
        await self.repo.delete_all_by_id(ids)
        await self.repo.commit()
        for entity in entities:
            await self.post_delete(entity)

    async def count(self) -> int:
        """Count the number of entities."""
        return await self.repo.count()

    async def exists_by_id(self, id: IdT) -> bool:
        """Check if an entity exists by its ID."""
        return await self.repo.exists_by_id(id)

    async def find_by_id(self, id: IdT) -> OutSchemaT | None:
        """Find an entity by its ID."""
        entity = await self.repo.find_by_id(id)
        if entity is None:
            return None
        return self._to_output_schema(entity)

    async def find_all(self) -> list[OutSchemaT]:
        """Find all entities."""
        entities = await self.repo.find_all()
        return [self._to_output_schema(e) for e in entities]

    async def find_paginated(self, page: int, size: int) -> tuple[list[OutSchemaT], int]:
        """Find entities with pagination."""
        offset = (page - 1) * size
        entities = await self.repo.find_all_paginated(offset, size)
        total = await self.repo.count()
        return [self._to_output_schema(e) for e in entities], total

    async def find_all_by_id(self, ids: Sequence[IdT]) -> list[OutSchemaT]:
        """Find entities by their IDs."""
        entities = await self.repo.find_all_by_id(ids)
        return [self._to_output_schema(e) for e in entities]
