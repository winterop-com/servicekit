"""Service registration with orchestrator for service discovery."""

import asyncio
import os
import socket
from typing import Any

import httpx
from pydantic import BaseModel

from servicekit.logging import get_logger

logger = get_logger(__name__)

# Global references for keepalive management
_keepalive_task: asyncio.Task | None = None
_service_id: str | None = None
_ping_url: str | None = None
_service_key: str | None = None


def _resolve_service_key(service_key: str | None, service_key_env: str) -> str | None:
    """Resolve service key from parameter or environment variable."""
    if service_key:
        return service_key
    return os.getenv(service_key_env)


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
    service_key: str | None = None,
    service_key_env: str = "SERVICEKIT_REGISTRATION_KEY",
) -> dict[str, Any] | None:
    """Register service with orchestrator for service discovery and return registration info."""
    # Resolve service key for authentication
    resolved_service_key = _resolve_service_key(service_key, service_key_env)

    # Store globally for keepalive
    global _service_key
    _service_key = resolved_service_key

    # Resolve orchestrator URL
    resolved_orchestrator_url = orchestrator_url or os.getenv(orchestrator_url_env)
    if not resolved_orchestrator_url:
        error_msg = f"Orchestrator URL not provided via parameter or {orchestrator_url_env} environment variable"
        logger.error("registration.missing_orchestrator_url", env_var=orchestrator_url_env)
        if fail_on_error:
            raise ValueError(error_msg)
        logger.warning("registration.skipped", reason="missing orchestrator URL")
        return None

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
        return None

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

    # Extract service ID from info (requires id attribute)
    service_id = getattr(info, "id", None)
    if not service_id:
        error_msg = "ServiceInfo must have an 'id' attribute for registration"
        logger.error("registration.missing_service_id")
        if fail_on_error:
            raise ValueError(error_msg)
        logger.warning("registration.skipped", reason="missing service ID")
        return None

    # Build registration payload
    payload: dict[str, Any] = {
        "id": service_id,
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

    # Build headers with optional service key
    headers: dict[str, str] = {}
    if resolved_service_key:
        headers["X-Service-Key"] = resolved_service_key

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    resolved_orchestrator_url,
                    json=payload,
                    headers=headers if headers else None,
                )
                response.raise_for_status()

                # Parse response for additional info (ping_url, ttl)
                response_data = response.json()

                log_context = {
                    "orchestrator_url": resolved_orchestrator_url,
                    "service_url": service_url,
                    "service_id": service_id,
                    "attempt": attempt,
                    "status_code": response.status_code,
                }

                # Store global references for keepalive
                global _service_id, _ping_url
                _service_id = service_id
                _ping_url = response_data.get("ping_url")

                logger.info("registration.success", **log_context)

                # Return registration info for keepalive setup
                return {
                    "service_id": service_id,
                    "service_url": service_url,
                    "orchestrator_url": resolved_orchestrator_url,
                    "ttl_seconds": response_data.get("ttl_seconds"),
                    "ping_url": _ping_url,
                }

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

    return None


async def _keepalive_loop(ping_url: str, interval: float, timeout: float, service_key: str | None) -> None:
    """Background task to periodically ping the orchestrator."""
    logger.info("keepalive.started", ping_url=ping_url, interval_seconds=interval)

    # Build headers with optional service key
    headers: dict[str, str] = {}
    if service_key:
        headers["X-Service-Key"] = service_key

    while True:
        try:
            await asyncio.sleep(interval)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.put(ping_url, headers=headers if headers else None)
                response.raise_for_status()

                response_data = response.json()
                logger.debug(
                    "keepalive.ping_success",
                    service_id=_service_id,
                    last_ping_at=response_data.get("last_ping_at"),
                    expires_at=response_data.get("expires_at"),
                )

        except asyncio.CancelledError:
            logger.info("keepalive.cancelled", service_id=_service_id)
            raise

        except Exception as e:
            logger.warning(
                "keepalive.ping_failed",
                service_id=_service_id,
                ping_url=ping_url,
                error=str(e),
                error_type=type(e).__name__,
            )


async def start_keepalive(
    *,
    ping_url: str,
    interval: float = 10.0,
    timeout: float = 10.0,
    service_key: str | None = None,
    service_key_env: str = "SERVICEKIT_REGISTRATION_KEY",
) -> None:
    """Start background keepalive task to ping orchestrator."""
    global _keepalive_task

    if _keepalive_task:
        logger.warning("keepalive.already_running")
        return

    # Resolve service key (use global from registration if not provided)
    resolved_service_key = _resolve_service_key(service_key, service_key_env) or _service_key

    _keepalive_task = asyncio.create_task(_keepalive_loop(ping_url, interval, timeout, resolved_service_key))
    logger.info("keepalive.task_started", ping_url=ping_url, interval_seconds=interval)


async def stop_keepalive() -> None:
    """Stop the background keepalive task."""
    global _keepalive_task

    if _keepalive_task:
        _keepalive_task.cancel()
        try:
            await _keepalive_task
        except asyncio.CancelledError:
            pass
        _keepalive_task = None
        logger.info("keepalive.task_stopped", service_id=_service_id)


async def deregister_service(
    *,
    service_id: str,
    orchestrator_url: str,
    timeout: float = 10.0,
    service_key: str | None = None,
    service_key_env: str = "SERVICEKIT_REGISTRATION_KEY",
) -> None:
    """Explicitly deregister service from orchestrator."""
    # Build deregister URL from orchestrator base URL
    # orchestrator_url is like "http://orchestrator:9000/services/$register"
    # we need "http://orchestrator:9000/services/{service_id}"
    base_url = orchestrator_url.replace("/$register", "")
    deregister_url = f"{base_url}/{service_id}"

    # Resolve service key (use global from registration if not provided)
    resolved_service_key = _resolve_service_key(service_key, service_key_env) or _service_key

    # Build headers with optional service key
    headers: dict[str, str] = {}
    if resolved_service_key:
        headers["X-Service-Key"] = resolved_service_key

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.delete(deregister_url, headers=headers if headers else None)
            response.raise_for_status()

            logger.info(
                "deregistration.success",
                service_id=service_id,
                deregister_url=deregister_url,
                status_code=response.status_code,
            )

    except Exception as e:
        logger.warning(
            "deregistration.failed",
            service_id=service_id,
            deregister_url=deregister_url,
            error=str(e),
            error_type=type(e).__name__,
        )
