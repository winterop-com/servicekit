"""Tests for API dependency injection."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from servicekit import Database
from servicekit.api.app import AppManager
from servicekit.api.dependencies import (
    get_app_manager,
    get_database,
    get_scheduler,
    get_session,
    set_app_manager,
    set_database,
    set_scheduler,
)
from servicekit.scheduler import JobScheduler


@pytest.fixture(autouse=True)
def reset_dependencies(monkeypatch):
    """Reset global dependencies before each test."""
    # Import the module to access private variables
    from servicekit.api import dependencies

    # Reset all globals
    monkeypatch.setattr(dependencies, "_database", None)
    monkeypatch.setattr(dependencies, "_scheduler", None)
    monkeypatch.setattr(dependencies, "_app_manager", None)
    yield


def test_get_database_raises_when_not_initialized():
    """Test that get_database raises RuntimeError when not initialized."""
    with pytest.raises(RuntimeError, match="Database not initialized"):
        get_database()


def test_get_database_returns_set_database():
    """Test that get_database returns the database after set_database."""
    mock_database = MagicMock(spec=Database)
    set_database(mock_database)
    assert get_database() is mock_database


def test_get_scheduler_raises_when_not_initialized():
    """Test that get_scheduler raises RuntimeError when not initialized."""
    with pytest.raises(RuntimeError, match="Scheduler not initialized"):
        get_scheduler()


def test_get_scheduler_returns_set_scheduler():
    """Test that get_scheduler returns the scheduler after set_scheduler."""
    mock_scheduler = MagicMock(spec=JobScheduler)
    set_scheduler(mock_scheduler)
    assert get_scheduler() is mock_scheduler


def test_get_app_manager_raises_when_not_initialized():
    """Test that get_app_manager raises RuntimeError when not initialized."""
    with pytest.raises(RuntimeError, match="AppManager not initialized"):
        get_app_manager()


def test_get_app_manager_returns_set_app_manager():
    """Test that get_app_manager returns the app manager after set_app_manager."""
    mock_app_manager = MagicMock(spec=AppManager)
    set_app_manager(mock_app_manager)
    assert get_app_manager() is mock_app_manager


async def test_get_session_yields_session():
    """Test that get_session yields a session from the database."""
    # Create a mock database
    mock_database = MagicMock(spec=Database)

    # Create a mock session context manager
    mock_session = MagicMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_session
    mock_context_manager.__aexit__.return_value = None
    mock_database.session.return_value = mock_context_manager

    # Set the database
    set_database(mock_database)

    # Test the get_session dependency
    async for session in get_session(mock_database):
        assert session is mock_session
        break

    # Verify session was properly opened
    mock_database.session.assert_called_once()
