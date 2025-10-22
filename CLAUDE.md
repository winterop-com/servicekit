# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overall guidelines

- Be concise and to the point
- Follow existing code style and patterns
- Prioritize readability and maintainability
- Use type annotations consistently
- Write clear commit messages without Claude attribution
- Don't use emojis anywhere (in commit messages, docstrings, comments, etc.)
- Ask the user before creating branches or pull requests
- Always run tests and linting after making changes

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

**Commit message requirements:**
- NEVER include "Co-Authored-By: Claude" or similar AI attribution
- Keep messages concise and descriptive
- Focus on what changed and why

**PR requirements:**
- All tests must pass (`make test`)
- All linting must pass (`make lint`)
- Code coverage should not decrease
- Descriptive PR title and body

## Project Overview

`servicekit` is an async SQLAlchemy framework with FastAPI integration - a reusable foundation for building data services. It provides core infrastructure patterns (database, repository, manager, CRUD, authentication, monitoring) without domain-specific modules.

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
    ├── registration.py      # Service registration with orchestrator
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

## BaseServiceBuilder API

**Builder methods:**
- `.with_health()` - Health check endpoint at `/health`
- `.with_system()` - System info endpoint at `/api/v1/system`
- `.with_monitoring()` - Prometheus metrics at `/metrics` + OpenTelemetry
- `.with_registration()` - Auto-register with orchestrator for service discovery
- `.with_app(path, prefix)` - Mount single static web app
- `.with_apps(path)` - Auto-discover and mount all apps in directory or package
- `.with_jobs(max_concurrency)` - Job scheduler at `/api/v1/jobs`
- `.with_logging()` - Structured logging with request tracing
- `.with_auth()` - API key authentication
- `.with_database(url)` - Database configuration
- `.include_router(router)` - Add custom routers
- `.on_startup(hook)` / `.on_shutdown(hook)` - Lifecycle hooks
- `.build()` - Returns FastAPI app

**Endpoint Design:**
- **Operational monitoring** (root level): `/health`, `/metrics`
- **API endpoints** (versioned): `/api/v1/*`
- **Operations** (computed/derived): Use `$` prefix (e.g., `/api/v1/users/$schema`, `/services/$register`)

## Core Patterns

### Repository Pattern

Repositories handle low-level ORM data access.

**Naming conventions:**
- `find_*`: Single entity or None
- `find_all_*`: Sequence
- `exists_*`: Boolean
- `count`: Integer

### Manager Pattern

Managers add Pydantic validation and business logic on top of repositories.

**Manager vs Repository:**
- Repository: Low-level ORM data access, works with Entity models
- Manager: Pydantic validation + business logic, works with In/Out schemas

### Router Pattern

Extend `Router` base class and implement `_register_routes()`. Use `.create()` class method to return APIRouter instance.

### CRUD Router

Auto-generates REST endpoints: POST (create), GET (list/get), PUT (update), DELETE (delete), GET /$schema.

## Database & Migrations

- Use `SqliteDatabaseBuilder` for database setup
- File DBs: Automatic Alembic migrations on init
- In-memory: Skip migrations (fast tests)
- Commands: `make migrate MSG='description'`, `make upgrade`

**Workflow:**
1. Modify ORM models (Entity subclasses)
2. Generate: `make migrate MSG='description'`
3. Review in `alembic/versions/`
4. Restart app (auto-applies)
5. Commit migration file

## Naming Conventions

**IMPORTANT: Always use full descriptive names, never abbreviations**

- `self.repository` (not `self.repo`)
- `config_repository` (not `config_repo`)
- `artifact_repository` (not `artifact_repo`)

This applies to:
- Class attributes
- Local variables
- Function parameters
- Any other code references

**Rationale:** Full names improve code readability and maintainability.

## Authentication

API key authentication with multiple sources: file-based (`./api_keys.txt`), environment variable (`API_KEYS`), Docker secrets (`/run/secrets/api_keys`), or custom header.

## Service Registration

Services can auto-register with an orchestrator for discovery using `.with_registration()`.

**Key features:**
- Hostname auto-detection via `socket.gethostname()` (Docker container name)
- Configurable retry logic (default: 5 attempts, 2s delay)
- Custom environment variables support
- Orchestrator assigns ULID-based service IDs
- Endpoint: `POST /services/$register` returns `{"id": "...", "status": "registered", ...}`

See `examples/registration/` and `docs/guides/registration.md` for details.

## Code Quality

**Standards:**
- Python 3.13+, line length 120, type annotations required
- Double quotes, async/await, conventional commits
- Class order: public → protected → private
- `__all__` declarations only in `__init__.py` files

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
uv sync                   # Install all dependencies from pyproject.toml
```

**Important rules:**
- Never manually edit `pyproject.toml` dependencies
- Never use `uv pip` commands - always use `uv add`, `uv sync`, etc.
- `uv pip` is deprecated; use native uv commands that work with pyproject.toml

## Examples

See `examples/` directory for working examples:
- `core_api.py` - Basic CRUD service
- `job_scheduler_api.py` - Background jobs
- `job_scheduler_sse_api.py` - Job monitoring with SSE
- `app_hosting_api.py` - Static web apps
- `auth_*.py` - Various authentication methods
- `monitoring_api.py` - Prometheus metrics
- `registration/` - Service registration with orchestrator

**Postman Collections:**
- Each example with REST endpoints should include `postman_collection.json`
- Always name it exactly `postman_collection.json` (not service-specific names)

## Related Projects

- **[chapkit](https://github.com/dhis2-chap/chapkit)** - Domain modules (artifacts, configs, tasks, ML workflows) built on servicekit
