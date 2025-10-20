"""Example API with environment variable authentication for production deployments."""

from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Production API with Environment Variable Auth",
            version="2.0.0",
            summary="Production-ready API using environment variables for authentication",
            description=(
                "Demonstrates the recommended approach for production deployments: "
                "reading API keys from SERVICEKIT_API_KEYS environment variable. "
                "Supports multiple keys for zero-downtime rotation."
            ),
            contact={"email": "ops@example.com"},
            license_info={"name": "MIT"},
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    .with_auth()  # Reads from SERVICEKIT_API_KEYS environment variable (recommended!)
    .with_landing_page()
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
