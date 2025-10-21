"""Example API with custom ServiceInfo subclass for registration."""

from servicekit.api import BaseServiceBuilder, ServiceInfo


class CustomServiceInfo(ServiceInfo):
    """Extended service info with custom metadata fields."""

    deployment_env: str = "production"
    team: str = "platform"
    capabilities: list[str] = ["data-processing", "analytics"]
    priority: int = 1


app = (
    BaseServiceBuilder(
        info=CustomServiceInfo(
            display_name="Custom Metadata Service",
            version="2.0.0",
            summary="Demonstrates custom ServiceInfo with additional metadata",
            description=(
                "This service uses a custom ServiceInfo subclass to include "
                "additional metadata in the registration payload. The orchestrator "
                "receives all custom fields for enhanced service discovery."
            ),
            deployment_env="staging",
            team="data-science",
            capabilities=["ml-inference", "feature-extraction"],
            priority=5,
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .with_registration()
    .with_landing_page()
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main_custom:app", host="0.0.0.0", port=8000, reload=True)
