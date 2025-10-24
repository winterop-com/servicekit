# Servicekit Enhancement Roadmap

**Version:** 1.1
**Last Updated:** 2025-10-22
**Status:** In Progress


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
**Status:** Not Started

### 1.1 Motivation

Current CRUD endpoints only support basic operations (list all, pagination, find by ID).

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

### 1.2 Technical Approach

- Add `QueryOptions` and `FilterSpec` dataclasses in core layer
- Implement `_apply_filters()`, `_apply_sorting()`, `_apply_fields()` in `BaseRepository`
- Add query parameter parsers in `servicekit/api/query.py`
- Update `CrudRouter.find_all()` to accept query params with security allowlists
- Support PostgreSQL with connection pooling alongside SQLite

### 1.3 Implementation Tasks

- [ ] Create `QueryOptions` and `FilterSpec` in core layer
- [ ] Implement repository filter/sort/field methods
- [ ] Add query parameter parsers
- [ ] Update `CrudRouter` with query support
- [ ] Add field allowlists for security
- [ ] Implement PostgreSQL database adapter
- [ ] Update `BaseServiceBuilder.with_database()` for auto-detection
- [ ] Add comprehensive tests
- [ ] Update documentation with query examples

### 1.4 Success Criteria

- [ ] Can filter entities: GET `/api/v1/users?filter={"is_active": true}`
- [ ] Can sort entities: GET `/api/v1/users?sort=-created_at,+name`
- [ ] Can select fields: GET `/api/v1/users?fields=id,name,email`
- [ ] Can combine filters, sort, fields, pagination
- [ ] PostgreSQL connection works with pool configuration
- [ ] All tests pass (95%+ coverage)
- [ ] Documentation includes query guide

---

## Phase 2: Performance & Caching

**Goal:** Add caching layer and batch operations for high-performance services

**Duration:** 2-3 weeks
**Priority:** High
**Status:** Not Started
**Dependencies:** Phase 1

### 2.1 Motivation

Visualization services often:
- Receive the same requests repeatedly (same data → same Vega spec)
- Process large datasets that don't change frequently
- Need fast response times for good UX

**Target performance:**
- Cache hit: <10ms response time
- Batch insert: 1000 entities in <1s
- Cache invalidation on entity updates

### 2.2 Technical Approach

- Create abstract `Cache` interface with `InMemoryCache` implementation (LRU with TTL)
- Add `CacheableManager` mixin for automatic caching with invalidation
- Implement `save_all_bulk()` for batch operations
- Add `POST /$bulk` endpoint to `CrudRouter`
- Optional Redis cache implementation

### 2.3 Implementation Tasks

- [ ] Create `Cache` interface and `InMemoryCache` implementation
- [ ] Add `CacheableManager` mixin class
- [ ] Implement `save_all_bulk()` in repository and manager
- [ ] Add `POST /$bulk` endpoint to `CrudRouter`
- [ ] Add cache configuration to `BaseServiceBuilder`
- [ ] Implement cache invalidation on updates/deletes
- [ ] Add cache metrics (hit rate, size)
- [ ] Add Redis cache implementation (optional)
- [ ] Add comprehensive tests
- [ ] Update documentation with caching guide

### 2.4 Success Criteria

- [ ] Cache hit response time <10ms
- [ ] Bulk insert 1000 entities in <1s
- [ ] Cache invalidates on entity updates
- [ ] Can configure cache TTL per manager
- [ ] Metrics show cache hit rate
- [ ] All tests pass (95%+ coverage)

---

## Phase 3: Data Management Features

**Goal:** Add file storage, soft deletes, and audit logging

**Duration:** 2-3 weeks
**Priority:** Medium
**Status:** Not Started
**Dependencies:** Phase 1

### 3.1 Features

**File/Blob Storage Abstraction:**
- Abstract `Storage` interface for files and blobs
- `LocalStorage` implementation with path management
- `FileEntity` model for metadata tracking
- Optional S3-compatible storage

**Soft Deletes:**
- `SoftDeleteEntity` base class with `deleted_at` field
- `SoftDeleteRepository` that excludes deleted by default
- Option to include deleted entities in queries

**Audit Logging:**
- `AuditLog` entity tracking who changed what and when
- `AuditableManager` mixin for automatic logging
- Audit log router for querying logs

### 3.2 Implementation Tasks

- [ ] Create `Storage` interface and `LocalStorage` implementation
- [ ] Add `FileEntity` model and CRUD endpoints
- [ ] Implement `SoftDeleteEntity` and `SoftDeleteRepository`
- [ ] Add `AuditLog` model and `AuditableManager`
- [ ] Add storage configuration to `BaseServiceBuilder`
- [ ] Implement S3-compatible storage (optional)
- [ ] Add file upload/download endpoints
- [ ] Add audit log router
- [ ] Add comprehensive tests
- [ ] Update documentation

### 3.3 Success Criteria

- [ ] Can store/retrieve files via API
- [ ] Soft-deleted entities hidden by default
- [ ] All entity changes logged in audit table
- [ ] Storage abstraction works with local and S3
- [ ] All tests pass (95%+ coverage)

---

## Phase 4: API Capabilities

**Goal:** Rate limiting, WebSockets, data export

**Duration:** 2 weeks
**Priority:** Medium
**Status:** Not Started
**Dependencies:** Phase 1

### 4.1 Features

**Rate Limiting:**
- Token bucket rate limiter
- Configurable requests per minute and burst size
- Builder method: `.with_rate_limiting()`

**WebSocket Support:**
- `WebSocketRouter` base class for real-time endpoints
- Connection handling patterns

**Data Export:**
- `GET /$export` endpoint for CSV export
- Streaming responses for large datasets
- Optional Excel export

### 4.2 Implementation Tasks

- [ ] Implement token bucket rate limiter
- [ ] Add rate limiting middleware
- [ ] Create `WebSocketRouter` base class
- [ ] Implement CSV export endpoint
- [ ] Add Excel export (optional)
- [ ] Add comprehensive tests
- [ ] Update documentation

### 4.3 Success Criteria

- [ ] Rate limiting blocks excessive requests
- [ ] WebSocket connections work for real-time updates
- [ ] Can export CRUD data as CSV
- [ ] All tests pass (95%+ coverage)

---

## Phase 5: Extension Patterns

**Goal:** Patterns for building specialized services (visualization, reporting, etc.)

**Duration:** 1-2 weeks
**Priority:** Medium
**Status:** Not Started
**Dependencies:** Phase 1, 2

### 5.1 Transformation Service Pattern

- Extract `TransformationRouter` base class pattern from Vega example
- Integrate caching support (Phase 2.2)
- ~~Add PyArrow/Parquet support for DataFrame (optional - requires pyarrow dependency)~~

**Note:** DataFrame enhancements completed separately (feat/dataframe-enhancements branch) with 15 new methods for data manipulation, missing data handling, and utilities. The DataFrame now provides comprehensive data interchange capabilities using stdlib only. PyArrow/Parquet support deferred - users can convert to pandas/polars for advanced I/O formats.

### 5.2 Schema Registry

**Goal:** Version API schemas, track breaking changes

**Status:** Not Started

- `SchemaVersion` entity for versioned schema definitions
- `SchemaRegistry` for registering and retrieving schemas
- Schema deprecation tracking

### 5.3 Event Bus / Webhooks

**Goal:** Notify external systems of entity changes

**Status:** Not Started

- `EventBus` for publish/subscribe pattern
- Event-driven manager for automatic publishing
- Webhook delivery system

### 5.4 Implementation Tasks

- [ ] Extract `TransformationRouter` base class from Vega example
- [ ] Add cache integration to `TransformationRouter`
- [ ] Create `SchemaRegistry` for versioned schemas
- [ ] Implement `EventBus` for publish/subscribe
- [ ] Add webhook delivery system
- [ ] Add PyArrow/Parquet support (optional)

### 5.5 Success Criteria

- [ ] `TransformationRouter` supports caching
- [ ] Schema registry tracks versions
- [ ] Event bus publishes entity changes

---

## Phase 6: Chapkit Enhancements

**Goal:** Enhance ML/data capabilities in chapkit

**Duration:** 3-4 weeks
**Priority:** Medium
**Status:** Not Started
**Dependencies:** Phase 1-5 (servicekit features)

### 6.1 Visualization Artifact Types

Store Vega specs as artifacts with metadata using `VegaArtifactData` schema.

### 6.2 ML Pipeline Enhancements

**Multi-Model Ensembles:**
- `EnsembleRunner` for running multiple models and combining predictions
- Ensemble strategies (average, voting, weighted)

**Model Versioning:**
- `ModelVersion` entity tracking versions with metrics
- Deployment status tracking

### 6.3 Advanced Task Features

**Task Dependencies:**
- Tasks can depend on other tasks
- Automatic dependency resolution and execution order

**Scheduled Tasks (Cron):**
- `ScheduledTask` entity with cron expressions
- Automatic recurring task execution

### 6.4 Integration Patterns

Example: ML service with visualization endpoint combining chapkit ML capabilities with servicekit visualization patterns.

### 6.5 Implementation Tasks

- [ ] Add `VegaArtifactData` schema to artifact module
- [ ] Implement `EnsembleRunner` for multi-model predictions
- [ ] Add `ModelVersion` entity and manager
- [ ] Implement task dependencies in `TaskManager`
- [ ] Add cron-based task scheduling
- [ ] Create visualization integration example
- [ ] Add comprehensive tests
- [ ] Update chapkit documentation

### 6.6 Success Criteria

- [ ] Can store Vega specs as artifacts
- [ ] Ensemble runner combines multiple models
- [ ] Model versions tracked with metrics
- [ ] Tasks can depend on other tasks
- [ ] Cron scheduler runs tasks automatically
- [ ] All tests pass (95%+ coverage)
- [ ] Integration examples documented

---

## Implementation Timeline

### Month 1: Core Query & Performance
- Week 1-2: Phase 1 (Advanced Query & Data Access)
- Week 3-4: Phase 2 (Performance & Caching)

### Month 2: Data Management & API
- Week 1-2: Phase 3 (Data Management Features)
- Week 3-4: Phase 4 (API Capabilities)

### Month 3: Extension Patterns & Chapkit
- Week 1-2: Phase 5 (Extension Patterns - complete remaining items)
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

1. Prioritize remaining phases based on project needs
2. Create GitHub issues for Phase 1 tasks
3. Begin implementation of advanced query features
4. Continue iterating based on feedback

---

**Questions or feedback?** Please open an issue or discussion on GitHub.
