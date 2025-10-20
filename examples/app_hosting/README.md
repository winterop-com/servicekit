# App Hosting Demo

Demonstrates how to host static web applications (HTML/JS/CSS) alongside your FastAPI service using Servicekit's app hosting system.

## Features

- **Static App Hosting**: Mount web apps at custom URL prefixes
- **Sample Dashboard**: Example dashboard app at `/dashboard`
- **Health Checks**: Built-in health endpoint at `/health`
- **System Info**: Service metadata at `/api/v1/system`
- **Auto-Discovery**: Support for mounting multiple apps from a directory

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

## Endpoints

### Service Endpoints

- `GET /health` - Health check (no auth required)
- `GET /api/v1/system` - Service information and metadata
- `GET /docs` - Swagger UI API documentation
- `GET /redoc` - ReDoc API documentation

### Hosted Apps

- `GET /dashboard` - Sample dashboard web application

## App Structure

Apps are organized in the `apps/` directory. Each app must have a `manifest.json` file:

```
apps/
└── sample-dashboard/
    ├── manifest.json    # App metadata (required)
    ├── index.html      # Entry point
    ├── style.css       # Styles
    └── script.js       # JavaScript
```

### Manifest Format

Each app requires a `manifest.json` file:

```json
{
  "name": "Sample Dashboard",
  "version": "1.0.0",
  "prefix": "/dashboard",
  "description": "A sample dashboard application",
  "author": "Your Name",
  "entry": "index.html"
}
```

**Required fields:**
- `name` - Display name of the app
- `version` - Semantic version
- `prefix` - URL prefix where the app will be mounted (e.g., `/dashboard`)

**Optional fields:**
- `description` - Brief description of the app
- `author` - Author name or organization
- `entry` - Entry point file (defaults to `index.html`)

## Mounting Apps

### Single App

Mount a specific app directory:

```python
app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_app("apps/sample-dashboard")  # Uses prefix from manifest
    .build()
)
```

### Override Prefix

Override the manifest prefix:

```python
app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_app("apps/sample-dashboard", prefix="/admin")
    .build()
)
```

### Auto-Discovery

Mount all apps in a directory:

```python
app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_apps("apps")  # Discovers all subdirectories with manifest.json
    .build()
)
```

### From Python Package

Mount apps bundled in a Python package:

```python
app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_apps(("mycompany.webapps", "apps"))  # Package path + subdirectory
    .build()
)
```

## Creating Your Own App

1. **Create app directory**:
```bash
mkdir -p apps/my-app
```

2. **Create manifest.json**:
```json
{
  "name": "My App",
  "version": "1.0.0",
  "prefix": "/my-app"
}
```

3. **Create index.html**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>My Custom App</h1>
    <script src="script.js"></script>
</body>
</html>
```

4. **Add to service**:
```python
.with_app("apps/my-app")
```

## Accessing the Dashboard

Once the service is running, visit:

- **Local**: http://localhost:8000/dashboard
- **Docker**: http://localhost:8000/dashboard

The sample dashboard includes:
- System metrics visualization
- API status indicators
- Interactive UI components
- Real-time data updates

## Important Notes

### Path Resolution

- **Filesystem paths**: Resolved relative to the working directory where the service runs
- **Package paths**: Use tuple syntax `("package.name", "subpath")` for bundled apps
- **Both approaches** work with `.with_app()` and `.with_apps()`

### Restrictions

- Apps cannot mount at `/api` or `/api/**` (reserved for API endpoints)
- Prefix must start with `/` and cannot contain `..` (security)
- Root mounts (`/`) are supported but may intercept some redirects

### Override Semantics

- Duplicate prefixes use "last wins" - later calls override earlier ones
- Useful for customizing default apps from libraries

## Example Use Cases

### Admin Dashboard

```python
.with_app("apps/admin", prefix="/admin")
```

### Multiple Apps

```python
.with_apps("apps")  # Auto-discovers all apps
```

### Library-Provided Apps

```python
from mylib import get_default_apps

app = (
    BaseServiceBuilder(info=ServiceInfo(...))
    .with_apps(get_default_apps())  # Library defaults
    .with_app("apps/custom", prefix="/")  # Override with custom
    .build()
)
```

## Troubleshooting

### App Not Loading

1. Check manifest.json exists and is valid JSON
2. Verify prefix is unique and doesn't conflict
3. Check file permissions on app directory
4. Review logs for validation errors

### 404 on App Route

1. Ensure prefix matches manifest
2. Check that entry file (default: index.html) exists
3. Verify app was mounted (check startup logs)

### Styles/Scripts Not Loading

1. Use relative paths in HTML (e.g., `./style.css` not `/style.css`)
2. Ensure files exist in app directory
3. Check browser console for 404 errors

## Development Tips

- **Live Reload**: Use `uv run uvicorn main:app --reload` for development
- **Static Files**: Place all assets (CSS, JS, images) in the app directory
- **API Integration**: Apps can call service APIs at `/api/v1/*`
- **Debugging**: Check browser developer tools console and network tab

## Next Steps

- Add API integration to your custom apps
- Create multi-page applications with routing
- Implement authentication for protected apps
- Bundle apps as Python packages for distribution

## Related Examples

- `core_api/` - Basic CRUD API service
- `monitoring/` - Metrics and observability
- `auth_envvar/` - API key authentication
