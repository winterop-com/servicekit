# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Documentation Standards

**IMPORTANT: All code must follow these documentation requirements:**

- **Every Python file**: One-line module docstring at top
- **Every class**: One-line docstring
- **Every method/function**: One-line docstring
- **Format**: Use triple quotes `"""docstring"""`
- **Style**: Keep concise - one line preferred

**Example:**
```python
"""Module for handling user authentication."""

class AuthManager:
    """Manages user authentication and authorization."""

    def verify_token(self, token: str) -> bool:
        """Verify JWT token validity."""
        ...
```

## Git Workflow

**Branch + PR workflow is highly recommended. Ask user before creating branches/PRs.**

**Branch naming:**
- `feat/*` - New features (aligns with `feat:` commits)
- `fix/*` - Bug fixes (aligns with `fix:` commits)
- `refactor/*` - Code refactoring (aligns with `refactor:` commits)
- `docs/*` - Documentation changes (aligns with `docs:` commits)
- `test/*` - Test additions/corrections (aligns with `test:` commits)
- `chore/*` - Dependencies, tooling, maintenance (aligns with `chore:` commits)

**Process:**
1. **Ask user** if they want a branch + PR for the change
2. Create branch from `main`: `git checkout -b feat/my-feature`
3. Make changes and commit: `git commit -m "feat: add new feature"`
4. Push: `git push -u origin feat/my-feature`
5. Create PR: `gh pr create --title "..." --body "..."`
6. Wait for manual review and merge

**Commit message prefixes:** `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`

**Commit message format:**
- Use conventional commit format: `<type>: <description>`
- Keep subject line under 72 characters
- Do NOT include "Co-Authored-By: Claude" or any Claude attribution in commits
- Focus on what changed and why, not who made the change

**PR requirements:**
- All tests must pass (`make test`)
- All linting must pass (`make lint`)
- Code coverage should not decrease
- Descriptive PR title and body

## Project Overview

`servicekit` is an async SQLAlchemy framework with FastAPI integration - a reusable foundation for building data services. It provides the core infrastructure patterns (database, repository, manager, CRUD, authentication, monitoring) without domain-specific modules.

**Key Principle:** Framework-agnostic core with FastAPI integration layer.

## Architecture

```
servicekit/
├── database.py          # Database, SqliteDatabase, SqliteDatabaseBuilder
├── models.py            # Base, Entity ORM classes
├── repository.py        # Repository, BaseRepository
├── manager.py           # Manager, BaseManager
├── schemas.py           # EntityIn, EntityOut, PaginatedResponse, JobRecord
├── scheduler.py         # JobScheduler, AIOJobScheduler
├── exceptions.py        # Error classes (NotFoundError, ValidationError, etc.)
├── logging.py           # Structured logging with request context
├── types.py             # ULIDType, JsonSafe
└── api/                 # FastAPI framework layer
    ├── router.py        # Router base class
    ├── crud.py          # CrudRouter, CrudPermissions
    ├── auth.py          # APIKeyMiddleware, key loading utilities
    ├── app.py           # AppManifest, App, AppLoader (static web app hosting)
    ├── service_builder.py   # BaseServiceBuilder (app factory)
    ├── dependencies.py      # get_database, get_session, get_scheduler
    ├── middleware.py        # Error handlers, logging middleware
    ├── monitoring.py        # OpenTelemetry setup
    ├── pagination.py        # Pagination helpers
    ├── utilities.py         # build_location_url, run_app
    ├── sse.py               # Server-Sent Events utilities
    └── routers/         # Generic routers
        ├── health.py    # HealthRouter
        ├── job.py       # JobRouter
        ├── system.py    # SystemRouter
        └── metrics.py   # MetricsRouter (Prometheus)
```

**Layer Rules:**
- Core layer (`*.py` files) is framework-agnostic
- API layer (`api/`) provides FastAPI integration
- Core never imports from API
- API imports from core

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

**Run:** `fastapi dev your_file.py` or `uvicorn your_module:app`

## BaseServiceBuilder API

**Builder methods:**
- `.with_health()` - Health check endpoint at `/health` (operational monitoring)
- `.with_system()` - System info endpoint at `/api/v1/system` (service metadata)
- `.with_monitoring()` - Prometheus metrics at `/metrics` + OpenTelemetry
- `.with_registration()` - Auto-register with orchestrator for service discovery
- `.with_app(path, prefix)` - Mount single static web app (HTML/JS/CSS)
- `.with_apps(path)` - Auto-discover and mount all apps in directory or package
- `.with_jobs(max_concurrency)` - Job scheduler at `/api/v1/jobs`
- `.with_logging()` - Structured logging with request tracing
- `.with_auth()` - API key authentication
- `.with_database(url)` - Database configuration
- `.include_router(router)` - Add custom routers
- `.on_startup(hook)` / `.on_shutdown(hook)` - Lifecycle hooks
- `.build()` - Returns FastAPI app

**Endpoint Design:**
- **Operational monitoring** (root level): `/health`, `/metrics` - infrastructure/monitoring for Kubernetes and Prometheus
- **API endpoints** (versioned): `/api/v1/*` - business logic and service metadata

## App System

The app system enables hosting static web applications (HTML/JS/CSS) alongside your FastAPI service using `.with_app()` and `.with_apps()`.

**App Structure:**
- Directory containing `manifest.json` and static files
- `manifest.json` defines name, version, prefix, and optional metadata
- Apps mount at custom URL prefixes (e.g., `/dashboard`, `/admin`)
- Uses FastAPI StaticFiles with SPA-style routing (serves index.html for directories)

**Manifest Format (manifest.json):**
```json
{
  "name": "My Dashboard",
  "version": "1.0.0",
  "prefix": "/dashboard",
  "description": "Optional description",
  "author": "Optional author",
  "entry": "index.html"
}
```

**Required fields:** `name`, `version`, `prefix`
**Optional fields:** `description`, `author`, `entry` (defaults to "index.html")

**Usage Examples:**

```python
# Mount single app from filesystem
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()
    .with_app("./apps/dashboard")  # Uses prefix from manifest
    .build()
)

# Override prefix
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_app("./apps/dashboard", prefix="/admin")  # Override manifest prefix
    .build()
)

# Auto-discover all apps in directory (filesystem)
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_apps("./apps")  # Discovers all subdirectories with manifest.json
    .build()
)

# Auto-discover all apps in package (bundled)
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_apps(("mypackage.apps", "webapps"))  # Discovers all apps in package subdirectory
    .build()
)

# Mount single app from Python package
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_app(("mypackage.apps", "dashboard"))  # Tuple syntax for single package app
    .build()
)
```

**Path Resolution:**
- **Filesystem paths:** Resolve relative to current working directory (where service runs)
- **Package resources:** Use tuple syntax `("package.name", "subpath")` to serve from installed packages
- Both `.with_app()` and `.with_apps()` support filesystem and package paths
- Allows libraries to ship default apps and projects to organize apps in their structure

**Restrictions:**
- Apps cannot mount at `/api` or `/api/**` (reserved for API endpoints)
- Prefix must start with `/` and cannot contain `..` (path traversal protection)
- Root apps ARE fully supported (mount at `/`)

**Override Semantics:**
- Duplicate prefixes use "last wins" semantics - later calls override earlier ones
- Useful for customizing default apps from libraries

**Known Limitation:**
- Root mounts intercept trailing slash redirects
- Use exact paths for API endpoints (e.g., `/api/v1/items` not `/api/v1/items/`)

**Validation:**
- Manifest validated with Pydantic (type checking, required fields)
- Prefix conflicts detected at build time (fail fast)
- Missing files (manifest.json, entry file) raise errors during load
- Apps mount AFTER routers, so API routes take precedence

**Example App Structure:**
```
apps/
└── dashboard/
    ├── manifest.json
    ├── index.html
    ├── style.css
    └── script.js
```

See `examples/app_hosting_api.py` and `examples/apps/` for complete working examples.

## Core Patterns

### Repository Pattern

Repositories handle low-level ORM data access.

**Naming conventions:**
- `find_*`: Single entity or None
- `find_all_*`: Sequence
- `exists_*`: Boolean
- `count`: Integer

**Example:**
```python
from servicekit import BaseRepository, Entity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

class User(Entity):
    """User entity for authentication."""

    __tablename__ = "users"
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column()

class UserRepository(BaseRepository[User, ULID]):
    """Repository for user data access."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize user repository."""
        super().__init__(session, User)

    async def find_by_username(self, username: str) -> User | None:
        """Find user by username."""
        from sqlalchemy import select

        stmt = select(self.model).where(self.model.username == username)
        result = await self.s.execute(stmt)
        return result.scalar_one_or_none()
```

**Important:** Always favor `repository` over `repo` in variable names and parameters.

### Manager Pattern

Managers add Pydantic validation and business logic on top of repositories.

**Example:**
```python
from servicekit import BaseManager, EntityIn, EntityOut

class UserIn(EntityIn):
    """Input schema for user operations."""

    username: str
    email: str

class UserOut(EntityOut):
    """Output schema for user responses."""

    username: str
    email: str

class UserManager(BaseManager[User, UserIn, UserOut, ULID]):
    """Manager for user business logic."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize user manager."""
        super().__init__(repository, User, UserOut)
        self.repository: UserRepository = repository

    async def find_by_username(self, username: str) -> UserOut | None:
        """Find user by username and return output schema."""
        user = await self.repository.find_by_username(username)
        return self._to_output_schema(user) if user else None
```

**Manager vs Repository:**
- **Repository:** Low-level ORM data access, works with Entity models
- **Manager:** Pydantic validation + business logic, works with In/Out schemas

### CRUD Router

Auto-generates REST endpoints with full CRUD operations.

**Example:**
```python
from servicekit.api import CrudRouter, CrudPermissions
from fastapi import Depends

def get_user_manager(session: AsyncSession = Depends(get_session)) -> UserManager:
    """Provide user manager for dependency injection."""
    return UserManager(UserRepository(session))

router = CrudRouter.create(
    prefix="/api/v1/users",
    tags=["Users"],
    entity_in_type=UserIn,
    entity_out_type=UserOut,
    manager_factory=get_user_manager,
    permissions=CrudPermissions(create=True, read=True, update=True, delete=False)
)
```

**Generated endpoints:**
- `POST /api/v1/users` - Create (if permissions allow)
- `GET /api/v1/users` - List all (pagination support with `?page=1&size=20`)
- `GET /api/v1/users/{id}` - Get by ID
- `PUT /api/v1/users/{id}` - Update
- `DELETE /api/v1/users/{id}` - Delete (if permissions allow)
- `GET /api/v1/users/$schema` - Pydantic schema

**Operation prefix:** `$` indicates operations (computed/derived data) vs resource access

## Database & Migrations

**Database classes:**
- `Database` - Generic base class (framework-agnostic)
- `SqliteDatabase` - SQLite-specific with WAL mode, pragmas, in-memory detection
- `SqliteDatabaseBuilder` - Fluent builder API (recommended)

**Builder example:**
```python
from servicekit import SqliteDatabaseBuilder

db = (
    SqliteDatabaseBuilder()
    .with_file("./data.db")
    .with_echo(True)
    .with_pool_size(10)
    .build()
)
```

**Migrations:**
- File DBs: Automatic Alembic migrations on `SqliteDatabase.init()`
- In-memory: Skip migrations (fast tests)

**Commands:**
```bash
make migrate MSG='description'  # Generate migration
make upgrade                    # Apply migrations (auto-applied on init)
```

**Workflow:**
1. Modify ORM models (subclasses of `Entity`)
2. Generate: `make migrate MSG='add user table'`
3. Review in `alembic/versions/`
4. Restart app (auto-applies)
5. Commit migration file

## API Responses

- Simple operations return pure objects
- Collections support optional pagination (`?page=1&size=20`)
- Errors follow RFC 9457 Problem Details with URN identifiers (`not-found`, `invalid-ulid`, `validation-failed`, `conflict`, `unauthorized`, `forbidden`)
- Schema endpoint auto-registered for all CrudRouters at `/$schema`

## Authentication

API key authentication with multiple key sources.

**File-based:**
```python
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_auth()  # Loads from ./api_keys.txt
    .build()
)
```

**Environment variable:**
```python
import os
os.environ["API_KEYS"] = "key1,key2,key3"

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_auth()
    .build()
)
```

**Docker secrets:**
```python
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_auth()  # Reads from /run/secrets/api_keys
    .build()
)
```

**Custom header:**
```python
from servicekit.api.auth import APIKeyMiddleware

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .build()
)

# Add custom auth middleware
middleware = APIKeyMiddleware(keys=["secret-key"], header_name="X-Custom-Auth")
app.add_middleware(APIKeyMiddleware, keys=["secret-key"], header_name="X-Custom-Auth")
```

See `examples/auth_*.py` for complete examples.

## Monitoring

Prometheus metrics and OpenTelemetry integration.

**Example:**
```python
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()
    .with_monitoring()  # Adds /metrics endpoint
    .build()
)
```

**Metrics provided:**
- HTTP request duration histograms
- HTTP request counter by status code
- SQLAlchemy connection pool metrics
- Process CPU, memory, and Python runtime metrics

See `examples/monitoring_api.py` for complete example.

## Job Scheduling

Background job execution with concurrency control.

**Example:**
```python
from servicekit.api.dependencies import get_scheduler

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()
    .with_jobs(max_concurrency=10)
    .build()
)

# Use scheduler via dependency injection
from fastapi import Depends, APIRouter
from servicekit.scheduler import JobScheduler

router = APIRouter()

@router.post("/process")
async def process_data(scheduler: JobScheduler = Depends(get_scheduler)):
    """Schedule background processing job."""

    async def background_task():
        # Do expensive work
        return {"status": "complete"}

    job_id = await scheduler.add_job(background_task)
    return {"job_id": str(job_id)}
```

**Job endpoints:**
- `GET /api/v1/jobs` - List all jobs (with optional `?status=` filter)
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Delete job
- `GET /api/v1/jobs/{id}/stream` - SSE stream for job updates

See `examples/job_scheduler_api.py` and `examples/job_scheduler_sse_api.py` for complete examples.

## Service Registration

Automatic service registration with orchestrator for service discovery in Docker Compose/Kubernetes.

**Example:**
```python
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()
    .with_registration()  # Auto-detect hostname, reads SERVICEKIT_ORCHESTRATOR_URL
    .build()
)
```

**Docker Compose:**
```yaml
services:
  my-service:
    image: my-service:latest
    environment:
      SERVICEKIT_ORCHESTRATOR_URL: http://orchestrator:9000/services/$register
      # SERVICEKIT_HOST auto-detected from container name (lowercase)
      # SERVICEKIT_PORT defaults to 8000
```

**Registration payload sent to orchestrator:**
```json
{
  "url": "http://my-service:8000",
  "info": {
    "display_name": "My Service",
    "version": "1.0.0",
    ...
  }
}
```

**Orchestrator response:**
```json
{
  "id": "01K83B5V85PQZ1HTH4DQ7NC9JM",
  "status": "registered",
  "service_url": "http://my-service:8000",
  "message": "Service registered successfully"
}
```

**Features:**
- **Hostname Auto-Detection**: Uses `socket.gethostname()` (Docker container name)
- **Retry Logic**: Configurable retries with delays (default: 5 attempts, 2s delay)
- **Custom Metadata**: Supports ServiceInfo subclasses with additional fields
- **Fail-Fast Mode**: Optional `fail_on_error=True` to abort startup on failure
- **Custom Environment Variables**: Override default env var names

**Configuration:**
```python
.with_registration(
    orchestrator_url="http://orchestrator:9000/services/$register",  # Or env var
    host="my-service",                                              # Or auto-detect
    port=8000,                                                      # Or env var or 8000
    max_retries=5,
    retry_delay=2.0,
    fail_on_error=False,
)
```

See `examples/registration/` for complete examples and `docs/guides/registration.md` for detailed guide.

## Code Quality

**Standards:**
- Python 3.13+, line length 120, type annotations required
- Double quotes, async/await, conventional commits
- Class order: public → protected → private
- `__all__` declarations only in `__init__.py` files

**Documentation Requirements:**
- Every Python file: one-line module docstring at top
- Every class: one-line docstring
- Every method/function: one-line docstring
- Use triple quotes `"""docstring"""`
- Keep concise - one line preferred

**Testing:**
```bash
make test      # Fast tests
make coverage  # With coverage
make lint      # Linting
```

**Always run `make lint` and `make test` after changes**

## Dependency Management

**Always use `uv`:**
```bash
uv add <package>          # Runtime dependency
uv add --dev <package>    # Dev dependency
uv add <package>@latest   # Update specific
uv lock --upgrade         # Update all
```

**Never manually edit `pyproject.toml` dependencies**

## Key Dependencies

- sqlalchemy[asyncio] >= 2.0
- aiosqlite >= 0.21
- pydantic >= 2.12
- fastapi[standard] >= 0.119
- python-ulid >= 3.1
- structlog >= 24.4
- opentelemetry-* (metrics and tracing)

## Examples

See the `examples/` directory for complete working examples:

- `core_api.py` - Basic CRUD service with custom User entity
- `job_scheduler_api.py` - Background job execution
- `job_scheduler_sse_api.py` - Job monitoring with Server-Sent Events
- `app_hosting_api.py` - Hosting static web apps
- `auth_basic.py` - API key authentication from file
- `auth_envvar.py` - API key from environment variable
- `auth_docker_secrets.py` - API key from Docker secrets
- `auth_custom_header.py` - Custom authentication header
- `monitoring_api.py` - Prometheus metrics and OpenTelemetry
- `registration/` - Service registration with orchestrator for service discovery

## Related Projects

- **[chapkit](https://github.com/dhis2-chap/chapkit)** - Domain modules (artifacts, configs, tasks, ML workflows) built on servicekit
