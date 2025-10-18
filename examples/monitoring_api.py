"""Monitoring example with OpenTelemetry and Prometheus metrics."""

from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Monitoring Example Service",
            version="1.0.0",
            summary="Service with OpenTelemetry monitoring and Prometheus metrics",
            description="Demonstrates automatic instrumentation of FastAPI and SQLAlchemy "
            "with metrics exposed at /metrics endpoint. Includes health check endpoint.",
        )
    )
    .with_database()
    .with_health()
    .with_system()
    .with_monitoring()  # Enables OpenTelemetry with Prometheus endpoint at /metrics
    .with_logging()
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("monitoring_api:app", host="0.0.0.0", port=8000, reload=True)
