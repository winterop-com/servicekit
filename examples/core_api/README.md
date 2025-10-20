# Core API Demo

A complete demonstration of Servicekit's core features using BaseServiceBuilder with a custom User entity.

## Features

- **Custom Entity**: User model with username, email, full_name, and is_active fields
- **CRUD Operations**: Full REST API for user management
- **Health Checks**: Built-in health endpoint at `/health`
- **System Info**: Service metadata at `/api/v1/system`
- **Job Scheduling**: Background job execution at `/api/v1/jobs`
- **Monitoring**: Prometheus metrics at `/metrics` with OpenTelemetry
- **Logging**: Structured JSON logging with request context
- **Landing Page**: Interactive API documentation at `/`
- **Data Seeding**: Auto-populated with example users (Alice and Bob)

## Quick Start

### Local Development

```bash
# Install dependencies
uv sync

# Run the service
uv run uvicorn main:app --reload

# Or use fastapi CLI
uv run fastapi dev main.py
```

The API will be available at http://localhost:8000

### Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up

# Run in detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

## API Endpoints

### Health & System

- `GET /health` - Health check (no auth required)
- `GET /api/v1/system` - Service information and metadata

### Users (CRUD)

- `GET /api/v1/users` - List all users (with pagination support)
- `POST /api/v1/users` - Create new user
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/users/$schema` - Get Pydantic schema

### Jobs

- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Delete job
- `GET /api/v1/jobs/{id}/stream` - SSE stream for job updates

### Monitoring

- `GET /metrics` - Prometheus metrics

### Documentation

- `GET /` - Landing page with interactive API docs
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## Example Usage

### List Users

```bash
curl http://localhost:8000/api/v1/users
```

### Create User

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "charlie",
    "email": "charlie@example.com",
    "full_name": "Charlie Brown",
    "is_active": true
  }'
```

### Get User by ID

```bash
# Replace {id} with actual ULID from list/create response
curl http://localhost:8000/api/v1/users/{id}
```

### Update User

```bash
curl -X PUT http://localhost:8000/api/v1/users/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "username": "charlie",
    "email": "charlie@updated.com",
    "full_name": "Charlie Brown Jr",
    "is_active": true
  }'
```

### Delete User

```bash
curl -X DELETE http://localhost:8000/api/v1/users/{id}
```

### Pagination

```bash
# Get first page with 10 items
curl http://localhost:8000/api/v1/users?page=1&size=10
```

## Database

This demo uses an in-memory SQLite database by default. The database is automatically initialized with:

- **alice** (alice@example.com) - Alice Smith
- **bob** (bob@example.com) - Bob Johnson

For persistent storage, modify `main.py`:

```python
app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_database("sqlite+aiosqlite:///./data.db")  # File-based database
    # ... rest of configuration
    .build()
)
```

## Development

### Project Structure

```
examples/core_api/
├── main.py           # Application entry point
├── pyproject.toml    # Project metadata and dependencies
├── uv.lock          # Locked dependencies
├── Dockerfile       # Production container image
├── compose.yml      # Docker Compose configuration
└── README.md        # This file
```

### Code Organization

The demo showcases the complete pattern:

1. **Entity Layer**: `User(Entity)` - SQLAlchemy ORM model
2. **Schema Layer**: `UserIn(EntityIn)`, `UserOut(EntityOut)` - Pydantic validation
3. **Repository Layer**: `UserRepository(BaseRepository)` - Data access
4. **Manager Layer**: `UserManager(BaseManager)` - Business logic
5. **Router Layer**: `CrudRouter.create()` - REST endpoints
6. **Application Layer**: `BaseServiceBuilder` - Service assembly

### Extending the Demo

Add custom endpoints:

```python
from fastapi import APIRouter

custom_router = APIRouter(prefix="/api/v1/custom", tags=["custom"])

@custom_router.get("/hello")
async def hello():
    return {"message": "Hello World"}

app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_database()
    .with_health()
    .include_router(user_router)
    .include_router(custom_router)  # Add custom router
    .build()
)
```

## Monitoring with Prometheus

The demo includes built-in Prometheus metrics:

```bash
# View metrics
curl http://localhost:8000/metrics
```

Metrics include:
- HTTP request duration histograms
- HTTP request counters by status code
- SQLAlchemy connection pool metrics
- Process CPU and memory metrics

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Change port in compose.yml
ports:
  - "8080:8000"  # Map to 8080 instead

# Or for local development
uv run uvicorn main:app --port 8080
```

### Database Locked

SQLite in-memory databases are reset on restart. For persistent storage, use a file-based database as shown in the Database section above.

## Next Steps

- Add authentication with `.with_auth()`
- Implement custom business logic in `UserManager`
- Add more custom query methods to `UserRepository`
- Deploy to production with proper database configuration
- Set up monitoring with Prometheus and Grafana

## Related Examples

- `monitoring/` - Full monitoring stack with Grafana
- `auth_envvar/` - API key authentication
- `job_scheduler/` - Advanced job scheduling patterns

## Postman Collection

A Postman collection is included for easy API testing. Import the collection file into Postman:

**Import Steps:**
1. Open Postman
2. Click **Import** button
3. Select the `.postman_collection.json` file from this directory
4. Click **Import**

**Collection Features:**
- Pre-configured requests for all endpoints
- Auto-captured variables (IDs from responses)
- Test scripts for validation
- Example workflows

**Variables:**
- `baseUrl`: Default `http://127.0.0.1:8000`
- `user_id`: Auto-set from create requests
- `api_key`: Set your API key (for auth demos)

See the collection file for complete request examples and workflows.
