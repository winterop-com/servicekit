"""Vega-Lite visualization service demo.

This example demonstrates:
- Custom Router for data transformation (PandasDataFrame → Vega-Lite spec)
- Multiple chart types (line, bar, scatter, heatmap, aggregations)
- Data processing (filtering, aggregation, pivoting)
- RESTful API design with $ prefix for operations
- Proof of concept for Phase 5.1 (Transformation Service Pattern)
"""

from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from servicekit.api import BaseServiceBuilder, ServiceInfo
from servicekit.api.router import Router
from servicekit.data import DataFrame


class VegaGenerateRequest(BaseModel):
    """Request to generate a Vega-Lite specification from data."""

    data: DataFrame
    chart_type: str = Field(
        ...,
        description="Chart type: line, bar, scatter, heatmap, boxplot, histogram",
    )
    x_field: str | None = Field(None, description="Field for x-axis")
    y_field: str | None = Field(None, description="Field for y-axis")
    color_field: str | None = Field(None, description="Field for color encoding")
    title: str | None = Field(None, description="Chart title")
    width: int = Field(600, description="Chart width in pixels")
    height: int = Field(400, description="Chart height in pixels")
    aggregate: str | None = Field(
        None,
        description="Aggregation function: mean, sum, count, median, min, max",
    )


class VegaAggregateRequest(BaseModel):
    """Request to aggregate data and generate visualization."""

    data: DataFrame
    group_by: list[str] = Field(..., description="Fields to group by")
    agg_field: str = Field(..., description="Field to aggregate")
    agg_func: str = Field(..., description="Aggregation function: mean, sum, count, etc.")
    chart_type: str = Field("bar", description="Chart type for aggregated data")
    title: str | None = None


class VegaResponse(BaseModel):
    """Response containing Vega-Lite specification."""

    spec: dict[str, Any] = Field(..., description="Vega-Lite specification")
    row_count: int = Field(..., description="Number of data rows")
    columns: list[str] = Field(..., description="Data columns")


class VegaRouter(Router):
    """Router for generating Vega-Lite visualizations from PandasDataFrame."""

    def _register_routes(self) -> None:
        """Register Vega visualization endpoints."""

        @self.router.post(
            "/$generate",
            response_model=VegaResponse,
            status_code=status.HTTP_200_OK,
            summary="Generate Vega-Lite spec",
            description="Transform PandasDataFrame to Vega-Lite specification",
        )
        async def generate_vega(request: VegaGenerateRequest) -> VegaResponse:
            """Generate Vega-Lite specification from data."""
            # Convert to pandas DataFrame
            df = request.data.to_pandas()

            # Validate fields exist
            if request.x_field and request.x_field not in df.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{request.x_field}' not found in data",
                )
            if request.y_field and request.y_field not in df.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{request.y_field}' not found in data",
                )

            # Generate spec based on chart type
            spec = self._build_spec(
                df=df,
                chart_type=request.chart_type,
                x_field=request.x_field,
                y_field=request.y_field,
                color_field=request.color_field,
                title=request.title,
                width=request.width,
                height=request.height,
                aggregate=request.aggregate,
            )

            return VegaResponse(
                spec=spec,
                row_count=len(df),
                columns=df.columns.tolist(),
            )

        @self.router.post(
            "/$aggregate",
            response_model=VegaResponse,
            status_code=status.HTTP_200_OK,
            summary="Aggregate and visualize",
            description="Aggregate PandasDataFrame and generate visualization",
        )
        async def aggregate_and_visualize(request: VegaAggregateRequest) -> VegaResponse:
            """Aggregate data and generate visualization."""
            # Convert to pandas DataFrame
            df = request.data.to_pandas()

            # Validate fields
            for field in request.group_by:
                if field not in df.columns:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Group field '{field}' not found in data",
                    )
            if request.agg_field not in df.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Aggregation field '{request.agg_field}' not found in data",
                )

            # Perform aggregation
            agg_df = self._aggregate_data(
                df=df,
                group_by=request.group_by,
                agg_field=request.agg_field,
                agg_func=request.agg_func,
            )

            # Generate spec for aggregated data
            x_field = request.group_by[0] if request.group_by else None
            y_field = f"{request.agg_field}_{request.agg_func}"

            spec = self._build_spec(
                df=agg_df,
                chart_type=request.chart_type,
                x_field=x_field,
                y_field=y_field,
                color_field=request.group_by[1] if len(request.group_by) > 1 else None,
                title=request.title or f"{request.agg_func.title()} of {request.agg_field}",
                width=600,
                height=400,
            )

            return VegaResponse(
                spec=spec,
                row_count=len(agg_df),
                columns=agg_df.columns.tolist(),
            )

    def _build_spec(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_field: str | None,
        y_field: str | None,
        color_field: str | None,
        title: str | None,
        width: int,
        height: int,
        aggregate: str | None = None,
    ) -> dict[str, Any]:
        """Build Vega-Lite specification based on parameters."""
        # Base spec
        spec: dict[str, Any] = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": df.to_dict(orient="records")},
            "width": width,
            "height": height,
        }

        if title:
            spec["title"] = title

        # Chart-specific configurations
        if chart_type == "line":
            spec["mark"] = {"type": "line", "point": True, "tooltip": True}
            spec["encoding"] = self._build_encoding(x_field, y_field, color_field, aggregate)

        elif chart_type == "bar":
            spec["mark"] = {"type": "bar", "tooltip": True}
            spec["encoding"] = self._build_encoding(x_field, y_field, color_field, aggregate)

        elif chart_type == "scatter":
            spec["mark"] = {"type": "point", "tooltip": True}
            spec["encoding"] = self._build_encoding(x_field, y_field, color_field, aggregate)

        elif chart_type == "heatmap":
            spec["mark"] = "rect"
            encoding = self._build_encoding(x_field, y_field, color_field, aggregate)
            # For heatmap, color represents the value
            if aggregate and y_field:
                encoding["color"] = {
                    "field": y_field,
                    "type": "quantitative",
                    "aggregate": aggregate,
                }
            spec["encoding"] = encoding

        elif chart_type == "boxplot":
            spec["mark"] = {"type": "boxplot", "extent": "min-max"}
            spec["encoding"] = self._build_encoding(x_field, y_field, color_field, aggregate=None)

        elif chart_type == "histogram":
            spec["mark"] = "bar"
            spec["encoding"] = {
                "x": {
                    "field": x_field or y_field,
                    "type": "quantitative",
                    "bin": True,
                },
                "y": {"aggregate": "count", "type": "quantitative"},
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported chart type: {chart_type}",
            )

        return spec

    def _build_encoding(
        self,
        x_field: str | None,
        y_field: str | None,
        color_field: str | None,
        aggregate: str | None,
    ) -> dict[str, Any]:
        """Build encoding specification for Vega-Lite."""
        encoding: dict[str, Any] = {}

        if x_field:
            encoding["x"] = {"field": x_field, "type": "nominal"}

        if y_field:
            y_encoding: dict[str, Any] = {"field": y_field, "type": "quantitative"}
            if aggregate:
                y_encoding["aggregate"] = aggregate
            encoding["y"] = y_encoding

        if color_field:
            encoding["color"] = {"field": color_field, "type": "nominal"}

        encoding["tooltip"] = [{"field": f, "type": "nominal"} for f in [x_field, y_field, color_field] if f]

        return encoding

    def _aggregate_data(
        self,
        df: pd.DataFrame,
        group_by: list[str],
        agg_field: str,
        agg_func: str,
    ) -> pd.DataFrame:
        """Aggregate DataFrame by specified fields."""
        if agg_func == "count":
            agg_df = df.groupby(group_by).size().reset_index(name=f"{agg_field}_count")
        else:
            agg_mapping = {f"{agg_field}_{agg_func}": (agg_field, agg_func)}
            agg_df = df.groupby(group_by).agg(**agg_mapping).reset_index()

        return agg_df


# Create router instance
vega_router = VegaRouter.create(
    prefix="/api/v1/visualizations",
    tags=["visualizations"],
)

# Build FastAPI application
app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            display_name="Vega Visualization Service",
            version="1.0.0",
            summary="Transform PandasDataFrame to Vega-Lite specifications",
            description="Proof of concept for Phase 5.1 Transformation Service Pattern. "
            "Accepts PandasDataFrame input and generates Vega-Lite grammar for various chart types. "
            "Supports data processing including aggregation, filtering, and transformations.",
        )
    )
    .with_health()
    .with_system()
    .with_logging()
    .with_monitoring()
    .with_landing_page()
    .include_router(vega_router)
    .build()
)


if __name__ == "__main__":
    from servicekit.api.utilities import run_app

    run_app(app, reload=False)
