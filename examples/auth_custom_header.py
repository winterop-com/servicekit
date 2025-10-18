"""Example API with custom authentication header for legacy system integration."""

from servicekit import BaseConfig
from servicekit.api import BaseServiceBuilder, ServiceInfo


class CustomAuthConfig(BaseConfig):
    """Configuration for service with custom auth header."""

    api_version: str = "v1"
    custom_feature_enabled: bool = True


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="API with Custom Authentication Header",
            version="1.0.0",
            summary="API using custom header name for authentication",
            description=(
                "Demonstrates custom authentication header configuration. "
                "Uses 'X-Custom-Auth-Token' instead of default 'X-API-Key'. "
                "Useful for legacy system integration or compliance requirements."
            ),
            contact={"email": "api@example.com"},
            license_info={"name": "MIT"},
        ),
    )
    .with_logging()
    .with_health()
    .with_config(CustomAuthConfig)
    .with_auth(
        header_name="X-Custom-Auth-Token",  # Custom header name instead of "X-API-Key"
        # Keys still from SERVICEKIT_API_KEYS environment variable
    )
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("auth_custom_header:app", host="0.0.0.0", port=8000, reload=True)
