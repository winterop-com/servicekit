"""Tests for tags support in Entity, EntityIn, and EntityOut."""

from ulid import ULID

from servicekit import EntityIn, EntityOut, SqliteDatabaseBuilder

from .conftest import DemoData, TestEntity, TestEntityIn, TestEntityManager, TestEntityOut, TestEntityRepository


class TestEntityTags:
    """Tests for tags field in Entity ORM model."""

    async def test_entity_tags_default_empty_list(self) -> None:
        """Test that tags default to empty list when not provided."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity without tags
            entity = TestEntity(name="test", data={"x": 1, "y": 2, "z": 3, "tags": []})
            saved = await repo.save(entity)
            await repo.commit()

            # Verify tags is empty list
            assert saved.tags == []
            assert isinstance(saved.tags, list)

        await db.dispose()

    async def test_entity_tags_set_on_creation(self) -> None:
        """Test that tags can be set during entity creation."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity with tags
            entity = TestEntity(
                name="test",
                data={"x": 1, "y": 2, "z": 3, "tags": []},
                tags=["production", "v2", "critical"],
            )
            saved = await repo.save(entity)
            await repo.commit()

            # Verify tags are saved
            assert saved.tags == ["production", "v2", "critical"]

        await db.dispose()

    async def test_entity_tags_persist_to_database(self) -> None:
        """Test that tags persist to database and can be retrieved."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create and save entity with tags
            entity = TestEntity(
                name="test",
                data={"x": 1, "y": 2, "z": 3, "tags": []},
                tags=["tag1", "tag2"],
            )
            saved = await repo.save(entity)
            await repo.commit()
            entity_id = saved.id

        # Retrieve in new session
        async with db.session() as session:
            repo = TestEntityRepository(session)
            found = await repo.find_by_id(entity_id)

            assert found is not None
            assert found.tags == ["tag1", "tag2"]

        await db.dispose()

    async def test_entity_tags_update(self) -> None:
        """Test that tags can be updated."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity with initial tags
            entity = TestEntity(
                name="test",
                data={"x": 1, "y": 2, "z": 3, "tags": []},
                tags=["old-tag"],
            )
            saved = await repo.save(entity)
            await repo.commit()

            # Update tags
            saved.tags = ["new-tag", "updated"]
            updated = await repo.save(saved)
            await repo.commit()

            # Verify tags updated
            assert updated.tags == ["new-tag", "updated"]

        await db.dispose()

    async def test_entity_tags_empty_list_vs_none(self) -> None:
        """Test that tags are never None, always a list."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity without explicit tags
            entity = TestEntity(name="test", data={"x": 1, "y": 2, "z": 3, "tags": []})
            saved = await repo.save(entity)
            await repo.commit()

            # Tags should be empty list, not None
            assert saved.tags is not None
            assert saved.tags == []
            assert len(saved.tags) == 0

        await db.dispose()


class TestEntityInSchemaTags:
    """Tests for tags field in EntityIn Pydantic schema."""

    def test_entity_in_tags_default_empty_list(self) -> None:
        """Test that EntityIn tags default to empty list."""
        entity_in = TestEntityIn(name="test", data=DemoData(x=1, y=2, z=3, tags=[]))

        assert entity_in.tags == []
        assert isinstance(entity_in.tags, list)

    def test_entity_in_tags_accepts_list(self) -> None:
        """Test that EntityIn accepts tags as list of strings."""
        entity_in = TestEntityIn(
            name="test",
            data=DemoData(x=1, y=2, z=3, tags=[]),
            tags=["prod", "v2"],
        )

        assert entity_in.tags == ["prod", "v2"]

    def test_entity_in_tags_with_empty_list(self) -> None:
        """Test that EntityIn accepts explicit empty list."""
        entity_in = TestEntityIn(
            name="test",
            data=DemoData(x=1, y=2, z=3, tags=[]),
            tags=[],
        )

        assert entity_in.tags == []

    def test_entity_in_tags_with_id_and_tags(self) -> None:
        """Test that EntityIn works with both id and tags."""
        entity_id = ULID()
        entity_in = TestEntityIn(
            id=entity_id,
            name="test",
            data=DemoData(x=1, y=2, z=3, tags=[]),
            tags=["important"],
        )

        assert entity_in.id == entity_id
        assert entity_in.tags == ["important"]

    def test_entity_in_tags_serialization(self) -> None:
        """Test that EntityIn tags serialize correctly to dict."""
        entity_in = TestEntityIn(
            name="test",
            data=DemoData(x=1, y=2, z=3, tags=[]),
            tags=["alpha", "beta"],
        )

        dumped = entity_in.model_dump()
        assert "tags" in dumped
        assert dumped["tags"] == ["alpha", "beta"]


class TestEntityOutSchemaTags:
    """Tests for tags field in EntityOut Pydantic schema."""

    async def test_entity_out_tags_from_orm(self) -> None:
        """Test that EntityOut correctly reads tags from ORM model."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity with tags
            entity = TestEntity(
                name="test",
                data={"x": 1, "y": 2, "z": 3, "tags": []},
                tags=["tag1", "tag2"],
            )
            saved = await repo.save(entity)
            await repo.commit()

            # Convert to output schema
            entity_out = TestEntityOut.model_validate(saved)

            assert entity_out.tags == ["tag1", "tag2"]

        await db.dispose()

    async def test_entity_out_tags_default_empty_list(self) -> None:
        """Test that EntityOut tags default to empty list."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity without tags
            entity = TestEntity(name="test", data={"x": 1, "y": 2, "z": 3, "tags": []})
            saved = await repo.save(entity)
            await repo.commit()

            # Convert to output schema
            entity_out = TestEntityOut.model_validate(saved)

            assert entity_out.tags == []

        await db.dispose()

    async def test_entity_out_tags_serialization(self) -> None:
        """Test that EntityOut tags serialize correctly to JSON."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)

            # Create entity with tags
            entity = TestEntity(
                name="test",
                data={"x": 1, "y": 2, "z": 3, "tags": []},
                tags=["gamma", "delta"],
            )
            saved = await repo.save(entity)
            await repo.commit()

            # Convert to output schema and serialize
            entity_out = TestEntityOut.model_validate(saved)
            dumped = entity_out.model_dump()

            assert "tags" in dumped
            assert dumped["tags"] == ["gamma", "delta"]

        await db.dispose()


class TestManagerTags:
    """Tests for tags support in BaseManager operations."""

    async def test_manager_save_with_tags(self) -> None:
        """Test that manager save works with tags."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)
            manager = TestEntityManager(repo)

            # Save entity with tags
            entity_in = TestEntityIn(
                name="test",
                data=DemoData(x=1, y=2, z=3, tags=[]),
                tags=["managed", "tagged"],
            )
            result = await manager.save(entity_in)

            assert result.tags == ["managed", "tagged"]

        await db.dispose()

    async def test_manager_save_all_with_tags(self) -> None:
        """Test that manager save_all works with tags."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)
            manager = TestEntityManager(repo)

            # Save multiple entities with different tags
            entities = [
                TestEntityIn(name="test1", data=DemoData(x=1, y=1, z=1, tags=[]), tags=["group-a"]),
                TestEntityIn(name="test2", data=DemoData(x=2, y=2, z=2, tags=[]), tags=["group-b"]),
                TestEntityIn(name="test3", data=DemoData(x=3, y=3, z=3, tags=[]), tags=["group-a", "group-b"]),
            ]
            results = await manager.save_all(entities)

            assert results[0].tags == ["group-a"]
            assert results[1].tags == ["group-b"]
            assert results[2].tags == ["group-a", "group-b"]

        await db.dispose()

    async def test_manager_update_tags(self) -> None:
        """Test that manager can update tags."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)
            manager = TestEntityManager(repo)

            # Create entity with initial tags
            entity_in = TestEntityIn(
                name="test",
                data=DemoData(x=1, y=2, z=3, tags=[]),
                tags=["old"],
            )
            created = await manager.save(entity_in)

            # Update tags
            update_in = TestEntityIn(
                id=created.id,
                name="test",
                data=DemoData(x=1, y=2, z=3, tags=[]),
                tags=["new", "updated"],
            )
            updated = await manager.save(update_in)

            assert updated.tags == ["new", "updated"]

        await db.dispose()

    async def test_manager_find_returns_tags(self) -> None:
        """Test that manager find operations return tags."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)
            manager = TestEntityManager(repo)

            # Create entity with tags
            entity_in = TestEntityIn(
                name="test",
                data=DemoData(x=1, y=2, z=3, tags=[]),
                tags=["findable"],
            )
            created = await manager.save(entity_in)

            # Find by ID
            found = await manager.find_by_id(created.id)

            assert found is not None
            assert found.tags == ["findable"]

        await db.dispose()

    async def test_manager_find_all_returns_tags(self) -> None:
        """Test that manager find_all returns tags for all entities."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repo = TestEntityRepository(session)
            manager = TestEntityManager(repo)

            # Create multiple entities with tags
            entities = [
                TestEntityIn(name=f"test{i}", data=DemoData(x=i, y=i, z=i, tags=[]), tags=[f"tag-{i}"])
                for i in range(3)
            ]
            await manager.save_all(entities)

            # Find all
            all_entities = await manager.find_all()

            assert len(all_entities) == 3
            assert all(isinstance(e.tags, list) for e in all_entities)
            assert all_entities[0].tags == ["tag-0"]
            assert all_entities[1].tags == ["tag-1"]
            assert all_entities[2].tags == ["tag-2"]

        await db.dispose()


class TestBaseEntityInAndOutTags:
    """Tests for tags in base EntityIn and EntityOut schemas."""

    def test_base_entity_in_has_tags(self) -> None:
        """Test that base EntityIn has tags field."""
        entity_in = EntityIn(tags=["test"])

        assert hasattr(entity_in, "tags")
        assert entity_in.tags == ["test"]

    def test_base_entity_in_tags_default(self) -> None:
        """Test that base EntityIn tags default to empty list."""
        entity_in = EntityIn()

        assert entity_in.tags == []

    def test_base_entity_out_has_tags(self) -> None:
        """Test that base EntityOut has tags field in model fields."""
        from datetime import datetime

        from ulid import ULID

        entity_out = EntityOut(
            id=ULID(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["base"],
        )

        assert hasattr(entity_out, "tags")
        assert entity_out.tags == ["base"]
