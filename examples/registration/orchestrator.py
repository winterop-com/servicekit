"""Mock orchestrator service that receives service registrations."""

from datetime import UTC, datetime

from pydantic import BaseModel
from ulid import ULID

from servicekit.api import BaseServiceBuilder, Router, ServiceInfo
from servicekit.exceptions import NotFoundError
from servicekit.logging import get_logger

logger = get_logger(__name__)

# In-memory registry keyed by ULID
# NOTE: This uses an in-memory dict which only works with a single worker.
# For production use with multiple workers, use a shared data store (Redis, database, etc.)
service_registry: dict[str, dict] = {}


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


class ServiceDetail(BaseModel):
    """Detailed service information."""

    id: str
    url: str
    info: dict
    registered_at: str
    last_updated: str


class ServiceListResponse(BaseModel):
    """Response for listing all services."""

    count: int
    services: list[ServiceDetail]


class RegistrationRouter(Router):
    """Router for service registration operations."""

    def _register_routes(self) -> None:
        """Register service registration endpoints."""

        @self.router.post("/$register", response_model=RegistrationResponse)
        async def register_service(payload: RegistrationPayload) -> RegistrationResponse:
            """Register a service and add it to the in-memory registry."""
            service_url = payload.url
            service_info = payload.info

            # Generate ULID for this service
            service_id = str(ULID())

            # Store in registry with ULID key
            service_registry[service_id] = {
                "id": service_id,
                "url": service_url,
                "info": service_info,
                "registered_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat(),
            }

            # Build log context with optional fields
            log_context = {
                "service_id": service_id,
                "service_url": service_url,
                "display_name": service_info.get("display_name", "Unknown"),
                "version": service_info.get("version", "Unknown"),
                "registered_at": service_registry[service_id]["registered_at"],
            }
            if "deployment_env" in service_info:
                log_context["deployment_env"] = service_info["deployment_env"]
            if "team" in service_info:
                log_context["team"] = service_info["team"]
            if "capabilities" in service_info:
                log_context["capabilities"] = service_info["capabilities"]

            logger.info("service.registered", **log_context)

            return RegistrationResponse(
                id=service_id,
                status="registered",
                service_url=service_url,
                message=f"Service {service_info.get('display_name', 'Unknown')} registered successfully",
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


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Mock Orchestrator",
            version="1.0.0",
            summary="Simple orchestrator for testing service registration",
            description=(
                "Provides service registration endpoints for servicekit services to register themselves for discovery."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .include_router(RegistrationRouter.create(prefix="/services", tags=["registration"]))
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
