# Multi-Level Orchestrator Example

This example demonstrates a hierarchical service discovery architecture using servicekit, where orchestrators can manage other orchestrators in a multi-level hierarchy.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Level 1: Global                          │
│                                                              │
│              Parent Orchestrator (port 9000)                 │
│                                                              │
└────────────┬──────────────┬─────────────┬───────────────────┘
             │              │             │
    ┌────────▼────┐  ┌─────▼──────┐  ┌──▼───────────┐
    │   Level 2:  │  │  Level 2:  │  │   Level 2:   │
    │  Regional   │  │  Regional  │  │    Domain    │
    │             │  │            │  │              │
    │     US      │  │     EU     │  │      ML      │
    │ Orchestrator│  │Orchestrator│  │ Orchestrator │
    │ (port 9001) │  │(port 9002) │  │ (port 9003)  │
    └──┬────┬─────┘  └─────┬──────┘  └──────┬───────┘
       │    │              │                 │
   ┌───▼┐ ┌─▼───┐      ┌──▼──┐          ┌──▼──┐
   │8001│ │8002 │      │8003 │          │8004 │
   │    │ │     │      │     │          │     │
   │ US │ │ US  │      │ EU  │          │ ML  │
   │Svc1│ │Svc2 │      │Svc1 │          │Svc1 │
   └────┘ └─────┘      └─────┘          └─────┘
     │       │            │                │
     └───────┴────────────┴────────────────┘
              Level 3: Services
```

## Components

### Level 1: Parent Orchestrator
- **Port**: 9000
- **Role**: Global service registry
- **Endpoints**:
  - `POST /api/v1/orchestrators/$register` - Register child orchestrator
  - `GET /api/v1/orchestrators` - List all child orchestrators
  - `GET /api/v1/orchestrators/{id}` - Get orchestrator details
  - `POST /api/v1/services/$register` - Register service (forwarded from children)
  - `GET /api/v1/services` - List all services across hierarchy
  - `GET /api/v1/hierarchy` - Get full hierarchy view
  - `DELETE /api/v1/orchestrators/{id}` - Deregister orchestrator

### Level 2: Child Orchestrators
Child orchestrators manage services in specific regions or domains:

- **US Orchestrator** (port 9001)
  - Region: `us-east`
  - Manages US-based services

- **EU Orchestrator** (port 9002)
  - Region: `eu-west`
  - Manages EU-based services

- **ML Orchestrator** (port 9003)
  - Domain: `machine-learning`
  - Manages ML-specific services

**Endpoints**:
- `POST /services/$register` - Register service
- `GET /services` - List local services
- `GET /services/{id}` - Get service details
- `GET /services/info/orchestrator` - Get orchestrator info
- `DELETE /services/{id}` - Deregister service

### Level 3: Services
Example services that register with child orchestrators:
- US Payment Service (8001)
- US Inventory Service (8002)
- EU GDPR Compliance Service (8003)
- ML Model Training Service (8004)

## Running the Example

### Using Docker Compose (Recommended)

```bash
# Start the entire hierarchy
docker compose up

# View logs
docker compose logs -f parent-orchestrator
docker compose logs -f us-orchestrator

# Stop all services
docker compose down
```

### Manual Startup

```bash
# Terminal 1: Start parent orchestrator
python parent_orchestrator.py

# Terminal 2: Start US orchestrator
export PARENT_ORCHESTRATOR_URL=http://localhost:9000
export ORCHESTRATOR_REGION=us-east
export CHILD_HOST=localhost
export CHILD_PORT=9001
python child_orchestrator.py

# Terminal 3: Start EU orchestrator
export PARENT_ORCHESTRATOR_URL=http://localhost:9000
export ORCHESTRATOR_REGION=eu-west
export CHILD_HOST=localhost
export CHILD_PORT=9002
python child_orchestrator.py

# Terminal 4: Start a service
export SERVICE_NAME="Test Service"
export SERVICE_PORT=8001
export SERVICE_HOST=localhost
export ORCHESTRATOR_URL=http://localhost:9001/services/$register
python example_service.py
```

## API Examples

### View Full Hierarchy

```bash
curl http://localhost:9000/api/v1/hierarchy | python -m json.tool
```

Response shows the complete hierarchy:
```json
{
  "parent_id": "parent-orchestrator",
  "parent_info": {
    "display_name": "Parent Orchestrator",
    "level": "global"
  },
  "orchestrators": [
    {
      "orchestrator": {
        "id": "01JBXXX...",
        "url": "http://us-orchestrator:9001",
        "region": "us-east",
        "service_count": 2
      },
      "services": [
        {
          "id": "01JBYYY...",
          "url": "http://us-service-1:8001",
          "info": {"display_name": "US Payment Service"}
        }
      ]
    }
  ],
  "total_services": 4
}
```

### List All Child Orchestrators

```bash
curl http://localhost:9000/api/v1/orchestrators
```

### List Services from Specific Orchestrator

```bash
# Get all services
curl http://localhost:9000/api/v1/services

# Filter by orchestrator ID
curl "http://localhost:9000/api/v1/services?orchestrator_id=01JBXXX..."
```

### Register a Service

```bash
curl -X POST http://localhost:9001/services/\$register \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://my-service:8080",
    "info": {
      "display_name": "My Service",
      "version": "1.0.0"
    }
  }'
```

Response includes Location header:
```
HTTP/1.1 201 Created
Location: /services/01JBZZZ...
Content-Type: application/json

{
  "id": "01JBZZZ...",
  "status": "registered",
  "url": "http://my-service:8080",
  "message": "Service registered with us-east orchestrator"
}
```

### Check Child Orchestrator Info

```bash
curl http://localhost:9001/services/info/orchestrator
```

Response:
```json
{
  "orchestrator_id": "01JBXXX...",
  "parent_url": "http://parent-orchestrator:9000",
  "region": "us-east",
  "domain": null,
  "service_count": 2
}
```

## Use Cases

### 1. Multi-Region Deployment
Deploy orchestrators in different geographic regions (US, EU, Asia) with the parent providing global visibility.

### 2. Domain Separation
Separate services by domain (ML, data processing, APIs) with domain-specific orchestrators.

### 3. Team/Department Organization
Each team manages their own orchestrator, while the parent provides company-wide discovery.

### 4. Hybrid Cloud
On-premises orchestrator and cloud orchestrators both reporting to a global parent.

## Configuration

### Environment Variables

**Parent Orchestrator:**
- `PORT` - Server port (default: 9000)
- `LOG_LEVEL` - Logging level (default: info)

**Child Orchestrator:**
- `PARENT_ORCHESTRATOR_URL` - Parent URL (required)
- `ORCHESTRATOR_REGION` - Region name (optional)
- `ORCHESTRATOR_DOMAIN` - Domain name (optional)
- `CHILD_HOST` - Hostname for registration (default: localhost)
- `CHILD_PORT` - Server port (default: 9001)
- `LOG_LEVEL` - Logging level (default: info)

**Example Service:**
- `SERVICE_NAME` - Display name
- `SERVICE_PORT` - Server port
- `SERVICE_HOST` - Hostname for registration
- `ORCHESTRATOR_URL` - Child orchestrator URL
- `LOG_LEVEL` - Logging level

## Key Features

1. **Automatic Forwarding**: Child orchestrators automatically forward service registrations to parent
2. **Location Headers**: All POST operations return `201 Created` with Location header
3. **ULID-based IDs**: All resources use ULIDs for globally unique identifiers
4. **Async Registration**: Services register asynchronously to avoid blocking
5. **Health Checks**: All components expose `/health` endpoints
6. **Structured Logging**: Rich logging with contextual information
7. **Cascade Deletion**: Deregistering an orchestrator removes all its services

## Testing

```bash
# Run tests for the multi-level orchestrator
uv run pytest tests/test_example_multi_level_orchestrator.py -v

# Check all services are registered
curl http://localhost:9000/api/v1/hierarchy

# Verify service counts
curl http://localhost:9000/api/v1/orchestrators
```

## Notes

- In-memory storage is used for simplicity. For production, use a database.
- Single-worker deployment required for in-memory registry. Use Redis/database for multi-worker setups.
- Child orchestrators wait 2 seconds before registering with parent to ensure parent is ready.
- Registration failures are logged but don't prevent service startup.

## Future Enhancements

- Add authentication between orchestrators
- Implement service health monitoring
- Add service routing/proxying capabilities
- Support for service versioning
- Implement service mesh integration
- Add metrics aggregation across hierarchy
