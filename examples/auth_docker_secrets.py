"""Example API with Docker secrets file authentication for container deployments."""

from servicekit import BaseConfig
from servicekit.api import BaseServiceBuilder, ServiceInfo


class SecureConfig(BaseConfig):
    """Configuration for secure services."""

    service_name: str
    security_level: str = "high"
    audit_enabled: bool = True


app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Secure API with Docker Secrets",
            version="2.0.0",
            summary="Production API using Docker secrets file for authentication",
            description=(
                "Demonstrates Docker secrets file authentication pattern. "
                "API keys are read from a file mounted as a Docker secret at runtime. "
                "Compatible with Docker Compose, Docker Swarm, and Kubernetes."
            ),
            contact={"email": "security@example.com"},
            license_info={"name": "MIT"},
        ),
    )
    .with_logging()
    .with_health()
    .with_config(SecureConfig)
    .with_auth(
        # In production with Docker/K8s, this would be:
        # api_key_file="/run/secrets/api_keys"
        #
        # For local development, use environment variable:
        # export SERVICEKIT_API_KEY_FILE="./secrets/api_keys.txt"
        #
        # The BaseServiceBuilder will automatically read from SERVICEKIT_API_KEY_FILE
        # environment variable if api_key_file parameter is not provided.
    )
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("auth_docker_secrets:app", host="0.0.0.0", port=8000, reload=True)
