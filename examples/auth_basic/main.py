"""Example API with API key authentication."""

from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Authenticated API Example",
            version="1.0.0",
            summary="Basic API key authentication example",
            description=(
                "Demonstrates API key authentication with hardcoded keys for development. "
                "Shows the simplest auth setup pattern using the with_auth() method with "
                "explicit api_keys parameter. For production, use environment variables "
                "or Docker secrets instead."
            ),
        )
    )
    .with_logging()
    .with_health()
    .with_system()
    .with_auth(
        # For this example, using direct keys (NOT recommended for production!)
        # In production, use one of these instead:
        #   .with_auth()  # Reads from SERVICEKIT_API_KEYS env var (recommended)
        #   .with_auth(api_key_file="/run/secrets/api_keys")  # Docker secrets
        api_keys=["sk_dev_abc123", "sk_dev_xyz789"],
    )
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
