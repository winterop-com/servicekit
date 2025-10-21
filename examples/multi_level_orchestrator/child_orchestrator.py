"""Child orchestrator for regional/domain service management."""

import asyncio
import os
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from ulid import ULID

from servicekit.api import BaseServiceBuilder, Router, ServiceInfo
from servicekit.api.utilities import build_location_url
from servicekit.exceptions import NotFoundError
from servicekit.logging import get_logger

logger = get_logger(__name__)

# Configuration
PARENT_URL = os.getenv("PARENT_ORCHESTRATOR_URL", "http://localhost:9000")
REGION = os.getenv("ORCHESTRATOR_REGION")
DOMAIN = os.getenv("ORCHESTRATOR_DOMAIN")
CHILD_HOST = os.getenv("CHILD_HOST", "localhost")
CHILD_PORT = int(os.getenv("CHILD_PORT", "9001"))

# In-memory service registry
service_registry: dict[str, dict] = {}

# Store our orchestrator ID from parent registration
orchestrator_id: str | None = None


class ServiceRegistrationPayload(BaseModel):
    """Registration payload from services."""

    url: str
    info: dict


class RegistrationResponse(BaseModel):
    """Response from service registration."""

    id: str
    status: str
    url: str
    message: str


class ServiceDetail(BaseModel):
    """Detailed service information."""

    id: str
    url: str
    info: dict
    registered_at: str
    last_updated: str


class ServiceListResponse(BaseModel):
    """Response for listing services."""

    count: int
    services: list[ServiceDetail]


async def register_with_parent() -> str | None:
    """Register this orchestrator with the parent."""
    try:
        child_url = f"http://{CHILD_HOST}:{CHILD_PORT}"
        payload = {
            "url": child_url,
            "info": {
                "display_name": f"Child Orchestrator - {REGION or DOMAIN or 'default'}",
                "version": "1.0.0",
                "level": "regional" if REGION else "domain",
            },
        }

        if REGION:
            payload["region"] = REGION
        if DOMAIN:
            payload["domain"] = DOMAIN

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PARENT_URL}/api/v1/orchestrators/$register",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            orch_id: str | None = data.get("id")

            logger.info(
                "child_orchestrator.registered_with_parent",
                orchestrator_id=orch_id,
                parent_url=PARENT_URL,
                child_url=child_url,
                region=REGION,
                domain=DOMAIN,
            )

            return orch_id if orch_id else None

    except Exception as e:
        logger.error(
            "child_orchestrator.registration_failed",
            parent_url=PARENT_URL,
            error=str(e),
            error_type=type(e).__name__,
        )
        return None


async def forward_to_parent(service_id: str, service_data: dict) -> None:
    """Forward service registration to parent orchestrator."""
    global orchestrator_id

    if not orchestrator_id:
        logger.warning("child_orchestrator.forward_skipped", reason="not registered with parent", service_id=service_id)
        return

    try:
        payload = {
            "url": service_data["url"],
            "info": service_data["info"],
            "orchestrator_id": orchestrator_id,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PARENT_URL}/api/v1/services/$register",
                json=payload,
            )
            response.raise_for_status()

            logger.info(
                "child_orchestrator.forwarded_to_parent",
                service_id=service_id,
                parent_url=PARENT_URL,
            )

    except Exception as e:
        logger.warning(
            "child_orchestrator.forward_failed",
            service_id=service_id,
            parent_url=PARENT_URL,
            error=str(e),
        )


class ChildOrchestratorRouter(Router):
    """Router for child orchestrator operations."""

    def _register_routes(self) -> None:
        """Register child orchestrator endpoints."""

        @self.router.post("/$register", response_model=RegistrationResponse, status_code=201)
        async def register_service(
            request: Request, payload: ServiceRegistrationPayload, response: Response
        ) -> RegistrationResponse:
            """Register a service with this child orchestrator."""
            service_id = str(ULID())

            service_data = {
                "id": service_id,
                "url": payload.url,
                "info": payload.info,
                "registered_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat(),
            }

            service_registry[service_id] = service_data

            logger.info(
                "service.registered",
                service_id=service_id,
                url=payload.url,
                display_name=payload.info.get("display_name", "Unknown"),
            )

            # Forward to parent asynchronously
            asyncio.create_task(forward_to_parent(service_id, service_data))

            response.headers["Location"] = build_location_url(request, f"/services/{service_id}")

            return RegistrationResponse(
                id=service_id,
                status="registered",
                url=payload.url,
                message=f"Service registered with {REGION or DOMAIN or 'default'} orchestrator",
            )

        @self.router.get("", response_model=ServiceListResponse)
        async def list_services() -> ServiceListResponse:
            """List all services registered with this orchestrator."""
            services = [ServiceDetail(**svc) for svc in service_registry.values()]
            return ServiceListResponse(count=len(services), services=services)

        @self.router.get("/{service_id}", response_model=ServiceDetail)
        async def get_service(service_id: str) -> ServiceDetail:
            """Get details for a specific service."""
            if service_id not in service_registry:
                raise NotFoundError(f"Service {service_id} not found")
            return ServiceDetail(**service_registry[service_id])

        @self.router.delete("/{service_id}")
        async def deregister_service(service_id: str) -> dict:
            """Deregister a service."""
            if service_id not in service_registry:
                raise NotFoundError(f"Service {service_id} not found")

            service = service_registry.pop(service_id)
            logger.info(
                "service.deregistered",
                service_id=service_id,
                url=service["url"],
            )
            return {"status": "deregistered", "service": service}

        @self.router.get("/info/orchestrator")
        async def get_orchestrator_info() -> dict:
            """Get information about this orchestrator."""
            return {
                "orchestrator_id": orchestrator_id,
                "parent_url": PARENT_URL,
                "region": REGION,
                "domain": DOMAIN,
                "service_count": len(service_registry),
            }


async def startup_event(app: FastAPI) -> None:
    """Register with parent on startup."""
    global orchestrator_id
    # Wait a bit for parent to be ready
    await asyncio.sleep(2)
    orchestrator_id = await register_with_parent()


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name=f"Child Orchestrator - {REGION or DOMAIN or 'default'}",
            version="1.0.0",
            summary=f"Regional/domain orchestrator for {REGION or DOMAIN or 'default'}",
            description=(
                "Child orchestrator in a multi-level hierarchy. "
                "Manages local services and forwards registrations to parent orchestrator."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .on_startup(startup_event)
    .include_router(ChildOrchestratorRouter.create(prefix="/services", tags=["child-orchestrator"]))
    .build()
)


if __name__ == "__main__":
    from servicekit.api import run_app

    logger.info(
        "child_orchestrator.starting",
        url=f"http://0.0.0.0:{CHILD_PORT}",
        parent_url=PARENT_URL,
        region=REGION,
        domain=DOMAIN,
        register_endpoint=f"http://0.0.0.0:{CHILD_PORT}/services/$register",
    )

    run_app("child_orchestrator:app", port=CHILD_PORT)
