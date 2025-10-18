"""Tests for TaskRegistry functionality."""

from collections.abc import Generator

import pytest

from servicekit.task import TaskRegistry


@pytest.fixture(autouse=True)
def clear_registry() -> Generator[None, None, None]:
    """Clear registry before and after each test."""
    TaskRegistry.clear()
    yield
    TaskRegistry.clear()


def test_register_decorator() -> None:
    """Test registering a function using the decorator."""

    @TaskRegistry.register("test_func")
    def test_func() -> str:
        return "test"

    assert "test_func" in TaskRegistry.list_all()
    func = TaskRegistry.get("test_func")
    assert func() == "test"


def test_register_function_imperative() -> None:
    """Test registering a function imperatively."""

    def my_func() -> str:
        return "my result"

    TaskRegistry.register_function("my_func", my_func)

    assert "my_func" in TaskRegistry.list_all()
    func = TaskRegistry.get("my_func")
    assert func() == "my result"


def test_register_async_function() -> None:
    """Test registering an async function."""

    @TaskRegistry.register("async_func")
    async def async_func() -> str:
        return "async result"

    assert "async_func" in TaskRegistry.list_all()
    func = TaskRegistry.get("async_func")
    assert callable(func)


def test_duplicate_registration_decorator() -> None:
    """Test that duplicate registration raises ValueError."""

    @TaskRegistry.register("dup_func")
    def func1() -> str:
        return "first"

    with pytest.raises(ValueError, match="Task 'dup_func' already registered"):

        @TaskRegistry.register("dup_func")
        def func2() -> str:
            return "second"


def test_duplicate_registration_imperative() -> None:
    """Test that duplicate imperative registration raises ValueError."""

    def func1() -> str:
        return "first"

    def func2() -> str:
        return "second"

    TaskRegistry.register_function("dup_func", func1)

    with pytest.raises(ValueError, match="Task 'dup_func' already registered"):
        TaskRegistry.register_function("dup_func", func2)


def test_get_missing_function() -> None:
    """Test that getting a missing function raises KeyError."""
    with pytest.raises(KeyError, match="Task 'missing' not found in registry"):
        TaskRegistry.get("missing")


def test_list_all_empty() -> None:
    """Test listing all tasks when registry is empty."""
    assert TaskRegistry.list_all() == []


def test_list_all_multiple() -> None:
    """Test listing all registered tasks."""

    @TaskRegistry.register("func_a")
    def func_a() -> None:
        pass

    @TaskRegistry.register("func_c")
    def func_c() -> None:
        pass

    @TaskRegistry.register("func_b")
    def func_b() -> None:
        pass

    tasks = TaskRegistry.list_all()
    assert tasks == ["func_a", "func_b", "func_c"]  # Should be sorted


def test_clear() -> None:
    """Test clearing the registry."""

    @TaskRegistry.register("func1")
    def func1() -> None:
        pass

    @TaskRegistry.register("func2")
    def func2() -> None:
        pass

    assert len(TaskRegistry.list_all()) == 2

    TaskRegistry.clear()

    assert TaskRegistry.list_all() == []


def test_register_with_parameters() -> None:
    """Test registering function that accepts parameters."""

    @TaskRegistry.register("add_numbers")
    def add_numbers(a: int, b: int) -> int:
        return a + b

    func = TaskRegistry.get("add_numbers")
    assert func(5, 3) == 8
    assert func(a=10, b=20) == 30


def test_register_with_default_parameters() -> None:
    """Test registering function with default parameters."""

    @TaskRegistry.register("greet")
    def greet(name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"

    func = TaskRegistry.get("greet")
    assert func("World") == "Hello, World!"
    assert func("World", greeting="Hi") == "Hi, World!"
