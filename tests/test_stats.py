"""Tests for collection statistics functionality."""

from servicekit import SqliteDatabaseBuilder
from servicekit.schemas import CollectionStats

from .conftest import DemoData, TestEntity, TestEntityIn, TestEntityManager, TestEntityRepository


class TestRepositoryStats:
    """Tests for repository get_stats method."""

    async def test_get_stats_empty_collection(self) -> None:
        """Test stats for empty collection."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repository = TestEntityRepository(session)

            stats = await repository.get_stats()

            assert stats["total"] == 0

        await db.dispose()

    async def test_get_stats_with_entities(self) -> None:
        """Test stats with multiple entities."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repository = TestEntityRepository(session)

            # Create entities
            for i in range(5):
                entity = TestEntity(name=f"test{i}", data=DemoData(x=i, y=i, z=i, tags=[]))
                await repository.save(entity)

            await repository.commit()

            stats = await repository.get_stats()

            assert stats["total"] == 5

        await db.dispose()


class TestManagerStats:
    """Tests for manager get_stats method."""

    async def test_get_stats_empty_collection(self) -> None:
        """Test manager stats for empty collection."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repository = TestEntityRepository(session)
            manager = TestEntityManager(repository)

            stats = await manager.get_stats()

            assert isinstance(stats, CollectionStats)
            assert stats.total == 0

        await db.dispose()

    async def test_get_stats_with_entities(self) -> None:
        """Test manager stats with entities."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repository = TestEntityRepository(session)
            manager = TestEntityManager(repository)

            # Create entities through manager
            for i in range(10):
                entity_in = TestEntityIn(name=f"test{i}", data=DemoData(x=i, y=i, z=i, tags=[]))
                await manager.save(entity_in)

            stats = await manager.get_stats()

            assert isinstance(stats, CollectionStats)
            assert stats.total == 10

        await db.dispose()

    async def test_get_stats_returns_pydantic_model(self) -> None:
        """Test that stats returns properly structured Pydantic model."""
        db = SqliteDatabaseBuilder.in_memory().build()
        await db.init()

        async with db.session() as session:
            repository = TestEntityRepository(session)
            manager = TestEntityManager(repository)

            # Create some entities
            for i in range(3):
                entity_in = TestEntityIn(name=f"test{i}", data=DemoData(x=i, y=i, z=i, tags=[]))
                await manager.save(entity_in)

            stats = await manager.get_stats()

            # Verify Pydantic model structure
            assert hasattr(stats, "total")
            assert hasattr(stats, "model_dump")

            # Verify serialization
            dumped = stats.model_dump()
            assert "total" in dumped
            assert dumped["total"] == 3

        await db.dispose()


class TestCollectionStatsSchema:
    """Tests for CollectionStats Pydantic schema."""

    def test_collection_stats_creation(self) -> None:
        """Test creating CollectionStats instance."""
        stats = CollectionStats(total=42)

        assert stats.total == 42

    def test_collection_stats_zero_total(self) -> None:
        """Test CollectionStats with zero total."""
        stats = CollectionStats(total=0)

        assert stats.total == 0

    def test_collection_stats_negative_total_rejected(self) -> None:
        """Test that negative total is rejected."""
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CollectionStats(total=-1)

    def test_collection_stats_serialization(self) -> None:
        """Test CollectionStats serializes correctly."""
        stats = CollectionStats(total=100)

        dumped = stats.model_dump()

        assert dumped == {"total": 100}

    def test_collection_stats_json_serialization(self) -> None:
        """Test CollectionStats serializes to JSON."""
        stats = CollectionStats(total=50)

        json_str = stats.model_dump_json()

        assert '"total":50' in json_str or '"total": 50' in json_str
