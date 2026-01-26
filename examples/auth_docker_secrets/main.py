"""Example API with Docker secrets file authentication for container deployments."""

from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            id="auth-docker-secrets-example",
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
    .with_system()
    .with_auth(
        # For local demo, reads from secrets/api_keys.txt
        # In production with Docker/K8s, this would be:
        #   api_key_file="/run/secrets/api_keys"
        # The file is mounted as a Docker secret at runtime
        api_key_file="secrets/api_keys.txt",
    )
    .with_landing_page()
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
