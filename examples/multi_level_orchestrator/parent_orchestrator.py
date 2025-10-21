"""Parent orchestrator for multi-level service discovery."""

from datetime import UTC, datetime

from fastapi import Request, Response
from pydantic import BaseModel
from ulid import ULID

from servicekit.api import BaseServiceBuilder, Router, ServiceInfo
from servicekit.api.utilities import build_location_url
from servicekit.exceptions import NotFoundError
from servicekit.logging import get_logger

logger = get_logger(__name__)

# In-memory registries
child_orchestrators: dict[str, dict] = {}
all_services: dict[str, dict] = {}


class OrchestratorRegistrationPayload(BaseModel):
    """Registration payload from child orchestrators."""

    url: str
    info: dict
    region: str | None = None
    domain: str | None = None


class ServiceRegistrationPayload(BaseModel):
    """Registration payload from services via child orchestrators."""

    url: str
    info: dict
    orchestrator_id: str


class RegistrationResponse(BaseModel):
    """Response from registration."""

    id: str
    status: str
    url: str
    message: str


class OrchestratorDetail(BaseModel):
    """Detailed orchestrator information."""

    id: str
    url: str
    info: dict
    region: str | None
    domain: str | None
    registered_at: str
    last_updated: str
    service_count: int


class ServiceDetail(BaseModel):
    """Detailed service information."""

    id: str
    url: str
    info: dict
    orchestrator_id: str
    registered_at: str
    last_updated: str


class OrchestratorListResponse(BaseModel):
    """Response for listing orchestrators."""

    count: int
    orchestrators: list[OrchestratorDetail]


class ServiceListResponse(BaseModel):
    """Response for listing services."""

    count: int
    services: list[ServiceDetail]


class HierarchyResponse(BaseModel):
    """Full hierarchy view."""

    parent_id: str
    parent_info: dict
    orchestrators: list[dict]
    total_services: int


class ParentOrchestratorRouter(Router):
    """Router for parent orchestrator operations."""

    def _register_routes(self) -> None:
        """Register parent orchestrator endpoints."""

        @self.router.post("/orchestrators/$register", response_model=RegistrationResponse, status_code=201)
        async def register_orchestrator(
            request: Request, payload: OrchestratorRegistrationPayload, response: Response
        ) -> RegistrationResponse:
            """Register a child orchestrator."""
            orchestrator_id = str(ULID())

            child_orchestrators[orchestrator_id] = {
                "id": orchestrator_id,
                "url": payload.url,
                "info": payload.info,
                "region": payload.region,
                "domain": payload.domain,
                "registered_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat(),
                "service_count": 0,
            }

            logger.info(
                "orchestrator.registered",
                orchestrator_id=orchestrator_id,
                url=payload.url,
                region=payload.region,
                domain=payload.domain,
            )

            response.headers["Location"] = build_location_url(request, f"/orchestrators/{orchestrator_id}")

            return RegistrationResponse(
                id=orchestrator_id,
                status="registered",
                url=payload.url,
                message=f"Child orchestrator registered in {payload.region or payload.domain or 'default'}",
            )

        @self.router.post("/services/$register", response_model=RegistrationResponse, status_code=201)
        async def register_service(
            request: Request, payload: ServiceRegistrationPayload, response: Response
        ) -> RegistrationResponse:
            """Register a service from a child orchestrator."""
            if payload.orchestrator_id not in child_orchestrators:
                raise NotFoundError(f"Orchestrator {payload.orchestrator_id} not found")

            service_id = str(ULID())

            all_services[service_id] = {
                "id": service_id,
                "url": payload.url,
                "info": payload.info,
                "orchestrator_id": payload.orchestrator_id,
                "registered_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat(),
            }

            # Update orchestrator service count
            child_orchestrators[payload.orchestrator_id]["service_count"] += 1

            logger.info(
                "service.registered",
                service_id=service_id,
                url=payload.url,
                orchestrator_id=payload.orchestrator_id,
            )

            response.headers["Location"] = build_location_url(request, f"/services/{service_id}")

            return RegistrationResponse(
                id=service_id,
                status="registered",
                url=payload.url,
                message=f"Service registered via orchestrator {payload.orchestrator_id}",
            )

        @self.router.get("/orchestrators", response_model=OrchestratorListResponse)
        async def list_orchestrators() -> OrchestratorListResponse:
            """List all registered child orchestrators."""
            orchestrators = [OrchestratorDetail(**orch) for orch in child_orchestrators.values()]
            return OrchestratorListResponse(count=len(orchestrators), orchestrators=orchestrators)

        @self.router.get("/orchestrators/{orchestrator_id}", response_model=OrchestratorDetail)
        async def get_orchestrator(orchestrator_id: str) -> OrchestratorDetail:
            """Get details for a specific orchestrator."""
            if orchestrator_id not in child_orchestrators:
                raise NotFoundError(f"Orchestrator {orchestrator_id} not found")
            return OrchestratorDetail(**child_orchestrators[orchestrator_id])

        @self.router.get("/services", response_model=ServiceListResponse)
        async def list_all_services(orchestrator_id: str | None = None) -> ServiceListResponse:
            """List all services across all orchestrators or filtered by orchestrator."""
            if orchestrator_id:
                services = [
                    ServiceDetail(**svc) for svc in all_services.values() if svc["orchestrator_id"] == orchestrator_id
                ]
            else:
                services = [ServiceDetail(**svc) for svc in all_services.values()]
            return ServiceListResponse(count=len(services), services=services)

        @self.router.get("/services/{service_id}", response_model=ServiceDetail)
        async def get_service(service_id: str) -> ServiceDetail:
            """Get details for a specific service."""
            if service_id not in all_services:
                raise NotFoundError(f"Service {service_id} not found")
            return ServiceDetail(**all_services[service_id])

        @self.router.get("/hierarchy", response_model=HierarchyResponse)
        async def get_hierarchy() -> HierarchyResponse:
            """Get full hierarchy view."""
            orchestrators_with_services = []
            for orch_id, orch in child_orchestrators.items():
                services = [
                    ServiceDetail(**svc).model_dump()
                    for svc in all_services.values()
                    if svc["orchestrator_id"] == orch_id
                ]
                orchestrators_with_services.append(
                    {
                        "orchestrator": OrchestratorDetail(**orch).model_dump(),
                        "services": services,
                    }
                )

            return HierarchyResponse(
                parent_id="parent-orchestrator",
                parent_info={"display_name": "Parent Orchestrator", "level": "global"},
                orchestrators=orchestrators_with_services,
                total_services=len(all_services),
            )

        @self.router.delete("/orchestrators/{orchestrator_id}")
        async def deregister_orchestrator(orchestrator_id: str) -> dict:
            """Deregister a child orchestrator and all its services."""
            if orchestrator_id not in child_orchestrators:
                raise NotFoundError(f"Orchestrator {orchestrator_id} not found")

            # Remove all services from this orchestrator
            service_ids_to_remove = [
                sid for sid, svc in all_services.items() if svc["orchestrator_id"] == orchestrator_id
            ]
            for sid in service_ids_to_remove:
                del all_services[sid]

            orchestrator = child_orchestrators.pop(orchestrator_id)

            logger.info(
                "orchestrator.deregistered",
                orchestrator_id=orchestrator_id,
                services_removed=len(service_ids_to_remove),
            )

            return {
                "status": "deregistered",
                "orchestrator": orchestrator,
                "services_removed": len(service_ids_to_remove),
            }


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Parent Orchestrator",
            version="1.0.0",
            summary="Global orchestrator managing child orchestrators and services",
            description=(
                "Top-level orchestrator in a multi-level hierarchy. "
                "Manages child orchestrators (regional/domain) and provides global service discovery."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .include_router(ParentOrchestratorRouter.create(prefix="/api/v1", tags=["parent-orchestrator"]))
    .build()
)


if __name__ == "__main__":
    from servicekit.api import run_app

    logger.info(
        "parent_orchestrator.starting",
        url="http://0.0.0.0:9000",
        orchestrator_register_endpoint="http://0.0.0.0:9000/api/v1/orchestrators/$register",
        service_register_endpoint="http://0.0.0.0:9000/api/v1/services/$register",
        hierarchy_endpoint="http://0.0.0.0:9000/api/v1/hierarchy",
    )

    run_app("parent_orchestrator:app", port=9000)
