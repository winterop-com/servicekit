"""Tests for metrics router and Prometheus endpoint."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from servicekit.api.routers.metrics import MetricsRouter


def test_metrics_endpoint_returns_prometheus_format():
    """Test that the metrics endpoint returns Prometheus formatted metrics."""
    # Create a mock metric reader
    mock_reader = MagicMock()

    # Create FastAPI app
    app = FastAPI()

    # Create and add the metrics router
    metrics_router = MetricsRouter(
        prefix="/metrics",
        tags=["metrics"],
        metric_reader=mock_reader,
    )
    app.include_router(metrics_router.router)

    # Create test client
    client = TestClient(app)

    # Call the metrics endpoint
    response = client.get("/metrics")

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    # Prometheus metrics should be returned (even if empty, it's valid)
    assert isinstance(response.content, bytes)


def test_metrics_router_stores_metric_reader():
    """Test that MetricsRouter stores the metric_reader."""
    mock_reader = MagicMock()

    router = MetricsRouter(
        prefix="/metrics",
        tags=["metrics"],
        metric_reader=mock_reader,
    )

    assert router.metric_reader is mock_reader
