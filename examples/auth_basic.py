"""Example API with API key authentication."""

from servicekit import BaseConfig
from servicekit.api import BaseServiceBuilder, ServiceInfo


class AppConfig(BaseConfig):
    """Application configuration."""

    environment: str
    debug: bool = False


app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="Authenticated API Example"))
    .with_logging()
    .with_health()
    .with_config(AppConfig)
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

    uvicorn.run("auth_basic:app", host="0.0.0.0", port=8000, reload=True)
