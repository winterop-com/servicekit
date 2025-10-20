"""FastAPI service demonstrating job scheduler with polling and SSE streaming."""

import asyncio
from datetime import datetime
from typing import Annotated

import ulid
from fastapi import Depends, Request, Response
from pydantic import BaseModel, Field

from servicekit.api import BaseServiceBuilder, Router, ServiceInfo, build_location_url
from servicekit.api.dependencies import get_scheduler
from servicekit.exceptions import NotFoundError
from servicekit.scheduler import JobScheduler
from servicekit.schemas import JobRecord

ULID = ulid.ULID


class ComputeRequest(BaseModel):
    """Request schema for starting a computation with duration."""

    duration: float = Field(description="How long the computation takes (seconds)", ge=0.1, le=60)


class ComputeResponse(BaseModel):
    """Response schema for submitted computation with job tracking info."""

    job_id: str = Field(description="Job ID for tracking")
    message: str = Field(description="Human-readable message")
    poll_url: str = Field(description="URL for polling job status")
    stream_url: str = Field(description="SSE endpoint URL for real-time status updates")


class ComputeResultResponse(BaseModel):
    """Result of a computation job with status and timestamps."""

    job_id: str
    status: str
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: int | None = None
    error: str | None = None


async def long_running_computation(duration: float) -> int:
    """Simulate a long-running computation task that sleeps for given duration."""
    print(f"[TASK] Starting computation for {duration}s...")
    await asyncio.sleep(duration)
    print("[TASK] Computation complete, returning 42")
    return 42


class ComputeRouter(Router):
    """Router for submitting and polling long-running computation jobs."""

    def _register_routes(self) -> None:
        """Register routes for compute job submission and result polling."""

        @self.router.post("/compute", response_model=ComputeResponse, status_code=202)
        async def submit_computation(  # pyright: ignore[reportUnusedFunction]
            compute_request: ComputeRequest,
            request: Request,
            response: Response,
            scheduler: Annotated[JobScheduler, Depends(get_scheduler)],
        ) -> ComputeResponse:
            """Submit a computation job to the scheduler.

            Returns URLs for both polling and SSE streaming patterns.
            - Polling: Repeatedly GET poll_url to check status
            - Streaming: Connect to stream_url for real-time updates (recommended)
            """
            job_id = await scheduler.add_job(
                long_running_computation,
                compute_request.duration,
            )

            poll_url = f"/api/v1/jobs/{job_id}"
            stream_url = f"/api/v1/jobs/{job_id}/$stream"
            response.headers["Location"] = build_location_url(request, poll_url)

            return ComputeResponse(
                job_id=str(job_id),
                message=f"Job submitted. Use polling (GET {poll_url}) or streaming (GET {stream_url})",
                poll_url=poll_url,
                stream_url=stream_url,
            )

        @self.router.get("/compute/{job_id}/result", response_model=ComputeResultResponse)
        async def get_computation_result(  # pyright: ignore[reportUnusedFunction]
            job_id: str,
            scheduler: Annotated[JobScheduler, Depends(get_scheduler)],
        ) -> ComputeResultResponse:
            """Get the result or status of a computation job."""
            ulid_id = ULID.from_str(job_id)
            try:
                record: JobRecord = await scheduler.get_record(ulid_id)
            except KeyError:
                raise NotFoundError(f"Job {job_id} not found")

            result_value = None
            error_value = None

            if record.status == "completed":
                result_value = await scheduler.get_result(ulid_id)
            elif record.status == "failed":
                error_value = record.error

            return ComputeResultResponse(
                job_id=str(record.id),
                status=record.status,
                submitted_at=record.submitted_at,
                started_at=record.started_at,
                finished_at=record.finished_at,
                result=result_value,
                error=error_value,
            )


info = ServiceInfo(
    display_name="Job Scheduler Demo",
    summary="Demonstrates async job scheduling with polling and SSE streaming",
    version="1.0.0",
    description=(
        "Shows two patterns for monitoring long-running jobs: "
        "1) Polling - repeatedly GET /api/v1/jobs/{id} for status updates, "
        "2) SSE Streaming - connect to /api/v1/jobs/{id}/$stream for real-time push updates. "
        "Submit jobs via POST /api/v1/compute with a duration parameter."
    ),
)

app = (
    BaseServiceBuilder(info=info)
    .with_logging()
    .with_health()
    .with_system()
    .with_jobs(max_concurrency=5)
    .include_router(ComputeRouter.create(prefix="/api/v1", tags=["compute"]))
    .with_landing_page()
    .build()
)


if __name__ == "__main__":
    from servicekit.api import run_app

    run_app("main:app")
