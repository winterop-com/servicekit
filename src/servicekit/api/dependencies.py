"""Generic FastAPI dependency injection for database and scheduler."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from servicekit import Database
from servicekit.scheduler import Scheduler

from .app import AppManager

# Global database instance - should be initialized at app startup
_database: Database | None = None

# Global scheduler instance - should be initialized at app startup
_scheduler: Scheduler | None = None


def set_database(database: Database) -> None:
    """Set the global database instance."""
    global _database
    _database = database


def get_database() -> Database:
    """Get the global database instance."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call set_database() during app startup.")
    return _database


async def get_session(db: Annotated[Database, Depends(get_database)]) -> AsyncIterator[AsyncSession]:
    """Get a database session for dependency injection."""
    async with db.session() as session:
        yield session


def set_scheduler(scheduler: Scheduler) -> None:
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler


def get_scheduler() -> Scheduler:
    """Get the global scheduler instance."""
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call set_scheduler() during app startup.")
    return _scheduler


# Global app manager instance - should be initialized at app startup
_app_manager: AppManager | None = None


def set_app_manager(manager: AppManager) -> None:
    """Set the global app manager instance."""
    global _app_manager
    _app_manager = manager


def get_app_manager() -> AppManager:
    """Get the global app manager instance."""
    if _app_manager is None:
        raise RuntimeError("AppManager not initialized. Call set_app_manager() during app startup.")
    return _app_manager
