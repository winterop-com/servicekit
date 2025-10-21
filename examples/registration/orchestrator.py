"""Mock orchestrator service that receives service registrations."""

from datetime import UTC, datetime

from fastapi import FastAPI
from pydantic import BaseModel

from servicekit.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Mock Orchestrator",
    version="1.0.0",
    description="Simple orchestrator for testing service registration",
)

# In-memory registry
# NOTE: This uses an in-memory dict which only works with a single Gunicorn worker.
# For production use with multiple workers, use a shared data store (Redis, database, etc.)
service_registry: dict[str, dict] = {}


class RegistrationPayload(BaseModel):
    """Registration payload from services."""

    url: str
    info: dict


@app.post("/register")
async def register_service(payload: RegistrationPayload) -> dict:
    """Register a service and add it to the in-memory registry."""
    service_url = payload.url
    service_info = payload.info

    # Store in registry with timestamp
    service_registry[service_url] = {
        "url": service_url,
        "info": service_info,
        "registered_at": datetime.now(UTC).isoformat(),
        "last_updated": datetime.now(UTC).isoformat(),
    }

    # Build log context with optional fields
    log_context = {
        "service_url": service_url,
        "display_name": service_info.get("display_name", "Unknown"),
        "version": service_info.get("version", "Unknown"),
        "registered_at": service_registry[service_url]["registered_at"],
    }
    if "deployment_env" in service_info:
        log_context["deployment_env"] = service_info["deployment_env"]
    if "team" in service_info:
        log_context["team"] = service_info["team"]
    if "capabilities" in service_info:
        log_context["capabilities"] = service_info["capabilities"]

    logger.info("service.registered", **log_context)

    return {
        "status": "registered",
        "service_url": service_url,
        "message": f"Service {service_info.get('display_name', 'Unknown')} registered successfully",
    }


@app.get("/services")
async def list_services() -> dict:
    """List all registered services."""
    return {
        "count": len(service_registry),
        "services": list(service_registry.values()),
    }


@app.get("/services/{service_url:path}")
async def get_service(service_url: str) -> dict:
    """Get details for a specific service."""
    # URL decode the service_url
    import urllib.parse

    decoded_url = urllib.parse.unquote(service_url)

    # Normalize URL (add http:// if missing)
    if not decoded_url.startswith("http://") and not decoded_url.startswith("https://"):
        decoded_url = f"http://{decoded_url}"

    if decoded_url in service_registry:
        return service_registry[decoded_url]

    return {"error": "Service not found", "url": decoded_url}


@app.delete("/services/{service_url:path}")
async def deregister_service(service_url: str) -> dict:
    """Remove a service from the registry."""
    import urllib.parse

    decoded_url = urllib.parse.unquote(service_url)

    if not decoded_url.startswith("http://") and not decoded_url.startswith("https://"):
        decoded_url = f"http://{decoded_url}"

    if decoded_url in service_registry:
        service = service_registry.pop(decoded_url)
        return {"status": "deregistered", "service": service}

    return {"error": "Service not found", "url": decoded_url}


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "registered_services": len(service_registry)}


if __name__ == "__main__":
    import uvicorn

    from servicekit.logging import configure_logging

    configure_logging()

    logger.info(
        "orchestrator.starting",
        url="http://0.0.0.0:9000",
        register_endpoint="http://0.0.0.0:9000/register",
        services_endpoint="http://0.0.0.0:9000/services",
    )

    uvicorn.run("orchestrator:app", host="0.0.0.0", port=9000, reload=True)
