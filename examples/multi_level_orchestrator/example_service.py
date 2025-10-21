"""Example service that registers with child orchestrator."""

import os

from servicekit.api import BaseServiceBuilder, ServiceInfo

# Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "Example Service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:9001/services/$register")
SERVICE_HOST = os.getenv("SERVICE_HOST", "localhost")

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name=SERVICE_NAME,
            version="1.0.0",
            summary=f"Example service: {SERVICE_NAME}",
            description="A simple service that demonstrates multi-level orchestrator registration.",
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .with_registration(
        orchestrator_url=ORCHESTRATOR_URL,
        host=SERVICE_HOST,
        port=SERVICE_PORT,
    )
    .build()
)


if __name__ == "__main__":
    from servicekit.api import run_app
    from servicekit.logging import get_logger

    logger = get_logger(__name__)

    logger.info(
        "example_service.starting",
        name=SERVICE_NAME,
        url=f"http://0.0.0.0:{SERVICE_PORT}",
        orchestrator_url=ORCHESTRATOR_URL,
    )

    run_app("example_service:app", port=SERVICE_PORT)
