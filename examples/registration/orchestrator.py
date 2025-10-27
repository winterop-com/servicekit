"""Mock orchestrator service that receives service registrations."""

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from ulid import ULID

from servicekit.api import BaseServiceBuilder, Router, ServiceInfo
from servicekit.api.utilities import build_location_url
from servicekit.exceptions import NotFoundError
from servicekit.logging import get_logger

logger = get_logger(__name__)

# Configuration
TTL_SECONDS = 30  # Time before a service is considered dead without ping
CLEANUP_INTERVAL_SECONDS = 5  # How often to check for expired services

# In-memory registry keyed by ULID
# NOTE: This is a simple example suitable for demos and single-worker deployments.
# For production use, consider Redis or Valkey which provide:
#   - Built-in TTL (no manual cleanup task needed)
#   - Multi-worker support via shared state
#   - Atomic operations for concurrent updates
# Example: await redis.set(f"service:{id}", data, ex=TTL_SECONDS)
service_registry: dict[str, dict] = {}

# Background task for cleanup
cleanup_task: asyncio.Task | None = None


class RegistrationPayload(BaseModel):
    """Registration payload from services."""

    url: str
    info: dict


class RegistrationResponse(BaseModel):
    """Response from service registration."""

    id: str
    status: str
    service_url: str
    message: str
    ttl_seconds: int
    ping_url: str


class ServiceDetail(BaseModel):
    """Detailed service information."""

    id: str
    url: str
    info: dict
    registered_at: str
    last_updated: str
    last_ping_at: str
    expires_at: str


class ServiceListResponse(BaseModel):
    """Response for listing all services."""

    count: int
    services: list[ServiceDetail]


class PingResponse(BaseModel):
    """Response from service ping."""

    id: str
    status: str
    last_ping_at: str
    expires_at: str


async def cleanup_expired_services() -> None:
    """Background task to remove expired services from registry."""
    logger.info("cleanup.started", interval_seconds=CLEANUP_INTERVAL_SECONDS, ttl_seconds=TTL_SECONDS)

    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)

            now = datetime.now(UTC)
            expired_services = []

            for service_id, service in list(service_registry.items()):
                expires_at_str = service.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if now >= expires_at:
                        expired_services.append(service_id)

            for service_id in expired_services:
                service = service_registry.pop(service_id)
                logger.warning(
                    "service.expired",
                    service_id=service_id,
                    service_url=service["url"],
                    display_name=service["info"].get("display_name", "Unknown"),
                    last_ping_at=service.get("last_ping_at"),
                    expires_at=service.get("expires_at"),
                )

        except Exception as e:
            logger.error("cleanup.error", error=str(e), error_type=type(e).__name__)


class RegistrationRouter(Router):
    """Router for service registration operations."""

    def _register_routes(self) -> None:
        """Register service registration endpoints."""

        @self.router.post("/$register", response_model=RegistrationResponse, status_code=201)
        async def register_service(
            request: Request, payload: RegistrationPayload, response: Response
        ) -> RegistrationResponse:
            """Register a service and add it to the in-memory registry."""
            service_url = payload.url
            service_info = payload.info

            # Generate ULID for this service
            service_id = str(ULID())

            # Calculate expiration time
            now = datetime.now(UTC)
            expires_at = now + timedelta(seconds=TTL_SECONDS)

            # Store in registry with ULID key
            service_registry[service_id] = {
                "id": service_id,
                "url": service_url,
                "info": service_info,
                "registered_at": now.isoformat(),
                "last_updated": now.isoformat(),
                "last_ping_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            }

            # Build log context with optional fields
            log_context = {
                "service_id": service_id,
                "service_url": service_url,
                "display_name": service_info.get("display_name", "Unknown"),
                "version": service_info.get("version", "Unknown"),
                "registered_at": service_registry[service_id]["registered_at"],
                "ttl_seconds": TTL_SECONDS,
                "expires_at": expires_at.isoformat(),
            }
            if "deployment_env" in service_info:
                log_context["deployment_env"] = service_info["deployment_env"]
            if "team" in service_info:
                log_context["team"] = service_info["team"]
            if "capabilities" in service_info:
                log_context["capabilities"] = service_info["capabilities"]

            logger.info("service.registered", **log_context)

            # Set Location header to the created resource
            response.headers["Location"] = build_location_url(request, f"/services/{service_id}")

            # Build ping URL
            ping_url = build_location_url(request, f"/services/{service_id}/$ping")

            return RegistrationResponse(
                id=service_id,
                status="registered",
                service_url=service_url,
                message=f"Service {service_info.get('display_name', 'Unknown')} registered successfully",
                ttl_seconds=TTL_SECONDS,
                ping_url=ping_url,
            )

        @self.router.put("/{service_id}/$ping", response_model=PingResponse)
        async def ping_service(service_id: str) -> PingResponse:
            """Update service ping timestamp and extend TTL."""
            if service_id not in service_registry:
                raise NotFoundError(f"Service with ID {service_id} not found")

            # Update last ping time and expiration
            now = datetime.now(UTC)
            expires_at = now + timedelta(seconds=TTL_SECONDS)

            service_registry[service_id]["last_ping_at"] = now.isoformat()
            service_registry[service_id]["expires_at"] = expires_at.isoformat()
            service_registry[service_id]["last_updated"] = now.isoformat()

            logger.debug(
                "service.pinged",
                service_id=service_id,
                service_url=service_registry[service_id]["url"],
                display_name=service_registry[service_id]["info"].get("display_name", "Unknown"),
                last_ping_at=now.isoformat(),
                expires_at=expires_at.isoformat(),
            )

            return PingResponse(
                id=service_id,
                status="alive",
                last_ping_at=now.isoformat(),
                expires_at=expires_at.isoformat(),
            )

        @self.router.get("", response_model=ServiceListResponse)
        async def list_services() -> ServiceListResponse:
            """List all registered services."""
            services = [ServiceDetail(**svc) for svc in service_registry.values()]
            return ServiceListResponse(
                count=len(services),
                services=services,
            )

        @self.router.get("/{service_id}", response_model=ServiceDetail)
        async def get_service(service_id: str) -> ServiceDetail:
            """Get details for a specific service by ULID."""
            if service_id not in service_registry:
                raise NotFoundError(f"Service with ID {service_id} not found")

            return ServiceDetail(**service_registry[service_id])

        @self.router.delete("/{service_id}")
        async def deregister_service(service_id: str) -> dict:
            """Remove a service from the registry by ULID."""
            if service_id not in service_registry:
                raise NotFoundError(f"Service with ID {service_id} not found")

            service = service_registry.pop(service_id)
            logger.info(
                "service.deregistered",
                service_id=service_id,
                service_url=service["url"],
                display_name=service["info"].get("display_name", "Unknown"),
            )
            return {"status": "deregistered", "service": service}


async def start_cleanup_task(app: FastAPI) -> None:  # noqa: ARG001
    """Start the background cleanup task."""
    global cleanup_task
    cleanup_task = asyncio.create_task(cleanup_expired_services())
    logger.info("cleanup_task.started")


async def stop_cleanup_task(app: FastAPI) -> None:  # noqa: ARG001
    """Stop the background cleanup task."""
    global cleanup_task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        cleanup_task = None
        logger.info("cleanup_task.stopped")


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Mock Orchestrator",
            version="1.0.0",
            summary="Simple orchestrator for testing service registration",
            description=(
                "Provides service registration endpoints for servicekit services to register themselves for discovery. "
                f"Services must send keepalive pings within {TTL_SECONDS} seconds or they will be removed from the "
                "registry."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .include_router(RegistrationRouter.create(prefix="/services", tags=["registration"]))
    .on_startup(start_cleanup_task)
    .on_shutdown(stop_cleanup_task)
    .build()
)


if __name__ == "__main__":
    from servicekit.api import run_app

    logger.info(
        "orchestrator.starting",
        url="http://0.0.0.0:9000",
        register_endpoint="http://0.0.0.0:9000/services/$register",
        services_endpoint="http://0.0.0.0:9000/services",
    )

    run_app("orchestrator:app", port=9000)
