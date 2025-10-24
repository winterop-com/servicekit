"""Tests for model discovery utilities."""

from sqlalchemy.orm import Mapped, mapped_column

from servicekit import Base, Entity
from servicekit.utils import get_custom_tables, get_framework_tables, get_registered_tables, has_custom_models


class TestModelDiscovery:
    """Test model discovery utility functions."""

    def test_get_framework_tables_returns_empty(self) -> None:
        """Test that servicekit returns empty framework tables."""
        framework_tables = get_framework_tables()
        assert framework_tables == set()

    def test_get_registered_tables_with_no_models(self) -> None:
        """Test get_registered_tables with empty metadata."""
        # Create a new Base instance to avoid pollution
        from sqlalchemy.ext.asyncio import AsyncAttrs
        from sqlalchemy.orm import DeclarativeBase

        class TestBase(AsyncAttrs, DeclarativeBase):
            pass

        tables = get_registered_tables(TestBase)
        assert tables == set()

    def test_get_registered_tables_with_model(self) -> None:
        """Test get_registered_tables detects models."""

        class TestUser(Entity):  # pyright: ignore[reportUnusedClass]
            __tablename__ = "test_users"
            __table_args__ = {"extend_existing": True}

            username: Mapped[str] = mapped_column()

        tables = get_registered_tables(Base)
        assert "test_users" in tables

    def test_has_custom_models_false_with_no_models(self) -> None:
        """Test has_custom_models returns False with no models."""
        from sqlalchemy.ext.asyncio import AsyncAttrs
        from sqlalchemy.orm import DeclarativeBase

        class TestBase(AsyncAttrs, DeclarativeBase):
            pass

        assert not has_custom_models(TestBase)

    def test_has_custom_models_true_with_custom_model(self) -> None:
        """Test has_custom_models returns True with custom models."""

        class TestProduct(Entity):  # pyright: ignore[reportUnusedClass]
            __tablename__ = "test_products"
            __table_args__ = {"extend_existing": True}

            name: Mapped[str] = mapped_column()

        # Servicekit has no framework tables, so any model is "custom"
        assert has_custom_models(Base)

    def test_has_custom_models_with_framework_tables(self) -> None:
        """Test has_custom_models excludes framework tables."""

        class TestConfig(Entity):  # pyright: ignore[reportUnusedClass]
            __tablename__ = "test_configs"
            __table_args__ = {"extend_existing": True}

            name: Mapped[str] = mapped_column()

        # Simulate framework declaring "test_configs" as a framework table
        framework_tables = {"test_configs"}

        # Should return False since test_configs is considered framework
        # (may return True if other models exist from previous tests)
        custom_tables = get_custom_tables(Base, framework_tables)
        assert "test_configs" not in custom_tables

    def test_get_custom_tables_returns_correct_set(self) -> None:
        """Test get_custom_tables returns user tables only."""

        class TestOrder(Entity):  # pyright: ignore[reportUnusedClass]
            __tablename__ = "test_orders"
            __table_args__ = {"extend_existing": True}

            amount: Mapped[int] = mapped_column()

        framework_tables = {"other_framework_table"}

        custom_tables = get_custom_tables(Base, framework_tables)

        # test_orders should be in custom tables
        assert "test_orders" in custom_tables
        # Framework table should not be in custom tables
        assert "other_framework_table" not in custom_tables

    def test_get_custom_tables_empty_with_only_framework(self) -> None:
        """Test get_custom_tables returns empty when only framework tables exist."""

        class TestFrameworkTable(Entity):  # pyright: ignore[reportUnusedClass]
            __tablename__ = "test_framework_only"
            __table_args__ = {"extend_existing": True}

            data: Mapped[str] = mapped_column()

        all_tables = get_registered_tables(Base)
        framework_tables = all_tables.copy()  # Treat all as framework

        custom_tables = get_custom_tables(Base, framework_tables)
        assert custom_tables == set()
