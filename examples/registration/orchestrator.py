"""Mock orchestrator service that receives service registrations."""

import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import valkey.asyncio as valkey  # type: ignore[import-not-found]
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

# Valkey client (initialized in lifespan)
redis_client: valkey.Valkey | None = None  # type: ignore[no-any-unimported]


class RegistrationPayload(BaseModel):
    """Registration payload from services."""

    url: str
    info: dict[str, Any]


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
    info: dict[str, Any]
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


class DeregisterResponse(BaseModel):
    """Response from service deregistration."""

    status: str
    service: ServiceDetail


class RegistrationRouter(Router):
    """Router for service registration operations."""

    def _register_routes(self) -> None:
        """Register service registration endpoints."""

        @self.router.post("/$register", response_model=RegistrationResponse, status_code=201)
        async def register_service(
            request: Request, payload: RegistrationPayload, response: Response
        ) -> RegistrationResponse:
            """Register a service and add it to the Valkey registry."""
            service_url = payload.url
            service_info = payload.info

            # Generate ULID for this service
            service_id = str(ULID())

            # Calculate expiration time
            now = datetime.now(UTC)
            expires_at = now + timedelta(seconds=TTL_SECONDS)

            # Store in Valkey with automatic TTL
            service_data = {
                "id": service_id,
                "url": service_url,
                "info": service_info,
                "registered_at": now.isoformat(),
                "last_updated": now.isoformat(),
                "last_ping_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            }

            await redis_client.set(  # type: ignore
                f"service:{service_id}",
                json.dumps(service_data),
                ex=TTL_SECONDS,  # Automatically expire after TTL
            )

            # Build log context with optional fields
            log_context = {
                "service_id": service_id,
                "service_url": service_url,
                "display_name": service_info.get("display_name", "Unknown"),
                "version": service_info.get("version", "Unknown"),
                "registered_at": now.isoformat(),
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
            service_data_raw = await redis_client.get(f"service:{service_id}")  # type: ignore
            if not service_data_raw:
                raise NotFoundError(f"Service with ID {service_id} not found")

            # Parse existing data
            service_data = json.loads(service_data_raw)

            # Update last ping time and expiration
            now = datetime.now(UTC)
            expires_at = now + timedelta(seconds=TTL_SECONDS)

            service_data["last_ping_at"] = now.isoformat()
            service_data["expires_at"] = expires_at.isoformat()
            service_data["last_updated"] = now.isoformat()

            # Update in Valkey and reset TTL
            await redis_client.set(  # type: ignore
                f"service:{service_id}",
                json.dumps(service_data),
                ex=TTL_SECONDS,
            )

            logger.debug(
                "service.pinged",
                service_id=service_id,
                service_url=service_data["url"],
                display_name=service_data["info"].get("display_name", "Unknown"),
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
            # Get all service keys
            keys = await redis_client.keys("service:*")  # type: ignore

            services = []
            for key in keys:
                service_data_raw = await redis_client.get(key)  # type: ignore
                if service_data_raw:
                    service_data = json.loads(service_data_raw)
                    services.append(ServiceDetail(**service_data))

            return ServiceListResponse(
                count=len(services),
                services=services,
            )

        @self.router.get("/{service_id}", response_model=ServiceDetail)
        async def get_service(service_id: str) -> ServiceDetail:
            """Get details for a specific service by ULID."""
            service_data_raw = await redis_client.get(f"service:{service_id}")  # type: ignore
            if not service_data_raw:
                raise NotFoundError(f"Service with ID {service_id} not found")

            service_data = json.loads(service_data_raw)
            return ServiceDetail(**service_data)

        @self.router.delete("/{service_id}", response_model=DeregisterResponse)
        async def deregister_service(service_id: str) -> DeregisterResponse:
            """Remove a service from the registry by ULID."""
            service_data_raw = await redis_client.get(f"service:{service_id}")  # type: ignore
            if not service_data_raw:
                raise NotFoundError(f"Service with ID {service_id} not found")

            service_data = json.loads(service_data_raw)

            # Delete from Valkey
            await redis_client.delete(f"service:{service_id}")  # type: ignore

            logger.info(
                "service.deregistered",
                service_id=service_id,
                service_url=service_data["url"],
                display_name=service_data["info"].get("display_name", "Unknown"),
            )
            return DeregisterResponse(status="deregistered", service=ServiceDetail(**service_data))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Valkey connection lifecycle."""
    global redis_client

    # Startup: Connect to Valkey
    valkey_url = os.getenv("VALKEY_URL", "redis://localhost:6379")
    redis_client = await valkey.from_url(valkey_url, decode_responses=True)
    logger.info("valkey.connected", url=valkey_url)

    try:
        yield
    finally:
        # Shutdown: Close connection
        if redis_client:
            await redis_client.aclose()
            logger.info("valkey.disconnected")


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            id="mock-orchestrator",
            display_name="Mock Orchestrator",
            version="1.0.0",
            description=(
                "Provides service registration endpoints for servicekit services to register themselves for discovery. "
                f"Services must send keepalive pings within {TTL_SECONDS} seconds or they will be removed from the "
                "registry. Uses Valkey for TTL-based service expiration."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .include_router(RegistrationRouter.create(prefix="/services", tags=["registration"]))
    .build()
)

# Override the lifespan to include Valkey connection management
app.router.lifespan_context = lifespan


if __name__ == "__main__":
    from servicekit.api import run_app

    logger.info(
        "orchestrator.starting",
        url="http://0.0.0.0:9000",
        register_endpoint="http://0.0.0.0:9000/services/$register",
        services_endpoint="http://0.0.0.0:9000/services",
    )

    run_app("orchestrator:app", port=9000)
