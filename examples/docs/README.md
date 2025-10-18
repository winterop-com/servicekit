# Servicekit Examples - API Testing Guides

This directory contains comprehensive guides and Postman collections for testing Servicekit services.

## Core Examples

Basic CRUD services and infrastructure patterns:

- **core_api.py** - User CRUD service with custom repository and manager
- **core_cli.py** - CLI tool demonstrating programmatic API usage

## Authentication Examples

Secure your APIs with API key authentication:

- **auth_basic.py** - Basic authentication with file-based API keys (development)
- **auth_envvar.py** - Environment variable auth (recommended for production)
- **auth_docker_secrets.py** - Docker secrets file auth (most secure)
- **auth_custom_header.py** - Custom authentication header configuration

## Infrastructure Examples

Background jobs, monitoring, and app hosting:

- **job_scheduler_api.py** - Background job execution with concurrency control
- **job_scheduler_sse_api.py** - Real-time job monitoring with Server-Sent Events
- **monitoring_api.py** - Prometheus metrics and OpenTelemetry integration
- **app_hosting_api.py** - Static web application hosting alongside API

## Common Workflow

### 1. Start a Service

```bash
# Choose an example
fastapi dev examples/core_api.py
fastapi dev examples/auth_basic.py
fastapi dev examples/monitoring_api.py
```

Service runs at: `http://127.0.0.1:8000`

### 2. Check Health

```bash
curl http://127.0.0.1:8000/health
```

### 3. Explore Interactive Docs

Visit: `http://127.0.0.1:8000/docs` (Swagger UI)
Or: `http://127.0.0.1:8000/redoc` (ReDoc)

## Core API Example (User CRUD)

### Create User

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true
  }'
```

Save the returned `id` for later operations.

### List All Users

```bash
# Without pagination (returns array)
curl http://127.0.0.1:8000/api/v1/users

# With pagination (returns PaginatedResponse)
curl "http://127.0.0.1:8000/api/v1/users?page=1&size=10"
```

### Get User by ID

```bash
curl http://127.0.0.1:8000/api/v1/users/YOUR_USER_ID
```

### Update User

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/users/YOUR_USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john.doe@example.com",
    "full_name": "John D. Doe",
    "is_active": true
  }'
```

### Delete User

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/users/YOUR_USER_ID
```

### Get Schema

```bash
curl http://127.0.0.1:8000/api/v1/users/\$schema
```

## Authentication Example

### 1. Set API Keys

```bash
# File-based (auth_basic.py)
echo "sk_dev_abc123" > api_keys.txt
echo "sk_dev_xyz789" >> api_keys.txt

# Environment variable (auth_envvar.py)
export API_KEYS="sk_prod_abc123,sk_prod_xyz789"

# Docker secrets (auth_docker_secrets.py)
mkdir -p /run/secrets
echo "sk_secret_abc123" > /run/secrets/api_keys
```

### 2. Start Service

```bash
fastapi dev examples/auth_basic.py
```

### 3. Test Health (No Auth Required)

```bash
curl http://127.0.0.1:8000/health
```

### 4. Access Protected Endpoint

```bash
# Without auth (fails with 401)
curl http://127.0.0.1:8000/api/v1/users

# With valid API key (succeeds)
curl -H "X-API-Key: sk_dev_abc123" http://127.0.0.1:8000/api/v1/users
```

## Job Scheduler Example

### 1. Start Service

```bash
fastapi dev examples/job_scheduler_api.py
```

### 2. Create Background Job

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/users/\$heavy-process?delay=5&data=test_data"
```

Returns:
```json
{
  "job_id": "01K7W14XJE4DQNRF08RC4TPJ26",
  "status": "pending",
  "message": "Heavy processing job started"
}
```

### 3. Check Job Status

```bash
curl http://127.0.0.1:8000/api/v1/jobs/01K7W14XJE4DQNRF08RC4TPJ26
```

### 4. List All Jobs

```bash
# All jobs
curl http://127.0.0.1:8000/api/v1/jobs

# Filter by status
curl "http://127.0.0.1:8000/api/v1/jobs?status_filter=completed"
```

### 5. Monitor with SSE (Server-Sent Events)

```bash
# Start SSE service
fastapi dev examples/job_scheduler_sse_api.py

# Stream job updates
curl http://127.0.0.1:8000/api/v1/jobs/YOUR_JOB_ID/stream
```

## Monitoring Example

### 1. Start Service with Monitoring

```bash
fastapi dev examples/monitoring_api.py
```

### 2. Access Prometheus Metrics

```bash
curl http://127.0.0.1:8000/metrics
```

Returns metrics in Prometheus text format:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/health"} 1.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
...
```

### 3. View System Info

```bash
curl http://127.0.0.1:8000/api/v1/system
```

## App Hosting Example

### 1. Start Service

```bash
fastapi dev examples/app_hosting_api.py
```

### 2. Access Hosted App

Visit: `http://127.0.0.1:8000/dashboard`

The service hosts a static web application alongside the API.

## Common Endpoints

All services provide these base endpoints:

### Health & Info
- `GET /health` - Health check
- `GET /api/v1/system` - System information (if enabled)

### CRUD Operations (core_api, auth examples)
- `POST /api/v1/users` - Create user
- `GET /api/v1/users` - List all users (supports pagination)
- `GET /api/v1/users/{id}` - Get specific user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/users/$schema` - Get JSON schema

### Jobs (if enabled)
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{id}` - Get job status
- `DELETE /api/v1/jobs/{id}` - Cancel/delete job
- `GET /api/v1/jobs/{id}/stream` - Stream job updates (SSE)

### Monitoring (if enabled)
- `GET /metrics` - Prometheus metrics

## Pagination

List endpoints support optional pagination:

```bash
# Without pagination (returns array)
curl http://127.0.0.1:8000/api/v1/users

# With pagination (returns PaginatedResponse)
curl "http://127.0.0.1:8000/api/v1/users?page=1&size=10"
```

Paginated response format:
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

## Error Handling

All services use RFC 9457 Problem Details format:

```json
{
  "type": "urn:servicekit:error:not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "User 01K72P60ZNX2PJ6QJWZK7RMCRV not found",
  "instance": "/api/v1/users/01K72P60ZNX2PJ6QJWZK7RMCRV"
}
```

Common error types:
- `not-found` (404) - Resource not found
- `validation-failed` (400) - Input validation error
- `invalid-ulid` (400) - Invalid ID format
- `conflict` (409) - Resource conflict
- `unauthorized` (401) - Missing or invalid authentication
- `forbidden` (403) - Insufficient permissions

## Authentication Details

### Unauthenticated Endpoints (Public)
- `GET /health`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`
- Any static apps served via `.with_app()`

### Authenticated Endpoints (Require X-API-Key)
- All `/api/v1/*` endpoints (except `/api/v1/system` which can be configured)
- All CRUD operations
- All job management operations

### API Key Sources (Priority Order)

1. **Direct parameter** (auth_basic.py) - Development only
2. **Environment variable** - `API_KEYS` (recommended for production)
3. **Docker secrets file** - `/run/secrets/api_keys` (most secure)
4. **File** - `./api_keys.txt` (development)

### Multiple API Keys

Support key rotation with zero downtime:

```bash
# Environment variable
export API_KEYS="sk_old_key,sk_new_key"

# File (one per line)
echo "sk_old_key" > api_keys.txt
echo "sk_new_key" >> api_keys.txt
```

Both keys work simultaneously for gradual rollout.

## Tips

1. **Use jq**: Parse JSON responses: `curl ... | jq '.id'`
2. **Save IDs**: Store resource IDs for subsequent operations
3. **Interactive Docs**: Use Swagger UI at `/docs` for easier testing
4. **Logging**: Services with `.with_logging()` provide structured logs
5. **Monitoring**: Add `.with_monitoring()` for Prometheus metrics
6. **Background Jobs**: Use `.with_jobs()` for async operations

## Postman Collections

Import-ready Postman collections for API testing:

- `core_api.postman_collection.json` - User CRUD operations
- `auth_basic.postman_collection.json` - Authentication workflows
- `monitoring_api.postman_collection.json` - Metrics and system info

See [POSTMAN.md](POSTMAN.md) for import instructions and usage guide.

## Docker Deployment

See [../docker/](../docker/) for Docker Compose examples:

- Complete deployment configurations
- Environment variable setup
- Docker secrets management
- Monitoring with Prometheus and Grafana

## Next Steps

- Explore [example source code](../) for implementation details
- Read [POSTMAN.md](POSTMAN.md) for Postman collection usage
- Check [../../CLAUDE.md](../../CLAUDE.md) for architecture reference
- Visit [../../docs/](../../docs/) for comprehensive guides
