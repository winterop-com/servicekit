"""Example API with API key authentication, covering all key sources."""

from servicekit.api import BaseServiceBuilder, ServiceInfo, run_app

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            id="auth-example",
            display_name="Authenticated API Example",
            version="1.0.0",
            description=(
                "Demonstrates API key authentication. The default below reads keys from "
                "the SERVICEKIT_API_KEYS environment variable (recommended for production). "
                "See the README and the commented variants for inline keys, a custom header, "
                "and Docker secrets files."
            ),
        ),
    )
    .with_logging()
    .with_health()
    .with_system()
    # Recommended: read comma-separated keys from SERVICEKIT_API_KEYS (see .env.example).
    .with_auth()
    # Variant 1 - inline keys (development only, never commit real keys):
    #   .with_auth(api_keys=["sk_dev_abc123", "sk_dev_xyz789"])
    # Variant 2 - custom header name instead of the default "X-API-Key":
    #   .with_auth(header_name="X-Custom-Auth-Token")
    # Variant 3 - Docker secrets / mounted file (Compose, Swarm, K8s):
    #   .with_auth(api_key_file="/run/secrets/api_keys")  # local demo: "secrets/api_keys.txt"
    .with_landing_page()
    .build()
)


if __name__ == "__main__":
    run_app(app)
