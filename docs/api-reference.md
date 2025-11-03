# API Reference

Complete API documentation for all servicekit modules, classes, and functions.

## Core Infrastructure

Framework-agnostic infrastructure components.

### Database

::: servicekit.database

### Models

::: servicekit.models

### Repository

::: servicekit.repository

### Manager

::: servicekit.manager

### Schemas

::: servicekit.schemas

### Exceptions

::: servicekit.exceptions

### Scheduler

::: servicekit.scheduler

### Types

::: servicekit.types

### Logging

::: servicekit.logging

## FastAPI Layer

FastAPI-specific components for building web services.

### Service Builder

Service builder class for composing FastAPI applications.

#### BaseServiceBuilder

::: servicekit.api.service_builder.BaseServiceBuilder

#### ServiceInfo

::: servicekit.api.service_builder.ServiceInfo

### Routers

Base router classes and generic routers.

#### Router

::: servicekit.api.router.Router

#### CrudRouter

::: servicekit.api.crud.CrudRouter

#### CrudPermissions

::: servicekit.api.crud.CrudPermissions

#### HealthRouter

::: servicekit.api.routers.health.HealthRouter

#### JobRouter

::: servicekit.api.routers.job.JobRouter

#### SystemRouter

::: servicekit.api.routers.system.SystemRouter

#### MetricsRouter

::: servicekit.api.routers.metrics.MetricsRouter

### App System

Static web application hosting system.

#### AppLoader

::: servicekit.api.app.AppLoader

#### AppManifest

::: servicekit.api.app.AppManifest

#### App

::: servicekit.api.app.App

#### AppManager

::: servicekit.api.app.AppManager

#### AppInfo

::: servicekit.api.app.AppInfo

### Authentication

API key authentication middleware and utilities.

#### APIKeyMiddleware

::: servicekit.api.auth.APIKeyMiddleware

### Middleware

Error handling and logging middleware.

::: servicekit.api.middleware

### Dependencies

FastAPI dependency injection functions.

::: servicekit.api.dependencies

### Pagination

Pagination helpers for collection endpoints.

::: servicekit.api.pagination

### Utilities

Utility functions for FastAPI applications.

::: servicekit.api.utilities
