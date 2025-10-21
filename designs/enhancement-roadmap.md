# Servicekit & Chapkit Enhancement Roadmap

**Version:** 1.0
**Date:** 2025-10-21
**Status:** Draft

## Executive Summary

### Current State

**Servicekit** is a framework-agnostic core library (~3900 LOC) providing foundational infrastructure for building async Python services with FastAPI and SQLAlchemy. It implements core patterns (Repository, Manager, CRUD) with essential features including authentication, monitoring, job scheduling, and service registration.

**Chapkit** extends servicekit with domain-specific modules for ML/data services:
- **Artifacts**: Hierarchical data storage with parent-child relationships
- **Configs**: ML configuration management
- **Tasks**: Scheduled ML execution framework
- **ML**: Train/predict workflow abstractions

### Strategic Vision

This roadmap defines a phased approach to enhance servicekit and chapkit to support:

1. **Production-ready data services** with advanced querying, caching, and scalability
2. **Visualization extensions** for chap-core (data-in → Vega grammar out)
3. **Enterprise features** for multi-user, multi-tenant scenarios
4. **ML workflow improvements** for complex pipelines and monitoring

### Design Principles

- **Framework-agnostic core**: Core layer stays independent of FastAPI
- **Backward compatibility**: New features should not break existing code
- **Opt-in complexity**: Advanced features enabled via builder methods
- **Clear layering**: Core → API → Domain modules (chapkit)
- **Type safety**: Full type annotations, no runtime type checking

---

## Phase 1: Advanced Query & Data Access

**Goal:** Enable rich querying, filtering, and sorting for all CRUD endpoints

**Duration:** 2-3 weeks
**Priority:** High
**Dependencies:** None

### 1.1 Motivation

Current CRUD endpoints only support:
- List all entities (GET `/api/v1/users`)
- Pagination (`?page=1&size=20`)
- Find by ID (GET `/api/v1/users/{id}`)

**Missing capabilities:**
- Filtering: `?filter={"is_active": true, "role": "admin"}`
- Sorting: `?sort=-created_at,+name`
- Field selection: `?fields=id,name,email`
- Text search: `?search=alice`
- Range queries: `?created_at[gte]=2025-01-01`

**Use cases:**
- Visualization services need to filter datasets before generating charts
- Admin dashboards need sorted, filtered views
- Mobile clients need field selection to reduce bandwidth
- Search functionality for user-facing features

### 1.2 Technical Design

#### 1.2.1 Filter DSL

Add optional filtering to `BaseRepository.find_all()`:

```python
# Core layer (framework-agnostic)
from dataclasses import dataclass
from typing import Any

@dataclass
class FilterSpec:
    """Filter specification for queries."""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, like, in, not_in
    value: Any

@dataclass
class QueryOptions:
    """Query options for repository operations."""
    filters: list[FilterSpec] | None = None
    sort_by: list[tuple[str, str]] | None = None  # [(field, 'asc'|'desc')]
    fields: list[str] | None = None
    limit: int | None = None
    offset: int | None = None

class BaseRepository[T, IdT = ULID]:
    async def find_all(
        self,
        options: QueryOptions | None = None
    ) -> Sequence[T]:
        """Find entities with optional filtering and sorting."""
        query = select(self.model)

        if options:
            query = self._apply_filters(query, options.filters)
            query = self._apply_sorting(query, options.sort_by)
            query = self._apply_fields(query, options.fields)
            if options.limit:
                query = query.limit(options.limit)
            if options.offset:
                query = query.offset(options.offset)

        result = await self.s.execute(query)
        return result.scalars().all()
```

#### 1.2.2 API Layer Integration

Add query parameter parsing in `CrudRouter`:

```python
# API layer
from servicekit.api.query import parse_filter, parse_sort, parse_fields

@self.router.get("", response_model=list[OutSchemaT] | PaginatedResponse[OutSchemaT])
async def find_all(
    # Existing pagination
    page: int | None = None,
    size: int | None = None,
    # New query params
    filter: str | None = None,  # JSON: {"is_active": true}
    sort: str | None = None,    # CSV: "-created_at,+name"
    fields: str | None = None,  # CSV: "id,name,email"
    search: str | None = None,  # Full-text search
    manager: Manager = Depends(manager_factory),
) -> list[OutSchemaT] | PaginatedResponse[OutSchemaT]:
    options = QueryOptions(
        filters=parse_filter(filter, search),
        sort_by=parse_sort(sort),
        fields=parse_fields(fields),
    )

    if page is not None and size is not None:
        items, total = await manager.find_paginated(page, size, options)
        return create_paginated_response(items, total, page, size)

    return await manager.find_all(options)
```

#### 1.2.3 Filter Operators

| Operator | SQL | Example |
|----------|-----|---------|
| `eq` | `=` | `{"role": "admin"}` → `role = 'admin'` |
| `ne` | `!=` | `{"role[ne]": "guest"}` → `role != 'guest'` |
| `gt`, `gte` | `>`, `>=` | `{"age[gte]": 18}` → `age >= 18` |
| `lt`, `lte` | `<`, `<=` | `{"age[lt]": 65}` → `age < 65` |
| `like` | `LIKE` | `{"name[like]": "%alice%"}` → `name LIKE '%alice%'` |
| `in` | `IN` | `{"role[in]": ["admin", "moderator"]}` |
| `not_in` | `NOT IN` | `{"status[not_in]": ["deleted"]}` |

#### 1.2.4 Security Considerations

- **Allowlist fields**: Only allow filtering on explicitly allowed fields
- **SQL injection**: Use parameterized queries (already done by SQLAlchemy)
- **DoS protection**: Limit complexity (max 10 filters, max 5 sort fields)

```python
class CrudRouter:
    def __init__(
        self,
        # ...existing params...
        filterable_fields: set[str] | None = None,
        sortable_fields: set[str] | None = None,
        searchable_fields: set[str] | None = None,
    ):
        self.filterable_fields = filterable_fields or set()
        self.sortable_fields = sortable_fields or set()
        self.searchable_fields = searchable_fields or set()
```

### 1.3 PostgreSQL Support

**Current:** SQLite only
**Add:** PostgreSQL adapter with connection pooling

#### 1.3.1 Database Abstraction

```python
# servicekit/database.py
from enum import Enum

class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"

class PostgresDatabase(Database):
    """PostgreSQL database implementation."""

    def __init__(
        self,
        url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int = 3600,
    ):
        engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
```

#### 1.3.2 Builder Integration

```python
# servicekit/api/service_builder.py
class BaseServiceBuilder:
    def with_database(
        self,
        url: str | None = None,
        db_type: DatabaseType | None = None,
        pool_size: int = 5,
        **kwargs: Any,
    ) -> Self:
        """Configure database connection."""
        if url is None:
            url = "sqlite+aiosqlite:///:memory:"

        # Auto-detect database type from URL
        if "postgresql" in url:
            db = PostgresDatabase(url, pool_size=pool_size, **kwargs)
        else:
            db = SqliteDatabaseBuilder().with_url(url).build()

        set_database(db)
        return self
```

### 1.4 Implementation Tasks

- [ ] **1.4.1** Create `QueryOptions` and `FilterSpec` in core layer
- [ ] **1.4.2** Implement `_apply_filters()`, `_apply_sorting()`, `_apply_fields()` in `BaseRepository`
- [ ] **1.4.3** Add query parameter parsers in `servicekit/api/query.py`
- [ ] **1.4.4** Update `CrudRouter.find_all()` to accept query params
- [ ] **1.4.5** Add `filterable_fields`, `sortable_fields` configuration
- [ ] **1.4.6** Implement PostgreSQL database adapter
- [ ] **1.4.7** Update `BaseServiceBuilder.with_database()` for auto-detection
- [ ] **1.4.8** Add tests for filtering, sorting, field selection
- [ ] **1.4.9** Add tests for PostgreSQL connection pooling
- [ ] **1.4.10** Update documentation with query examples

### 1.5 Success Criteria

- [ ] **1.5.1** Can filter entities: GET `/api/v1/users?filter={"is_active": true}`
- [ ] **1.5.2** Can sort entities: GET `/api/v1/users?sort=-created_at,+name`
- [ ] **1.5.3** Can select fields: GET `/api/v1/users?fields=id,name,email`
- [ ] **1.5.4** Can combine filters, sort, fields, pagination
- [ ] **1.5.5** PostgreSQL connection works with pool configuration
- [ ] **1.5.6** All tests pass (95%+ coverage)
- [ ] **1.5.7** Documentation includes query guide

### 1.6 API Examples

```python
# List active users, sorted by name
GET /api/v1/users?filter={"is_active": true}&sort=+name

# Search users by email domain
GET /api/v1/users?filter={"email[like]": "%@example.com"}

# Get recent users (last 30 days)
GET /api/v1/users?filter={"created_at[gte]": "2025-09-21"}&sort=-created_at

# Paginated, filtered results with field selection
GET /api/v1/users?filter={"role": "admin"}&fields=id,username,email&page=1&size=20
```

---

## Phase 2: Performance & Caching

**Goal:** Add caching layer and batch operations for high-performance services

**Duration:** 2-3 weeks
**Priority:** High
**Dependencies:** Phase 1 (query options)

### 2.1 Motivation

Visualization services often:
- Receive the same requests repeatedly (same data → same Vega spec)
- Process large datasets that don't change frequently
- Need fast response times for good UX

**Current limitations:**
- No caching (every request hits database)
- No batch operations (inefficient for bulk imports)
- Single-item CRUD only

**Target performance:**
- Cache hit: <10ms response time
- Batch insert: 1000 entities in <1s
- Cache invalidation on entity updates

### 2.2 Technical Design

#### 2.2.1 Cache Abstraction

```python
# servicekit/cache.py
from abc import ABC, abstractmethod
from typing import Any

class Cache(ABC):
    """Abstract cache interface."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL (seconds)."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        ...

class InMemoryCache(Cache):
    """LRU cache implementation using cachetools."""

    def __init__(self, maxsize: int = 1000, ttl: int | None = None):
        from cachetools import TTLCache
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl or 3600)
```

#### 2.2.2 Cacheable Manager Mixin

```python
# servicekit/manager.py
class CacheableManager[InSchemaT, OutSchemaT, IdT](BaseManager[InSchemaT, OutSchemaT, IdT]):
    """Manager with automatic caching support."""

    def __init__(
        self,
        repository: Repository,
        model: type,
        out_schema: type[OutSchemaT],
        cache: Cache | None = None,
        cache_ttl: int = 3600,
    ):
        super().__init__(repository, model, out_schema)
        self._cache = cache
        self._cache_ttl = cache_ttl

    async def find_by_id(self, id: IdT) -> OutSchemaT | None:
        """Find entity with caching."""
        if self._cache:
            cache_key = f"{self.model.__tablename__}:{id}"
            cached = await self._cache.get(cache_key)
            if cached:
                return self.out_schema.model_validate(cached)

        entity = await super().find_by_id(id)

        if entity and self._cache:
            await self._cache.set(
                cache_key,
                entity.model_dump(),
                ttl=self._cache_ttl,
            )

        return entity

    async def save(self, data: InSchemaT) -> OutSchemaT:
        """Save entity and invalidate cache."""
        entity = await super().save(data)

        if self._cache and hasattr(entity, 'id'):
            cache_key = f"{self.model.__tablename__}:{entity.id}"
            await self._cache.delete(cache_key)

        return entity
```

#### 2.2.3 Batch Operations

```python
# servicekit/repository.py
class BaseRepository[T, IdT]:
    async def save_all_bulk(self, entities: Sequence[T]) -> None:
        """Bulk insert entities (no refresh, faster)."""
        self.s.add_all(entities)
        await self.s.flush()

# servicekit/manager.py
class BaseManager[InSchemaT, OutSchemaT, IdT]:
    async def save_all_bulk(
        self,
        items: Iterable[InSchemaT],
        batch_size: int = 1000,
    ) -> int:
        """Bulk save entities in batches."""
        entities = [self._to_model(item) for item in items]
        total = 0

        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            await self.repository.save_all_bulk(batch)
            total += len(batch)

        await self.repository.commit()
        return total
```

#### 2.2.4 API Integration

```python
# servicekit/api/crud.py
class CrudRouter:
    def _register_bulk_create_route(self):
        """Register bulk create endpoint."""

        @self.router.post(
            "/$bulk",
            status_code=status.HTTP_201_CREATED,
            response_model=BulkOperationResult,
        )
        async def bulk_create(
            entities: list[InSchemaT],
            manager: Manager = Depends(self.manager_factory),
        ) -> BulkOperationResult:
            """Create multiple entities in bulk."""
            if len(entities) > 1000:
                raise BadRequestError("Maximum 1000 entities per request")

            created_count = await manager.save_all_bulk(entities)

            return BulkOperationResult(
                success=True,
                created=created_count,
                updated=0,
                deleted=0,
            )
```

### 2.3 Implementation Tasks

- [ ] **2.3.1** Create `Cache` interface and `InMemoryCache` implementation
- [ ] **2.3.2** Add `CacheableManager` mixin class
- [ ] **2.3.3** Implement `save_all_bulk()` in repository and manager
- [ ] **2.3.4** Add `POST /$bulk` endpoint to `CrudRouter`
- [ ] **2.3.5** Add cache configuration to `BaseServiceBuilder`
- [ ] **2.3.6** Implement cache invalidation on updates/deletes
- [ ] **2.3.7** Add cache metrics (hit rate, size)
- [ ] **2.3.8** Add Redis cache implementation (optional)
- [ ] **2.3.9** Add tests for caching behavior
- [ ] **2.3.10** Add tests for bulk operations
- [ ] **2.3.11** Update documentation with caching guide

### 2.4 Success Criteria

- [ ] **2.4.1** Cache hit response time <10ms
- [ ] **2.4.2** Bulk insert 1000 entities in <1s
- [ ] **2.4.3** Cache invalidates on entity updates
- [ ] **2.4.4** Can configure cache TTL per manager
- [ ] **2.4.5** Metrics show cache hit rate
- [ ] **2.4.6** All tests pass (95%+ coverage)

### 2.5 Builder API

```python
from servicekit import InMemoryCache
from servicekit.api import BaseServiceBuilder

cache = InMemoryCache(maxsize=10000, ttl=3600)

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_database()
    .with_cache(cache)  # Enable global cache
    .build()
)

# Per-manager caching
class UserManager(CacheableManager[UserIn, UserOut, ULID]):
    def __init__(self, repo: UserRepository, cache: Cache):
        super().__init__(repo, User, UserOut, cache=cache, cache_ttl=1800)
```

---

## Phase 3: Data Management Features

**Goal:** Add file storage, soft deletes, and audit logging

**Duration:** 2-3 weeks
**Priority:** Medium
**Dependencies:** Phase 1

### 3.1 File/Blob Storage Abstraction

**Motivation:** Visualization services need to store generated Vega specs, large datasets, model artifacts

#### 3.1.1 Storage Interface

```python
# servicekit/storage.py
from abc import ABC, abstractmethod
from pathlib import Path

class Storage(ABC):
    """Abstract storage interface for files and blobs."""

    @abstractmethod
    async def save(self, key: str, data: bytes) -> str:
        """Save data and return storage URL."""
        ...

    @abstractmethod
    async def load(self, key: str) -> bytes:
        """Load data by key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data by key."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...

class LocalStorage(Storage):
    """Local filesystem storage."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, key: str, data: bytes) -> str:
        path = self.base_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"file://{path}"
```

#### 3.1.2 File Metadata Tracking

```python
# servicekit/models.py
class FileEntity(Entity):
    """Base entity for file metadata."""

    __tablename__ = "files"

    key: Mapped[str] = mapped_column(unique=True, index=True)
    filename: Mapped[str] = mapped_column()
    content_type: Mapped[str] = mapped_column()
    size_bytes: Mapped[int] = mapped_column()
    storage_url: Mapped[str] = mapped_column()
```

### 3.2 Soft Deletes

**Motivation:** Enable data recovery, audit compliance

```python
# servicekit/models.py
class SoftDeleteEntity(Entity):
    """Base entity with soft delete support."""

    __abstract__ = True

    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

# servicekit/repository.py
class SoftDeleteRepository[T, IdT](BaseRepository[T, IdT]):
    """Repository with soft delete support."""

    async def delete_by_id(self, id: IdT) -> None:
        """Soft delete entity."""
        entity = await self.find_by_id(id)
        if entity:
            entity.deleted_at = datetime.now(timezone.utc)
            await self.save(entity)

    async def find_all(self, include_deleted: bool = False) -> Sequence[T]:
        """Find entities, excluding soft-deleted by default."""
        query = select(self.model)
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        result = await self.s.execute(query)
        return result.scalars().all()
```

### 3.3 Audit Logging

**Motivation:** Track who changed what and when

```python
# servicekit/audit.py
class AuditLog(Entity):
    """Audit log entry."""

    __tablename__ = "audit_logs"

    entity_type: Mapped[str] = mapped_column(index=True)
    entity_id: Mapped[str] = mapped_column(index=True)
    action: Mapped[str] = mapped_column()  # create, update, delete
    user_id: Mapped[str | None] = mapped_column()
    changes: Mapped[dict] = mapped_column(type_=JsonSafe)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

# servicekit/manager.py
class AuditableManager[InSchemaT, OutSchemaT, IdT](BaseManager[InSchemaT, OutSchemaT, IdT]):
    """Manager with automatic audit logging."""

    async def save(self, data: InSchemaT) -> OutSchemaT:
        entity = await super().save(data)

        # Log audit entry
        await self._log_audit(
            entity_id=str(entity.id),
            action="create" if not hasattr(data, 'id') else "update",
            changes=data.model_dump(),
        )

        return entity
```

### 3.4 Implementation Tasks

- [ ] **3.4.1** Create `Storage` interface and `LocalStorage` implementation
- [ ] **3.4.2** Add `FileEntity` model and CRUD endpoints
- [ ] **3.4.3** Implement `SoftDeleteEntity` and `SoftDeleteRepository`
- [ ] **3.4.4** Add `AuditLog` model and `AuditableManager`
- [ ] **3.4.5** Add storage configuration to `BaseServiceBuilder`
- [ ] **3.4.6** Implement S3-compatible storage (optional)
- [ ] **3.4.7** Add file upload/download endpoints
- [ ] **3.4.8** Add audit log router for querying logs
- [ ] **3.4.9** Add tests for storage, soft deletes, audit logging
- [ ] **3.4.10** Update documentation

### 3.5 Success Criteria

- [ ] **3.5.1** Can store/retrieve files via API
- [ ] **3.5.2** Soft-deleted entities hidden by default
- [ ] **3.5.3** All entity changes logged in audit table
- [ ] **3.5.4** Storage abstraction works with local and S3
- [ ] **3.5.5** All tests pass (95%+ coverage)

---

## Phase 4: API Capabilities

**Goal:** Rate limiting, WebSockets, data export

**Duration:** 2 weeks
**Priority:** Medium
**Dependencies:** Phase 1

### 4.1 Rate Limiting

```python
# servicekit/api/middleware.py
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int | None = None,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute * 2
        self._buckets: dict[str, tuple[int, datetime]] = {}

# servicekit/api/service_builder.py
class BaseServiceBuilder:
    def with_rate_limiting(
        self,
        requests_per_minute: int = 60,
        burst_size: int | None = None,
    ) -> Self:
        """Add rate limiting middleware."""
        limiter = RateLimiter(requests_per_minute, burst_size)
        self._app.middleware("http")(limiter.middleware)
        return self
```

### 4.2 WebSocket Support

```python
# servicekit/api/websocket.py
from fastapi import WebSocket

class WebSocketRouter(Router):
    """Base class for WebSocket endpoints."""

    def __init__(self, prefix: str, tags: list[str]):
        super().__init__(prefix, tags)

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Override this method to handle WebSocket connections."""
        raise NotImplementedError
```

### 4.3 Data Export

```python
# servicekit/api/export.py
from fastapi.responses import StreamingResponse
import csv

class CrudRouter:
    def _register_export_route(self):
        """Register CSV export endpoint."""

        @self.router.get(
            "/$export",
            response_class=StreamingResponse,
        )
        async def export_csv(
            filter: str | None = None,
            sort: str | None = None,
            manager: Manager = Depends(self.manager_factory),
        ):
            """Export entities as CSV."""
            options = QueryOptions(
                filters=parse_filter(filter),
                sort_by=parse_sort(sort),
            )

            entities = await manager.find_all(options)

            # Stream CSV response
            async def generate_csv():
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=...)
                writer.writeheader()
                for entity in entities:
                    writer.writerow(entity.model_dump())
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)

            return StreamingResponse(
                generate_csv(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=export.csv"},
            )
```

### 4.4 Implementation Tasks

- [ ] **4.4.1** Implement token bucket rate limiter
- [ ] **4.4.2** Add rate limiting middleware
- [ ] **4.4.3** Create `WebSocketRouter` base class
- [ ] **4.4.4** Implement CSV export endpoint
- [ ] **4.4.5** Add Excel export (optional)
- [ ] **4.4.6** Add tests for rate limiting
- [ ] **4.4.7** Add tests for WebSocket connections
- [ ] **4.4.8** Add tests for CSV export
- [ ] **4.4.9** Update documentation

### 4.5 Success Criteria

- [ ] **4.5.1** Rate limiting blocks excessive requests
- [ ] **4.5.2** WebSocket connections work for real-time updates
- [ ] **4.5.3** Can export CRUD data as CSV
- [ ] **4.5.4** All tests pass (95%+ coverage)

---

## Phase 5: Extension Patterns

**Goal:** Patterns for building specialized services (visualization, reporting, etc.)

**Duration:** 2-3 weeks
**Priority:** High (for visualization use case)
**Dependencies:** Phase 1, 2

### 5.1 Transformation Service Pattern

**Motivation:** Many services follow data-in → transform → data-out pattern (e.g., DataFrame → Vega spec)

**Status:** ✅ **COMPLETED** - Universal DataFrame schema and Vega visualization example implemented

#### 5.1.0 Universal Data Schema (servicekit.data)

**Implemented:** Universal `DataFrame` schema for multi-library data interchange

The `servicekit.data` module provides a library-agnostic DataFrame schema that works with pandas, polars, xarray, and plain Python:

```python
# servicekit/data/dataframe.py
class DataFrame(BaseModel):
    """Universal Pydantic schema for tabular data from any library."""

    columns: list[str]
    data: list[list[Any]]

    # Library-specific conversions (optional dependencies)
    @classmethod
    def from_pandas(cls, df: Any) -> Self: ...

    @classmethod
    def from_polars(cls, df: Any) -> Self: ...

    @classmethod
    def from_xarray(cls, da: Any) -> Self: ...

    # Always available (no dependencies)
    @classmethod
    def from_dict(cls, data: dict[str, list[Any]]) -> Self: ...

    @classmethod
    def from_records(cls, records: list[dict[str, Any]]) -> Self: ...

    def to_pandas(self) -> Any: ...
    def to_polars(self) -> Any: ...
    def to_dict(self, orient: Literal["dict", "list", "records"] = "dict") -> Any: ...
```

**Key features:**
- Core schema requires only `columns` and `data` (no library dependencies)
- Library-specific methods use runtime imports with clear error messages
- Optional dependencies: `servicekit[data]` for pandas, `servicekit[polars]`, `servicekit[xarray]`
- Backwards compatible: `PandasDataFrame` alias maintained
- CSV support would be trivial to add (no dependencies needed)

**Installation:**
```bash
uv add 'servicekit[data]'      # pandas support
uv add 'servicekit[polars]'    # polars support
uv add 'servicekit[xarray]'    # xarray support
```

See: `src/servicekit/data/` and `examples/vega_visualization/`

#### 5.1.1 Transformation Router

```python
# servicekit/api/transformation.py
from abc import abstractmethod

class TransformationRouter[RequestT: BaseModel, ResponseT: BaseModel](Router):
    """Router for stateless transformation endpoints."""

    def __init__(
        self,
        prefix: str,
        tags: list[str],
        request_type: type[RequestT],
        response_type: type[ResponseT],
        cache: Cache | None = None,
        cache_ttl: int = 3600,
    ):
        self.request_type = request_type
        self.response_type = response_type
        self._cache = cache
        self._cache_ttl = cache_ttl
        super().__init__(prefix, tags)

    @abstractmethod
    async def transform(self, request: RequestT) -> ResponseT:
        """Transform request to response."""
        ...

    def _register_routes(self) -> None:
        """Register transformation endpoint."""

        @self.router.post(
            "/$transform",
            response_model=self.response_type,
            status_code=status.HTTP_200_OK,
        )
        async def transform_endpoint(
            request: self.request_type,
        ) -> ResponseT:
            # Check cache
            if self._cache:
                cache_key = self._compute_cache_key(request)
                cached = await self._cache.get(cache_key)
                if cached:
                    return self.response_type.model_validate(cached)

            # Transform
            response = await self.transform(request)

            # Cache result
            if self._cache:
                await self._cache.set(
                    cache_key,
                    response.model_dump(),
                    ttl=self._cache_ttl,
                )

            return response

    def _compute_cache_key(self, request: RequestT) -> str:
        """Compute cache key from request."""
        import hashlib
        request_json = request.model_dump_json()
        return hashlib.sha256(request_json.encode()).hexdigest()
```

#### 5.1.2 Vega Visualization Service Example

**Implemented:** Complete proof-of-concept Vega visualization service at `examples/vega_visualization/`

The example demonstrates the Transformation Router pattern using the `Router` base class:

```python
# examples/vega_visualization/main.py
from servicekit.data import DataFrame
from servicekit.api import Router, BaseServiceBuilder

class VegaGenerateRequest(BaseModel):
    """Request to generate a Vega-Lite specification from data."""
    data: DataFrame  # Universal schema supporting pandas/polars/xarray
    chart_type: str  # line, bar, scatter, heatmap, boxplot, histogram
    x_field: str | None = None
    y_field: str | None = None
    color_field: str | None = None
    aggregate: str | None = None  # mean, sum, count, median, min, max

class VegaResponse(BaseModel):
    """Response containing Vega-Lite specification."""
    spec: dict[str, Any]
    row_count: int
    columns: list[str]

class VegaRouter(Router):
    """Router for generating Vega-Lite visualizations from DataFrame."""

    def _register_routes(self) -> None:
        @self.router.post("/$generate", response_model=VegaResponse)
        async def generate_vega(request: VegaGenerateRequest) -> VegaResponse:
            df = request.data.to_pandas()
            spec = self._build_spec(df, request.chart_type, ...)
            return VegaResponse(spec=spec, row_count=len(df), columns=df.columns.tolist())

        @self.router.post("/$aggregate", response_model=VegaResponse)
        async def aggregate_and_visualize(request: VegaAggregateRequest) -> VegaResponse:
            df = request.data.to_pandas()
            agg_df = self._aggregate_data(df, ...)
            spec = self._build_spec(agg_df, ...)
            return VegaResponse(spec=spec, ...)

# Build service
app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="Vega Visualization Service"))
    .with_health()
    .with_system()
    .with_monitoring()
    .with_landing_page()
    .include_router(vega_router)
    .build()
)
```

**Features implemented:**
- Multiple chart types: line, bar, scatter, heatmap, boxplot, histogram
- Data aggregation: group by fields with mean/sum/count/median/min/max
- Multi-format input: Works with pandas, polars, xarray, dicts, records via DataFrame schema
- RESTful API: `POST /$generate` and `POST /$aggregate` endpoints
- Full Pydantic validation
- Docker deployment ready

**Ready for caching integration** (Phase 2.2)

See: `examples/vega_visualization/` with complete README and curl examples

### 5.2 Schema Registry

**Motivation:** Version API schemas, track breaking changes

```python
# servicekit/schema_registry.py
class SchemaVersion(Entity):
    """Versioned schema definition."""

    __tablename__ = "schema_versions"

    name: Mapped[str] = mapped_column(index=True)
    version: Mapped[str] = mapped_column()
    schema_json: Mapped[dict] = mapped_column(type_=JsonSafe)
    deprecated: Mapped[bool] = mapped_column(default=False)

class SchemaRegistry:
    """Registry for versioned schemas."""

    async def register(self, name: str, version: str, schema: type[BaseModel]) -> None:
        """Register a schema version."""
        ...

    async def get(self, name: str, version: str) -> type[BaseModel]:
        """Get schema by name and version."""
        ...
```

### 5.3 Event Bus / Webhooks

**Motivation:** Notify external systems of entity changes

```python
# servicekit/events.py
class EventBus:
    """Event bus for entity changes."""

    async def publish(self, event: str, data: dict) -> None:
        """Publish event to subscribers."""
        ...

    async def subscribe(self, event: str, handler: Callable) -> None:
        """Subscribe to events."""
        ...

# Usage in manager
class EventDrivenManager(BaseManager):
    async def save(self, data: InSchemaT) -> OutSchemaT:
        entity = await super().save(data)

        # Publish event
        await event_bus.publish(
            event=f"{self.model.__tablename__}.created",
            data={"id": str(entity.id), "entity": entity.model_dump()},
        )

        return entity
```

### 5.4 Implementation Tasks

- [ ] **5.4.0** ✅ **DONE** - Create universal `DataFrame` schema in `servicekit.data`
  - ✅ Core schema with `columns` and `data` fields
  - ✅ Library-specific conversions (pandas, polars, xarray) with runtime imports
  - ✅ Dict and records conversions (no dependencies)
  - ✅ Optional dependencies in pyproject.toml
  - ✅ Documentation with API reference and examples
  - ✅ Backwards compatibility alias `PandasDataFrame`
  - Future: Add CSV support (trivial, no dependencies needed)
- [ ] **5.4.1** Create `TransformationRouter` base class (pattern demonstrated in Vega example)
- [ ] **5.4.2** Add cache integration to `TransformationRouter`
- [ ] **5.4.3** ✅ **DONE** - Implement example Vega visualization service
  - ✅ Complete working example at `examples/vega_visualization/`
  - ✅ Multiple chart types: line, bar, scatter, heatmap, boxplot, histogram
  - ✅ Data aggregation support (group by, mean/sum/count/etc)
  - ✅ Uses DataFrame schema for multi-format input
  - ✅ RESTful API with `/$generate` and `/$aggregate` endpoints
  - ✅ Docker deployment configuration
  - ✅ Complete README with curl examples
- [ ] **5.4.4** Create `SchemaRegistry` for versioned schemas
- [ ] **5.4.5** Implement `EventBus` for publish/subscribe
- [ ] **5.4.6** Add webhook delivery system
- [ ] **5.4.7** Add tests for transformation pattern
- [ ] **5.4.8** Add tests for schema registry
- [ ] **5.4.9** Add tests for event bus
- [ ] **5.4.10** Update documentation with extension patterns guide

### 5.5 Success Criteria

- [ ] **5.5.0** ✅ **DONE** - Universal DataFrame schema works with multiple libraries
  - ✅ Supports pandas, polars, xarray via optional dependencies
  - ✅ Works with dicts and records without any dependencies
  - ✅ Clear error messages when optional libraries not installed
  - ✅ Backwards compatible with PandasDataFrame alias
- [ ] **5.5.1** `TransformationRouter` supports caching (ready for Phase 2.2 integration)
- [ ] **5.5.2** ✅ **PARTIAL** - Vega service functional (caching pending Phase 2.2)
  - ✅ Returns valid Vega-Lite specs for all chart types
  - ⏳ Caching integration pending (Phase 2.2)
- [ ] **5.5.3** Schema registry tracks versions
- [ ] **5.5.4** Event bus publishes entity changes
- [ ] **5.5.5** All tests pass (95%+ coverage)
- [ ] **5.5.6** ✅ **DONE** - Documentation shows how to build extensions
  - ✅ Complete README for Vega example with curl examples
  - ✅ API reference for DataFrame schema
  - ✅ Installation and usage examples

---

## Phase 6: Chapkit Enhancements

**Goal:** Enhance ML/data capabilities in chapkit

**Duration:** 3-4 weeks
**Priority:** Medium
**Dependencies:** Phase 1-5 (servicekit features)

### 6.1 Visualization Artifact Types

**Motivation:** Store Vega specs as artifacts with metadata

```python
# chapkit/artifact/schemas.py
class VegaArtifactData(BaseModel):
    """Vega specification artifact."""
    spec: dict[str, Any]
    data_hash: str
    chart_type: str
    generated_at: datetime

# Usage
artifact = await artifact_manager.save(ArtifactIn(
    name="disease-cases-timeseries",
    content_type="application/vnd.vega.v5+json",
    data=VegaArtifactData(
        spec=vega_spec,
        data_hash="abc123",
        chart_type="line",
        generated_at=datetime.now(),
    ),
))
```

### 6.2 ML Pipeline Enhancements

#### 6.2.1 Multi-Model Ensembles

```python
# chapkit/ml/ensemble.py
class EnsembleRunner(ModelRunnerProtocol):
    """Run multiple models and combine predictions."""

    def __init__(self, runners: list[ModelRunnerProtocol]):
        self.runners = runners

    async def train(self, config, data, geo):
        """Train all models."""
        models = [await runner.train(config, data, geo) for runner in self.runners]
        return {"models": models}

    async def predict(self, config, model, historic, future, geo):
        """Predict with all models and ensemble."""
        predictions = [
            await runner.predict(config, m, historic, future, geo)
            for runner, m in zip(self.runners, model["models"])
        ]

        # Ensemble predictions (average)
        ensemble = pd.concat(predictions).groupby(level=0).mean()
        return ensemble
```

#### 6.2.2 Model Versioning

```python
# chapkit/ml/versioning.py
class ModelVersion(Entity):
    """Track model versions."""

    __tablename__ = "model_versions"

    model_name: Mapped[str] = mapped_column(index=True)
    version: Mapped[str] = mapped_column()
    artifact_id: Mapped[ULID] = mapped_column(ForeignKey("artifacts.id"))
    metrics: Mapped[dict] = mapped_column(type_=JsonSafe)  # accuracy, rmse, etc.
    deployed: Mapped[bool] = mapped_column(default=False)
```

### 6.3 Advanced Task Features

#### 6.3.1 Task Dependencies

```python
# chapkit/task/models.py
class Task(Entity):
    """Task with dependencies."""

    dependencies: Mapped[list[ULID]] = mapped_column(type_=JsonSafe, default=list)

# chapkit/task/manager.py
class TaskManager:
    async def execute_with_dependencies(self, task_id: ULID) -> None:
        """Execute task after dependencies complete."""
        task = await self.find_by_id(task_id)

        # Wait for dependencies
        for dep_id in task.dependencies:
            dep_task = await self.find_by_id(dep_id)
            if dep_task.status != JobStatus.COMPLETED:
                raise RuntimeError(f"Dependency {dep_id} not completed")

        # Execute task
        await self.execute(task_id)
```

#### 6.3.2 Scheduled Tasks (Cron)

```python
# chapkit/task/scheduler.py
class ScheduledTask(Entity):
    """Task with cron schedule."""

    __tablename__ = "scheduled_tasks"

    task_id: Mapped[ULID] = mapped_column(ForeignKey("tasks.id"))
    cron_expression: Mapped[str] = mapped_column()  # "0 0 * * *"
    enabled: Mapped[bool] = mapped_column(default=True)
    last_run: Mapped[datetime | None] = mapped_column(default=None)
```

### 6.4 Integration Patterns

#### 6.4.1 Visualization Service Integration

```python
# Example: ML service with visualization endpoint
from chapkit.api import MLServiceBuilder
from servicekit.api import TransformationRouter

class PredictionVisualizationRouter(TransformationRouter):
    """Generate visualizations from predictions."""

    async def transform(self, request: VisualizationRequest):
        # Fetch prediction artifact
        prediction = await artifact_manager.find_by_id(request.artifact_id)

        # Generate Vega spec
        spec = generate_vega_spec(prediction.data)

        return VegaVisualizationResponse(spec=spec)

app = (
    MLServiceBuilder(info=info, config_schema=Config, hierarchy=HIERARCHY, runner=runner)
    .with_monitoring()
    .include_router(
        PredictionVisualizationRouter.create(
            prefix="/api/v1/visualizations",
            tags=["visualizations"],
        )
    )
    .build()
)
```

### 6.5 Implementation Tasks

- [ ] **6.5.1** Add `VegaArtifactData` schema to artifact module
- [ ] **6.5.2** Implement `EnsembleRunner` for multi-model predictions
- [ ] **6.5.3** Add `ModelVersion` entity and manager
- [ ] **6.5.4** Implement task dependencies in `TaskManager`
- [ ] **6.5.5** Add cron-based task scheduling
- [ ] **6.5.6** Create visualization integration example
- [ ] **6.5.7** Add tests for ensemble runner
- [ ] **6.5.8** Add tests for model versioning
- [ ] **6.5.9** Add tests for task dependencies
- [ ] **6.5.10** Update chapkit documentation

### 6.6 Success Criteria

- [ ] **6.6.1** Can store Vega specs as artifacts
- [ ] **6.6.2** Ensemble runner combines multiple models
- [ ] **6.6.3** Model versions tracked with metrics
- [ ] **6.6.4** Tasks can depend on other tasks
- [ ] **6.6.5** Cron scheduler runs tasks automatically
- [ ] **6.6.6** All tests pass (95%+ coverage)
- [ ] **6.6.7** Integration examples documented

---

## Implementation Timeline

### Month 1: Core Query & Performance
- Week 1-2: Phase 1 (Advanced Query & Data Access)
- Week 3-4: Phase 2 (Performance & Caching)

### Month 2: Data Management & API
- Week 1-2: Phase 3 (Data Management Features)
- Week 3-4: Phase 4 (API Capabilities)

### Month 3: Extension Patterns & Chapkit
- Week 1-2: Phase 5 (Extension Patterns)
- Week 3-4: Phase 6 (Chapkit Enhancements)

---

## Migration Strategy

### Backward Compatibility

All new features are **opt-in** via builder methods:

```python
# Existing code continues to work
app = BaseServiceBuilder(info=info).with_database().build()

# New features enabled explicitly
app = (
    BaseServiceBuilder(info=info)
    .with_database()
    .with_cache(InMemoryCache())  # Opt-in
    .with_rate_limiting()          # Opt-in
    .build()
)
```

### Deprecation Policy

1. Mark deprecated features with warnings (6 months)
2. Remove in next major version
3. Provide migration guide in CHANGELOG

---

## Testing Strategy

### Coverage Goals
- Core layer: 95%+ coverage
- API layer: 90%+ coverage
- Integration tests for all builder methods

### Test Categories
1. **Unit tests**: Repository, Manager, Router logic
2. **Integration tests**: Database, API endpoints
3. **Performance tests**: Caching, bulk operations
4. **E2E tests**: Full service builds

---

## Documentation Updates

### New Guides Needed
- Advanced querying and filtering
- Caching strategies
- Building transformation services
- Event-driven architectures
- ML model versioning
- Visualization service patterns

### API Reference
- Update all new classes/methods
- Add code examples for each feature
- Migration guides for breaking changes

---

## Success Metrics

### Performance
- Cache hit rate >80% for repeated requests
- Bulk operations 10x faster than individual saves
- Query response time <100ms for 1000 entities

### Code Quality
- Test coverage >90%
- Type coverage 100%
- Zero critical security vulnerabilities

### Developer Experience
- Clear documentation for all features
- Working examples for each pattern
- Migration path for all breaking changes

---

## Risks & Mitigations

### Risk: Breaking Changes
**Mitigation:** Strict backward compatibility, deprecation warnings, semantic versioning

### Risk: Complexity Creep
**Mitigation:** Keep core simple, advanced features opt-in, clear separation of concerns

### Risk: Performance Regression
**Mitigation:** Benchmark tests, performance budgets, profiling

### Risk: Database Migration Issues
**Mitigation:** Thorough testing, rollback scripts, migration validation

---

## Next Steps

1. **Review this roadmap** with stakeholders
2. **Prioritize phases** based on immediate needs
3. **Create GitHub issues** for each phase
4. **Start Phase 1** implementation
5. **Iterate based on feedback**

---

**Questions or feedback?** Please open an issue or discussion on GitHub.
