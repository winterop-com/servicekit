# Servicekit

> Async SQLAlchemy framework with FastAPI integration - reusable foundation for building data services

Servicekit is a framework-agnostic core library providing foundational infrastructure for building async Python services with FastAPI and SQLAlchemy.

## Features

- **Database Layer**: Async SQLAlchemy with SQLite support, connection pooling, and automatic migrations
- **Repository Pattern**: Generic repository base classes for data access
- **Manager Pattern**: Business logic layer with lifecycle hooks
- **CRUD API**: Auto-generated REST endpoints with full CRUD operations
- **Authentication**: API key middleware with file and environment variable support
- **Job Scheduling**: Async job scheduler with concurrency control
- **App Hosting**: Mount static web applications alongside your API
- **Monitoring**: Prometheus metrics and OpenTelemetry integration
- **Health Checks**: Flexible health check system with SSE streaming support
- **Error Handling**: RFC 9457 Problem Details for HTTP APIs
- **Logging**: Structured logging with request context

## Installation

```bash
pip install servicekit
```

## Quick Start

```python
from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()
    .with_database("sqlite+aiosqlite:///./data.db")
    .build()
)
```

## Architecture

```
servicekit/
├── database.py       # Database, SqliteDatabase, SqliteDatabaseBuilder
├── models.py         # Base, Entity ORM classes
├── repository.py     # Repository, BaseRepository
├── manager.py        # Manager, BaseManager
├── schemas.py        # EntityIn, EntityOut, PaginatedResponse
├── scheduler.py      # JobScheduler, AIOJobScheduler
├── exceptions.py     # Error classes
├── logging.py        # Structured logging
├── types.py          # ULIDType, JsonSafe
└── api/              # FastAPI framework layer
    ├── router.py     # Router base class
    ├── crud.py       # CrudRouter, CrudPermissions
    ├── auth.py       # API key authentication
    ├── app.py        # Static app hosting
    ├── middleware.py # Error handlers, logging
    └── routers/      # Health, Jobs, System, Metrics
```

## Key Components

### BaseServiceBuilder

```python
from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()                    # Health check endpoint
    .with_database(url)               # Database configuration
    .with_jobs(max_concurrency=10)   # Job scheduler
    .with_auth()                      # API key authentication
    .with_monitoring()                # Prometheus metrics
    .with_app("./webapp")             # Static web app
    .include_router(custom_router)   # Custom routes
    .build()
)
```

### Repository Pattern

```python
from servicekit import BaseRepository, Entity
from sqlalchemy.orm import Mapped, mapped_column

class User(Entity):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()

class UserRepository(BaseRepository[User, ULID]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
```

### CRUD Router

```python
from servicekit.api import CrudRouter, CrudPermissions

router = CrudRouter.create(
    prefix="/api/v1/users",
    tags=["Users"],
    entity_in_type=UserIn,
    entity_out_type=UserOut,
    manager_factory=get_user_manager,
    permissions=CrudPermissions(create=True, read=True, update=True, delete=False)
)
```

## Examples

See the `examples/` directory for complete working examples:

- `core_api.py` - Basic CRUD service
- `job_scheduler_api.py` - Background job execution
- `app_hosting_api.py` - Hosting static web apps
- `auth_basic.py` - API key authentication
- `monitoring_api.py` - Prometheus metrics

## Documentation

See `docs/` for comprehensive guides and API reference.

## Testing

```bash
make test      # Run tests
make lint      # Run linter
make coverage  # Test coverage
```

## License

AGPL-3.0-or-later

## Related Projects

- **[chapkit](https://github.com/dhis2-chap/chapkit)** - Domain modules (config, artifacts, tasks, ML) built on servicekit ([docs](https://dhis2-chap.github.io/chapkit))
