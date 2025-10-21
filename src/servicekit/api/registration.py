"""Service registration with orchestrator for service discovery."""

import asyncio
import os
import socket
from typing import Any

import httpx
from pydantic import BaseModel

from servicekit.logging import get_logger

logger = get_logger(__name__)


async def register_service(
    *,
    orchestrator_url: str | None = None,
    host: str | None = None,
    port: int | None = None,
    info: BaseModel,
    orchestrator_url_env: str = "SERVICEKIT_ORCHESTRATOR_URL",
    host_env: str = "SERVICEKIT_HOST",
    port_env: str = "SERVICEKIT_PORT",
    max_retries: int = 5,
    retry_delay: float = 2.0,
    fail_on_error: bool = False,
    timeout: float = 10.0,
) -> None:
    """Register service with orchestrator for service discovery."""
    # Resolve orchestrator URL
    resolved_orchestrator_url = orchestrator_url or os.getenv(orchestrator_url_env)
    if not resolved_orchestrator_url:
        error_msg = f"Orchestrator URL not provided via parameter or {orchestrator_url_env} environment variable"
        logger.error("registration.missing_orchestrator_url", env_var=orchestrator_url_env)
        if fail_on_error:
            raise ValueError(error_msg)
        logger.warning("registration.skipped", reason="missing orchestrator URL")
        return

    # Resolve host (parameter → auto-detect → env var)
    resolved_host: str | None = None
    host_source = "unknown"

    if host:
        resolved_host = host
        host_source = "parameter"
    else:
        # Try auto-detection via socket.gethostname()
        try:
            resolved_host = socket.gethostname()
            host_source = "auto-detected"
        except Exception as e:
            logger.debug("registration.hostname_detection_failed", error=str(e))

        # Fallback to environment variable
        if not resolved_host:
            resolved_host = os.getenv(host_env)
            if resolved_host:
                host_source = f"env:{host_env}"

    if not resolved_host:
        error_msg = f"Host not provided via parameter, auto-detection, or {host_env} environment variable"
        logger.error("registration.missing_host", env_var=host_env)
        if fail_on_error:
            raise ValueError(error_msg)
        logger.warning("registration.skipped", reason="missing host")
        return

    # Resolve port (parameter → env var → default)
    resolved_port: int = 8000
    port_source = "default"

    if port is not None:
        resolved_port = port
        port_source = "parameter"
    else:
        port_str = os.getenv(port_env)
        if port_str:
            try:
                resolved_port = int(port_str)
                port_source = f"env:{port_env}"
            except ValueError:
                logger.warning(
                    "registration.invalid_port",
                    env_var=port_env,
                    value=port_str,
                    using_default=8000,
                )

    # Build service URL
    service_url = f"http://{resolved_host}:{resolved_port}"

    # Build registration payload
    payload: dict[str, Any] = {
        "url": service_url,
        "info": info.model_dump(mode="json"),
    }

    logger.info(
        "registration.starting",
        orchestrator_url=resolved_orchestrator_url,
        service_url=service_url,
        host_source=host_source,
        port_source=port_source,
        max_retries=max_retries,
    )

    # Registration with retry logic
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    resolved_orchestrator_url,
                    json=payload,
                )
                response.raise_for_status()

                # Parse response to extract service ID
                response_data = response.json()
                service_id = response_data.get("id")

                log_context = {
                    "orchestrator_url": resolved_orchestrator_url,
                    "service_url": service_url,
                    "attempt": attempt,
                    "status_code": response.status_code,
                }
                if service_id:
                    log_context["service_id"] = service_id

                logger.info("registration.success", **log_context)
                return

        except Exception as e:
            last_error = e
            logger.warning(
                "registration.attempt_failed",
                orchestrator_url=resolved_orchestrator_url,
                service_url=service_url,
                attempt=attempt,
                max_retries=max_retries,
                error=str(e),
                error_type=type(e).__name__,
            )

            if attempt < max_retries:
                logger.debug(
                    "registration.retrying",
                    retry_delay=retry_delay,
                    next_attempt=attempt + 1,
                )
                await asyncio.sleep(retry_delay)

    # All retries exhausted
    logger.error(
        "registration.failed",
        orchestrator_url=resolved_orchestrator_url,
        service_url=service_url,
        attempts=max_retries,
        last_error=str(last_error),
    )

    if fail_on_error:
        raise RuntimeError(f"Failed to register service after {max_retries} attempts: {last_error}") from last_error
