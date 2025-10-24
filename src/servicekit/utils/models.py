"""Utilities for discovering and analyzing SQLAlchemy models."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from servicekit.models import Base


def get_registered_tables(base: type["Base"] | Any) -> set[str]:
    """Get all table names registered with a declarative base.

    Args:
        base: SQLAlchemy declarative base class

    Returns:
        Set of table names registered with the base
    """
    return set(base.metadata.tables.keys())


def get_framework_tables() -> set[str]:
    """Get table names provided by servicekit/framework.

    This returns an empty set for servicekit itself, but can be overridden
    by frameworks building on servicekit (like chapkit) to declare their
    framework-provided tables.

    Returns:
        Set of framework table names (empty for base servicekit)
    """
    return set()


def has_custom_models(base: type["Base"] | Any, framework_tables: set[str] | None = None) -> bool:
    """Check if user has defined custom models beyond framework tables.

    Args:
        base: SQLAlchemy declarative base class
        framework_tables: Set of framework-provided table names. If None, uses get_framework_tables()

    Returns:
        True if custom models exist, False otherwise
    """
    if framework_tables is None:
        framework_tables = get_framework_tables()

    all_tables = get_registered_tables(base)
    return bool(all_tables - framework_tables)


def get_custom_tables(base: type["Base"] | Any, framework_tables: set[str] | None = None) -> set[str]:
    """Get table names for custom user models (excluding framework tables).

    Args:
        base: SQLAlchemy declarative base class
        framework_tables: Set of framework-provided table names. If None, uses get_framework_tables()

    Returns:
        Set of custom table names
    """
    if framework_tables is None:
        framework_tables = get_framework_tables()

    all_tables = get_registered_tables(base)
    return all_tables - framework_tables
