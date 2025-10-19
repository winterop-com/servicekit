"""Tests for custom types - SQLAlchemy and Pydantic types."""

import json

from pydantic import BaseModel
from sqlalchemy import select
from ulid import ULID

from servicekit import SqliteDatabaseBuilder
from servicekit.types import (
    JsonSafe,
    ULIDType,
    _create_serialization_metadata,
    _is_json_serializable,
    _serialize_with_metadata,
)

# Tests for _is_json_serializable


def test_is_json_serializable_returns_true_for_basic_types():
    """Test that basic JSON-serializable types return True."""
    assert _is_json_serializable("string") is True
    assert _is_json_serializable(123) is True
    assert _is_json_serializable(12.34) is True
    assert _is_json_serializable(True) is True
    assert _is_json_serializable(None) is True
    assert _is_json_serializable([1, 2, 3]) is True
    assert _is_json_serializable({"key": "value"}) is True


def test_is_json_serializable_returns_false_for_complex_objects():
    """Test that non-serializable objects return False."""

    # Custom class instance
    class CustomClass:
        pass

    assert _is_json_serializable(CustomClass()) is False

    # Function
    def test_func(x: int) -> int:
        return x

    assert _is_json_serializable(test_func) is False

    # Set (not JSON serializable)
    assert _is_json_serializable({1, 2, 3}) is False


# Tests for _create_serialization_metadata


def test_create_serialization_metadata_includes_type_info():
    """Test that metadata includes type information."""

    class CustomClass:
        pass

    obj = CustomClass()
    metadata = _create_serialization_metadata(obj)

    assert metadata["_type"] == "CustomClass"
    assert "_module" in metadata
    assert "_repr" in metadata
    assert "_serialization_error" in metadata


def test_create_serialization_metadata_truncates_long_repr():
    """Test that long repr strings are truncated."""
    # Create an object with a very long repr
    long_list = list(range(1000))
    metadata = _create_serialization_metadata(long_list)

    assert len(metadata["_repr"]) <= 203  # 200 + "..."
    assert metadata["_repr"].endswith("...")


def test_create_serialization_metadata_different_error_messages():
    """Test that error messages differ based on is_full_object parameter."""
    obj = object()

    metadata_full = _create_serialization_metadata(obj, is_full_object=True)
    metadata_partial = _create_serialization_metadata(obj, is_full_object=False)

    assert "Access the original object" in metadata_full["_serialization_error"]
    assert "Access the original object" not in metadata_partial["_serialization_error"]


# Tests for _serialize_with_metadata


def test_serialize_with_metadata_preserves_json_serializable_values():
    """Test that JSON-serializable values are preserved."""
    value = {"name": "test", "count": 123}
    result = _serialize_with_metadata(value)
    assert result == value


def test_serialize_with_metadata_replaces_non_serializable_dict_values():
    """Test that non-serializable values in dicts are replaced with metadata."""

    class CustomClass:
        pass

    value = {
        "good": "value",
        "bad": CustomClass(),
    }

    result = _serialize_with_metadata(value)

    assert result["good"] == "value"
    assert isinstance(result["bad"], dict)
    assert "_type" in result["bad"]
    assert result["bad"]["_type"] == "CustomClass"


def test_serialize_with_metadata_handles_non_dict_non_serializable():
    """Test that non-dict non-serializable values return metadata."""

    class CustomClass:
        pass

    obj = CustomClass()
    result = _serialize_with_metadata(obj)

    assert isinstance(result, dict)
    assert result["_type"] == "CustomClass"
    assert "_serialization_error" in result


def test_serialize_with_metadata_handles_mixed_dict():
    """Test serialization of dict with mixed serializable/non-serializable values."""

    class CustomClass:
        pass

    value = {
        "string": "test",
        "number": 42,
        "object": CustomClass(),
        "function": lambda: None,
    }

    result = _serialize_with_metadata(value)

    assert result["string"] == "test"
    assert result["number"] == 42
    assert result["object"]["_type"] == "CustomClass"
    assert result["function"]["_type"] == "function"


# Tests for JsonSafe with Pydantic


def test_json_safe_with_pydantic_serializable_values():
    """Test JsonSafe with Pydantic for fully serializable values."""

    class TestModel(BaseModel):
        data: JsonSafe

    model = TestModel(data={"key": "value", "count": 123})
    assert model.model_dump() == {"data": {"key": "value", "count": 123}}

    # Verify it can be JSON serialized
    json_str = model.model_dump_json()
    assert json.loads(json_str) == {"data": {"key": "value", "count": 123}}


def test_json_safe_with_pydantic_non_serializable_values():
    """Test JsonSafe with Pydantic for non-serializable values."""

    class CustomClass:
        pass

    class TestModel(BaseModel):
        data: JsonSafe

    obj = CustomClass()
    model = TestModel(data=obj)
    result = model.model_dump()

    assert result["data"]["_type"] == "CustomClass"
    assert "_serialization_error" in result["data"]

    # Verify it can be JSON serialized
    json_str = model.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["data"]["_type"] == "CustomClass"


def test_json_safe_with_pydantic_mixed_dict():
    """Test JsonSafe with Pydantic for dict with mixed values."""

    class CustomClass:
        pass

    class TestModel(BaseModel):
        data: JsonSafe

    model = TestModel(data={"good": "value", "bad": CustomClass()})
    result = model.model_dump()

    assert result["data"]["good"] == "value"
    assert result["data"]["bad"]["_type"] == "CustomClass"


# Tests for ULIDType


async def test_ulid_type_stores_and_retrieves_ulid():
    """Test that ULIDType correctly stores and retrieves ULID values."""
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class ULIDTestEntity(Base):
        __tablename__ = "ulid_test_entities"
        id: Mapped[int] = mapped_column(primary_key=True)
        ulid_field: Mapped[ULID] = mapped_column(ULIDType)

    db = SqliteDatabaseBuilder.in_memory().build()
    await db.init()

    # Add table
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create and store an entity with ULID
    test_ulid = ULID()
    async with db.session() as session:
        entity = ULIDTestEntity(ulid_field=test_ulid)
        session.add(entity)
        await session.commit()

        # Retrieve and verify
        result = await session.execute(select(ULIDTestEntity))
        retrieved = result.scalar_one()
        assert retrieved.ulid_field == test_ulid
        assert isinstance(retrieved.ulid_field, ULID)

    await db.dispose()


async def test_ulid_type_accepts_string_and_normalizes():
    """Test that ULIDType accepts string input and normalizes it."""
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class ULIDStringTestEntity(Base):
        __tablename__ = "ulid_string_test_entities"
        id: Mapped[int] = mapped_column(primary_key=True)
        ulid_field: Mapped[ULID] = mapped_column(ULIDType)

    db = SqliteDatabaseBuilder.in_memory().build()
    await db.init()

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create ULID as string
    test_ulid = ULID()
    ulid_str = str(test_ulid)

    # Insert in one session
    async with db.session() as session:
        entity = ULIDStringTestEntity(ulid_field=ulid_str)  # type: ignore
        session.add(entity)
        await session.commit()

    # Retrieve in a fresh session to ensure process_result_value is called
    async with db.session() as session:
        result = await session.execute(select(ULIDStringTestEntity))
        retrieved = result.scalar_one()
        assert isinstance(retrieved.ulid_field, ULID)
        assert str(retrieved.ulid_field) == ulid_str

    await db.dispose()


async def test_ulid_type_handles_none():
    """Test that ULIDType correctly handles None values."""
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class ULIDNoneTestEntity(Base):
        __tablename__ = "ulid_none_test_entities"
        id: Mapped[int] = mapped_column(primary_key=True)
        ulid_field: Mapped[ULID | None] = mapped_column(ULIDType, nullable=True)

    db = SqliteDatabaseBuilder.in_memory().build()
    await db.init()

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with db.session() as session:
        entity = ULIDNoneTestEntity(ulid_field=None)
        session.add(entity)
        await session.commit()

        result = await session.execute(select(ULIDNoneTestEntity))
        retrieved = result.scalar_one()
        assert retrieved.ulid_field is None

    await db.dispose()
