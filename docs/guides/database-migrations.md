# Database Migrations

ServiceKit provides CLI tools and utilities for managing database schema migrations using Alembic with async SQLAlchemy.

## Overview

Database migrations allow you to:

- Track schema changes over time
- Version control your database structure
- Apply schema updates across environments
- Roll back changes when needed

ServiceKit uses [Alembic](https://alembic.sqlalchemy.org/) configured for async SQLAlchemy operations.

## When You Need Migrations

You need migrations when:

1. **Using file-based databases** (e.g., SQLite files, PostgreSQL)
2. **Deploying to production** where you need version-controlled schema updates
3. **Working with custom models** that extend ServiceKit's `Entity` base class
4. **Collaborating with teams** who need consistent database schemas

You may NOT need migrations if:

- Using in-memory databases for testing
- Working on prototypes where schema changes frequently
- Using frameworks (like chapkit) that provide auto-migrations for their entities

## Quick Start

### 1. Initialize Migrations

```bash
# Create alembic directory structure
servicekit migrations init

# Or specify custom output directory
servicekit migrations init --output migrations
```

This creates:

```
alembic/
├── env.py              # Migration environment config
├── versions/           # Migration scripts directory
└── script.py.mako      # Migration template
alembic.ini             # Alembic configuration
```

### 2. Import Your Models

Edit `alembic/env.py` to import your models:

```python
# alembic/env.py
from servicekit import Base

# Import your models here to register them with Base
from myapp.models import User, Product  # noqa: F401

# ... rest of file
```

### 3. Generate Your First Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "initial schema"
```

This creates a migration file in `alembic/versions/` with upgrade and downgrade functions.

### 4. Review and Apply

```bash
# Review the generated migration file
cat alembic/versions/*_initial_schema.py

# Apply the migration
alembic upgrade head
```

## Configuration

### Database URL

Configure your database URL in `alembic.ini` or pass it at runtime:

```bash
# Edit alembic.ini
sqlalchemy.url = sqlite+aiosqlite:///./myapp.db

# Or pass at runtime
alembic -x db=sqlite+aiosqlite:///./myapp.db upgrade head
```

### Using with ServiceBuilder

Configure ServiceKit to use your migrations:

```python
from pathlib import Path
from servicekit import SqliteDatabaseBuilder
from servicekit.api import BaseServiceBuilder, ServiceInfo

# Configure database with migrations
db = (
    SqliteDatabaseBuilder.from_file("app.db")
    .with_migrations(enabled=True, alembic_dir=Path("alembic"))
    .build()
)

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_database(db)
    .with_health()
    .build()
)
```

The database will automatically apply pending migrations on startup.

## Common Workflows

### Creating a New Migration

After modifying your models:

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add email column to users"

# Review the generated file
cat alembic/versions/*_add_email_column_to_users.py

# Apply it
alembic upgrade head
```

### Viewing Migration Status

```bash
# Show current migration version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

### Rolling Back

```bash
# Downgrade one migration
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123

# Downgrade all
alembic downgrade base
```

### Creating Empty Migration

For data migrations or custom operations:

```bash
# Create empty migration file
alembic revision -m "populate default data"

# Edit the file and add your operations
# Then apply it
alembic upgrade head
```

## Model Discovery Utilities

ServiceKit provides utilities for detecting custom models:

```python
from servicekit import Base
from servicekit.utils import (
    get_registered_tables,
    has_custom_models,
    get_custom_tables,
)

# Get all tables registered with Base
all_tables = get_registered_tables(Base)
print(f"All tables: {all_tables}")

# Check if custom models exist
if has_custom_models(Base):
    custom = get_custom_tables(Base)
    print(f"Custom tables found: {custom}")
```

These utilities are useful for:

- Validating that models are properly imported
- Detecting when custom migrations are needed
- Building framework tools that extend ServiceKit

## Advanced Topics

### Multiple Databases

For multiple databases, create separate alembic directories:

```bash
servicekit migrations init --output alembic_main
servicekit migrations init --output alembic_analytics
```

Configure each with its own `alembic.ini` or use `-c` flag:

```bash
alembic -c alembic_main.ini upgrade head
alembic -c alembic_analytics.ini upgrade head
```

### Migration Testing

Test migrations in isolation:

```python
import tempfile
from pathlib import Path
from servicekit import SqliteDatabaseBuilder

async def test_migrations():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        db = (
            SqliteDatabaseBuilder.from_file(str(db_path))
            .with_migrations(enabled=True, alembic_dir=Path("alembic"))
            .build()
        )

        await db.init()  # Applies migrations

        # Test your schema here
        async with db.session() as session:
            # ... perform tests
            pass
```

### Custom Migration Helpers

Create reusable migration helpers for your framework:

```python
# myframework/migration_helpers.py
from typing import Any

def create_users_table(op: Any) -> None:
    """Reusable helper for creating users table."""
    op.create_table(
        "users",
        sa.Column("id", ULIDType(length=26), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
```

Then use in migrations:

```python
# alembic/versions/xxx_initial.py
from myframework.migration_helpers import create_users_table

def upgrade() -> None:
    create_users_table(op)
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Check current version
alembic current

# Apply pending migrations
alembic upgrade head
```

### "Can't locate revision identified by 'xxx'"

Your migrations directory may be out of sync. Check:

```bash
# Verify alembic.ini script_location
cat alembic.ini | grep script_location

# Ensure migrations directory exists
ls alembic/versions/
```

### Models not detected in autogenerate

Ensure models are imported in `alembic/env.py`:

```python
# Must import models BEFORE target_metadata assignment
from myapp.models import User, Product  # noqa: F401

target_metadata = Base.metadata
```

### Async/await issues

ServiceKit's templates handle async properly. If you see errors:

1. Ensure using `async_engine_from_config`
2. Verify `run_sync` wrapper for migrations
3. Check event loop creation in `run_migrations_online()`

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [ServiceKit API Reference](/api-reference/)
