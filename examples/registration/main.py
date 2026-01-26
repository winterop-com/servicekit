"""Example API with service registration to orchestrator."""

from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            id="registration-example",
            display_name="Registration Example Service",
            version="1.0.0",
            description=(
                "This service automatically registers itself with an orchestrator on startup. "
                "The orchestrator can then discover and monitor this service. "
                "Hostname is auto-detected from Docker container name."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .with_registration()  # Auto-detect hostname, reads SERVICEKIT_ORCHESTRATOR_URL from env
    .with_landing_page()
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
