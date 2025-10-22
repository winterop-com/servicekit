"""Tests for Vega visualization example."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def vega_client() -> TestClient:
    """Create test client for vega visualization service."""
    pytest.importorskip("pandas", reason="pandas not installed")
    pytest.importorskip("altair", reason="altair not installed")
    pytest.importorskip("vl_convert", reason="vl-convert-python not installed")

    import sys
    from pathlib import Path

    example_path = Path(__file__).parent.parent / "examples" / "vega_visualization"
    sys.path.insert(0, str(example_path))

    from main import app  # type: ignore[import-not-found]

    sys.path.pop(0)
    return TestClient(app)


class TestHealthAndSystem:
    """Test basic service endpoints."""

    def test_health_check(self, vega_client: TestClient) -> None:
        """Health endpoint should return 200."""
        response = vega_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_system_info(self, vega_client: TestClient) -> None:
        """System endpoint should return system information."""
        response = vega_client.get("/api/v1/system")
        assert response.status_code == 200
        data = response.json()
        assert "current_time" in data
        assert "python_version" in data
        assert "platform" in data


class TestVegaGenerate:
    """Test /$generate endpoint with various chart types."""

    def test_generate_line_chart(self, vega_client: TestClient) -> None:
        """Generate a line chart from data."""
        request_data = {
            "data": {
                "columns": ["month", "sales"],
                "data": [
                    ["Jan", 100],
                    ["Feb", 150],
                    ["Mar", 180],
                ],
            },
            "chart_type": "line",
            "x_field": "month",
            "y_field": "sales",
            "title": "Monthly Sales",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["row_count"] == 3
        assert data["columns"] == ["month", "sales"]

        spec = data["spec"]
        assert spec["$schema"] == "https://vega.github.io/schema/vega-lite/v5.json"
        assert spec["mark"]["type"] == "line"
        assert spec["title"] == "Monthly Sales"
        assert spec["encoding"]["x"]["field"] == "month"
        assert spec["encoding"]["y"]["field"] == "sales"

    def test_generate_bar_chart(self, vega_client: TestClient) -> None:
        """Generate a bar chart from data."""
        request_data = {
            "data": {
                "columns": ["category", "value"],
                "data": [["A", 10], ["B", 20], ["C", 15]],
            },
            "chart_type": "bar",
            "x_field": "category",
            "y_field": "value",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        spec = data["spec"]
        assert spec["mark"]["type"] == "bar"

    def test_generate_scatter_plot(self, vega_client: TestClient) -> None:
        """Generate a scatter plot from data."""
        request_data = {
            "data": {
                "columns": ["x", "y", "category"],
                "data": [[1, 10, "A"], [2, 20, "B"], [3, 15, "A"]],
            },
            "chart_type": "scatter",
            "x_field": "x",
            "y_field": "y",
            "color_field": "category",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        spec = data["spec"]
        assert spec["mark"]["type"] == "point"
        assert spec["encoding"]["color"]["field"] == "category"

    def test_generate_heatmap(self, vega_client: TestClient) -> None:
        """Generate a heatmap from data."""
        request_data = {
            "data": {
                "columns": ["hour", "day", "traffic"],
                "data": [[8, "Mon", 120], [9, "Mon", 180], [8, "Tue", 110]],
            },
            "chart_type": "heatmap",
            "x_field": "hour",
            "y_field": "day",
            "aggregate": "sum",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        spec = data["spec"]
        assert spec["mark"] == "rect"

    def test_generate_histogram(self, vega_client: TestClient) -> None:
        """Generate a histogram from data."""
        request_data = {
            "data": {
                "columns": ["age"],
                "data": [[25], [28], [32], [35], [38]],
            },
            "chart_type": "histogram",
            "x_field": "age",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        spec = data["spec"]
        assert spec["mark"] == "bar"
        assert spec["encoding"]["x"]["bin"] is True

    def test_generate_boxplot(self, vega_client: TestClient) -> None:
        """Generate a boxplot from data."""
        request_data = {
            "data": {
                "columns": ["category", "value"],
                "data": [["A", 10], ["A", 15], ["B", 20], ["B", 25]],
            },
            "chart_type": "boxplot",
            "x_field": "category",
            "y_field": "value",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        spec = data["spec"]
        assert spec["mark"]["type"] == "boxplot"

    def test_generate_with_aggregation(self, vega_client: TestClient) -> None:
        """Generate chart with aggregation."""
        request_data = {
            "data": {
                "columns": ["category", "value"],
                "data": [["A", 10], ["A", 15], ["B", 20]],
            },
            "chart_type": "bar",
            "x_field": "category",
            "y_field": "value",
            "aggregate": "mean",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        spec = data["spec"]
        assert spec["encoding"]["y"]["aggregate"] == "mean"


class TestVegaAggregate:
    """Test /$aggregate endpoint."""

    def test_aggregate_and_visualize(self, vega_client: TestClient) -> None:
        """Aggregate data and generate visualization."""
        request_data = {
            "data": {
                "columns": ["date", "product", "revenue"],
                "data": [
                    ["2025-01-01", "Widget", 100],
                    ["2025-01-01", "Gadget", 75],
                    ["2025-01-02", "Widget", 140],
                    ["2025-01-02", "Gadget", 100],
                ],
            },
            "group_by": ["date"],
            "agg_field": "revenue",
            "agg_func": "sum",
            "chart_type": "bar",
        }

        response = vega_client.post("/api/v1/visualizations/$aggregate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["row_count"] == 2
        assert "revenue_sum" in data["columns"]

    def test_aggregate_with_multiple_groups(self, vega_client: TestClient) -> None:
        """Aggregate with multiple group-by fields."""
        request_data = {
            "data": {
                "columns": ["date", "product", "quantity"],
                "data": [
                    ["2025-01-01", "Widget", 5],
                    ["2025-01-01", "Gadget", 3],
                    ["2025-01-02", "Widget", 7],
                ],
            },
            "group_by": ["date", "product"],
            "agg_field": "quantity",
            "agg_func": "sum",
            "chart_type": "bar",
        }

        response = vega_client.post("/api/v1/visualizations/$aggregate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["row_count"] == 3
        spec = data["spec"]
        assert spec["encoding"]["color"]["field"] == "product"


class TestValidation:
    """Test input validation."""

    def test_invalid_chart_type(self, vega_client: TestClient) -> None:
        """Invalid chart type should return 400."""
        request_data = {
            "data": {
                "columns": ["x", "y"],
                "data": [[1, 2]],
            },
            "chart_type": "invalid",
            "x_field": "x",
            "y_field": "y",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 400
        assert "Unsupported chart type" in response.json()["detail"]

    def test_missing_field_in_data(self, vega_client: TestClient) -> None:
        """Missing field should return 400."""
        request_data = {
            "data": {
                "columns": ["x"],
                "data": [[1], [2]],
            },
            "chart_type": "line",
            "x_field": "x",
            "y_field": "nonexistent",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 400
        assert "not found in data" in response.json()["detail"]

    def test_aggregate_missing_field(self, vega_client: TestClient) -> None:
        """Missing aggregation field should return 400."""
        request_data = {
            "data": {
                "columns": ["category", "value"],
                "data": [["A", 10]],
            },
            "group_by": ["category"],
            "agg_field": "nonexistent",
            "agg_func": "sum",
        }

        response = vega_client.post("/api/v1/visualizations/$aggregate", json=request_data)
        assert response.status_code == 400


class TestDataFormats:
    """Test different data input formats."""

    def test_empty_data(self, vega_client: TestClient) -> None:
        """Handle empty data gracefully."""
        request_data = {
            "data": {
                "columns": [],
                "data": [],
            },
            "chart_type": "line",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 0

    def test_single_row(self, vega_client: TestClient) -> None:
        """Handle single row of data."""
        request_data = {
            "data": {
                "columns": ["x", "y"],
                "data": [[1, 10]],
            },
            "chart_type": "scatter",
            "x_field": "x",
            "y_field": "y",
        }

        response = vega_client.post("/api/v1/visualizations/$generate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 1
