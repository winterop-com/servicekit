"""Tests for service registration with orchestrator."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from servicekit.api.registration import deregister_service, register_service, start_keepalive, stop_keepalive
from servicekit.api.service_builder import ServiceInfo


class CustomServiceInfo(ServiceInfo):
    """Custom ServiceInfo with additional fields."""

    team: str = "platform"
    priority: int = 1


@pytest.mark.asyncio
async def test_successful_registration():
    """Test successful service registration."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "id": "01K83B5V85PQZ1HTH4DQ7NC9JM",
            "status": "registered",
            "service_url": "http://test-service:8000",
            "message": "Service registered successfully",
        }
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
        )

        # Verify POST was called with correct payload
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        assert call_args[0][0] == "http://orchestrator:9000/services/$register"
        payload = call_args[1]["json"]
        assert payload["url"] == "http://test-service:8000"
        assert payload["info"]["display_name"] == "Test Service"


@pytest.mark.asyncio
async def test_retry_logic_success_on_second_attempt():
    """Test retry logic succeeds on second attempt."""
    mock_response_fail = MagicMock()
    mock_response_fail.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500 error", request=MagicMock(), response=MagicMock())
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json = MagicMock(
        return_value={
            "id": "01K83B5V85PQZ1HTH4DQ7NC9JM",
            "status": "registered",
            "service_url": "http://test-service:8000",
            "message": "Service registered successfully",
        }
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=[mock_response_fail, mock_response_success]
        )

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
            max_retries=3,
            retry_delay=0.1,  # Short delay for testing
        )

        # Should have been called twice (fail, then success)
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 2


@pytest.mark.asyncio
async def test_fail_on_error_true_raises_exception():
    """Test that fail_on_error=True raises exception after retries exhausted."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500 error", request=MagicMock(), response=MagicMock())
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        with pytest.raises(RuntimeError, match="Failed to register service"):
            await register_service(
                orchestrator_url="http://orchestrator:9000/services/$register",
                host="test-service",
                port=8000,
                info=info,
                max_retries=2,
                retry_delay=0.1,
                fail_on_error=True,
            )


@pytest.mark.asyncio
async def test_fail_on_error_false_continues():
    """Test that fail_on_error=False logs warning and continues."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500 error", request=MagicMock(), response=MagicMock())
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        # Should not raise exception
        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
            max_retries=2,
            retry_delay=0.1,
            fail_on_error=False,
        )


@pytest.mark.asyncio
async def test_hostname_resolution_parameter():
    """Test hostname resolution from parameter."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client, patch.dict(os.environ, {}, clear=True):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="param-hostname",  # Explicit parameter
            port=8000,
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://param-hostname:8000"


@pytest.mark.asyncio
async def test_hostname_resolution_auto_detect():
    """Test hostname resolution from socket.gethostname()."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.AsyncClient") as mock_client,
        patch("socket.gethostname", return_value="container-name"),
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host=None,  # No explicit host
            port=8000,
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://container-name:8000"


@pytest.mark.asyncio
async def test_hostname_resolution_env_var():
    """Test hostname resolution from environment variable."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.AsyncClient") as mock_client,
        patch("socket.gethostname", side_effect=Exception("No hostname")),
        patch.dict(os.environ, {"SERVICEKIT_HOST": "env-hostname"}),
    ):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host=None,
            port=8000,
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://env-hostname:8000"


@pytest.mark.asyncio
async def test_hostname_missing_raises_with_fail_on_error():
    """Test missing hostname raises exception when fail_on_error=True."""
    with patch("socket.gethostname", side_effect=Exception("No hostname")), patch.dict(os.environ, {}, clear=True):
        info = ServiceInfo(display_name="Test Service")

        # Should log warning and return early (no exception with fail_on_error=False)
        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host=None,
            port=8000,
            info=info,
            fail_on_error=False,
        )

        # With fail_on_error=True, should raise
        with pytest.raises(ValueError, match="Host not provided"):
            await register_service(
                orchestrator_url="http://orchestrator:9000/services/$register",
                host=None,
                port=8000,
                info=info,
                fail_on_error=True,
            )


@pytest.mark.asyncio
async def test_port_resolution_parameter():
    """Test port resolution from parameter."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=9999,  # Explicit parameter
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://test-service:9999"


@pytest.mark.asyncio
async def test_port_resolution_env_var():
    """Test port resolution from environment variable."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client, patch.dict(os.environ, {"SERVICEKIT_PORT": "7777"}):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=None,  # No explicit port
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://test-service:7777"


@pytest.mark.asyncio
async def test_port_resolution_default():
    """Test port resolution defaults to 8000."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client, patch.dict(os.environ, {}, clear=True):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=None,
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://test-service:8000"


@pytest.mark.asyncio
async def test_custom_env_var_names():
    """Test custom environment variable names."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.AsyncClient") as mock_client,
        patch("socket.gethostname", side_effect=Exception("No auto-detect")),  # Prevent auto-detection
        patch.dict(
            os.environ,
            {
                "MY_ORCHESTRATOR_URL": "http://custom-orch:9000/register",
                "MY_HOST": "custom-host",
                "MY_PORT": "5555",
            },
        ),
    ):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url=None,
            host=None,
            port=None,
            info=info,
            orchestrator_url_env="MY_ORCHESTRATOR_URL",
            host_env="MY_HOST",
            port_env="MY_PORT",
        )

        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        assert call_args[0][0] == "http://custom-orch:9000/register"
        payload = call_args[1]["json"]
        assert payload["url"] == "http://custom-host:5555"


@pytest.mark.asyncio
async def test_custom_serviceinfo_serialization():
    """Test that custom ServiceInfo subclasses serialize correctly."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = CustomServiceInfo(
            display_name="Custom Service",
            version="2.0.0",
            team="data-science",
            priority=5,
        )

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["info"]["display_name"] == "Custom Service"
        assert payload["info"]["version"] == "2.0.0"
        assert payload["info"]["team"] == "data-science"
        assert payload["info"]["priority"] == 5


@pytest.mark.asyncio
async def test_missing_orchestrator_url():
    """Test missing orchestrator URL."""
    with patch.dict(os.environ, {}, clear=True):
        info = ServiceInfo(display_name="Test Service")

        # Should log warning and return early (no exception with fail_on_error=False)
        await register_service(
            orchestrator_url=None,
            host="test-service",
            port=8000,
            info=info,
            fail_on_error=False,
        )

        # With fail_on_error=True, should raise
        with pytest.raises(ValueError, match="Orchestrator URL not provided"):
            await register_service(
                orchestrator_url=None,
                host="test-service",
                port=8000,
                info=info,
                fail_on_error=True,
            )


@pytest.mark.asyncio
async def test_url_construction():
    """Test correct URL construction."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="my-service",
            port=8080,
            info=info,
        )

        payload = mock_client.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["url"] == "http://my-service:8080"


@pytest.mark.asyncio
async def test_timeout_parameter():
    """Test that timeout parameter is passed to httpx client."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
            timeout=5.0,
        )

        # Verify AsyncClient was called with timeout
        assert mock_client.call_args[1]["timeout"] == 5.0


@pytest.mark.asyncio
async def test_registration_returns_info():
    """Test that successful registration returns registration info."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "id": "01K83B5V85PQZ1HTH4DQ7NC9JM",
            "status": "registered",
            "service_url": "http://test-service:8000",
            "message": "Service registered successfully",
            "ttl_seconds": 30,
            "ping_url": "http://orchestrator:9000/services/01K83B5V85PQZ1HTH4DQ7NC9JM/$ping",
        }
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        result = await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
        )

        assert result is not None
        assert result["service_id"] == "01K83B5V85PQZ1HTH4DQ7NC9JM"
        assert result["service_url"] == "http://test-service:8000"
        assert result["ttl_seconds"] == 30
        assert result["ping_url"] == "http://orchestrator:9000/services/01K83B5V85PQZ1HTH4DQ7NC9JM/$ping"


@pytest.mark.asyncio
async def test_registration_returns_none_on_failure():
    """Test that failed registration returns None."""
    with patch.dict(os.environ, {}, clear=True):
        info = ServiceInfo(display_name="Test Service")

        result = await register_service(
            orchestrator_url=None,  # Missing URL
            host="test-service",
            port=8000,
            info=info,
            fail_on_error=False,
        )

        assert result is None


@pytest.mark.asyncio
async def test_start_keepalive():
    """Test starting keepalive background task."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "id": "01K83B5V85PQZ1HTH4DQ7NC9JM",
            "status": "alive",
            "last_ping_at": "2025-10-27T12:00:00Z",
            "expires_at": "2025-10-27T12:00:30Z",
        }
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(return_value=mock_response)

        # Start keepalive with short interval for testing
        await start_keepalive(
            ping_url="http://orchestrator:9000/services/01K83B5V85PQZ1HTH4DQ7NC9JM/$ping",
            interval=0.1,
            timeout=5.0,
        )

        # Give it time for at least one ping
        await asyncio.sleep(0.15)

        # Verify PUT was called
        assert mock_client.return_value.__aenter__.return_value.put.call_count >= 1

        # Clean up
        await stop_keepalive()


@pytest.mark.asyncio
async def test_stop_keepalive():
    """Test stopping keepalive background task."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"status": "alive"})

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(return_value=mock_response)

        # Start keepalive
        await start_keepalive(
            ping_url="http://orchestrator:9000/services/test/$ping",
            interval=0.1,
            timeout=5.0,
        )

        # Stop it immediately
        await stop_keepalive()

        # Give it time to ensure it doesn't ping again
        initial_count = mock_client.return_value.__aenter__.return_value.put.call_count
        await asyncio.sleep(0.2)
        final_count = mock_client.return_value.__aenter__.return_value.put.call_count

        # Call count should not increase after stop
        assert final_count == initial_count


@pytest.mark.asyncio
async def test_keepalive_handles_errors_gracefully():
    """Test that keepalive task handles ping failures without crashing."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500 error", request=MagicMock(), response=MagicMock())
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(return_value=mock_response)

        # Start keepalive - should not crash despite errors
        await start_keepalive(
            ping_url="http://orchestrator:9000/services/test/$ping",
            interval=0.1,
            timeout=5.0,
        )

        # Wait for at least one ping attempt
        await asyncio.sleep(0.15)

        # Task should still be running despite error
        assert mock_client.return_value.__aenter__.return_value.put.call_count >= 1

        # Clean up
        await stop_keepalive()


@pytest.mark.asyncio
async def test_deregister_service_success():
    """Test successful service deregistration."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.delete = AsyncMock(return_value=mock_response)

        await deregister_service(
            service_id="01K83B5V85PQZ1HTH4DQ7NC9JM",
            orchestrator_url="http://orchestrator:9000/services/$register",
            timeout=5.0,
        )

        # Verify DELETE was called with correct URL
        call_args = mock_client.return_value.__aenter__.return_value.delete.call_args
        assert call_args[0][0] == "http://orchestrator:9000/services/01K83B5V85PQZ1HTH4DQ7NC9JM"


@pytest.mark.asyncio
async def test_deregister_service_handles_errors():
    """Test that deregister_service handles errors gracefully."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("404 error", request=MagicMock(), response=MagicMock())
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.delete = AsyncMock(return_value=mock_response)

        # Should not raise exception, just log warning
        await deregister_service(
            service_id="01K83B5V85PQZ1HTH4DQ7NC9JM",
            orchestrator_url="http://orchestrator:9000/services/$register",
            timeout=5.0,
        )


@pytest.mark.asyncio
async def test_registration_with_service_key_parameter():
    """Test registration sends X-Service-Key header when service_key parameter is provided."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "01K83B5V85PQZ1HTH4DQ7NC9JM", "status": "registered"})

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
            service_key="my-secret-key",
        )

        # Verify POST was called with X-Service-Key header
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        headers = call_args[1].get("headers")
        assert headers is not None
        assert headers.get("X-Service-Key") == "my-secret-key"


@pytest.mark.asyncio
async def test_registration_with_service_key_from_env():
    """Test registration sends X-Service-Key header from default environment variable."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "01K83B5V85PQZ1HTH4DQ7NC9JM", "status": "registered"})

    with (
        patch("httpx.AsyncClient") as mock_client,
        patch.dict(os.environ, {"SERVICEKIT_REGISTRATION_KEY": "env-secret-key"}),
    ):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
        )

        # Verify POST was called with X-Service-Key header from env
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        headers = call_args[1].get("headers")
        assert headers is not None
        assert headers.get("X-Service-Key") == "env-secret-key"


@pytest.mark.asyncio
async def test_registration_with_custom_service_key_env():
    """Test registration uses custom environment variable name for service key."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "01K83B5V85PQZ1HTH4DQ7NC9JM", "status": "registered"})

    with (
        patch("httpx.AsyncClient") as mock_client,
        patch.dict(os.environ, {"MY_CUSTOM_SERVICE_KEY": "custom-env-key"}),
    ):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
            service_key_env="MY_CUSTOM_SERVICE_KEY",
        )

        # Verify POST was called with X-Service-Key header from custom env
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        headers = call_args[1].get("headers")
        assert headers is not None
        assert headers.get("X-Service-Key") == "custom-env-key"


@pytest.mark.asyncio
async def test_registration_without_service_key():
    """Test registration works without service key (backwards compatibility)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "01K83B5V85PQZ1HTH4DQ7NC9JM", "status": "registered"})

    with patch("httpx.AsyncClient") as mock_client, patch.dict(os.environ, {}, clear=True):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
        )

        # Verify POST was called without headers (or with None)
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        headers = call_args[1].get("headers")
        assert headers is None


@pytest.mark.asyncio
async def test_service_key_parameter_overrides_env():
    """Test that service_key parameter takes precedence over environment variable."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "01K83B5V85PQZ1HTH4DQ7NC9JM", "status": "registered"})

    with (
        patch("httpx.AsyncClient") as mock_client,
        patch.dict(os.environ, {"SERVICEKIT_REGISTRATION_KEY": "env-key"}),
    ):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        info = ServiceInfo(display_name="Test Service", version="1.0.0")

        await register_service(
            orchestrator_url="http://orchestrator:9000/services/$register",
            host="test-service",
            port=8000,
            info=info,
            service_key="param-key",  # Should override env
        )

        # Verify POST was called with parameter value, not env value
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        headers = call_args[1].get("headers")
        assert headers is not None
        assert headers.get("X-Service-Key") == "param-key"


@pytest.mark.asyncio
async def test_keepalive_sends_service_key():
    """Test that keepalive pings include X-Service-Key header."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"status": "alive", "last_ping_at": "2025-01-01T00:00:00Z"})

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(return_value=mock_response)

        # Start keepalive with service key
        await start_keepalive(
            ping_url="http://orchestrator:9000/services/test/$ping",
            interval=0.1,
            timeout=5.0,
            service_key="keepalive-secret-key",
        )

        # Wait for at least one ping
        await asyncio.sleep(0.15)

        # Verify PUT was called with X-Service-Key header
        call_args = mock_client.return_value.__aenter__.return_value.put.call_args
        headers = call_args[1].get("headers")
        assert headers is not None
        assert headers.get("X-Service-Key") == "keepalive-secret-key"

        # Clean up
        await stop_keepalive()


@pytest.mark.asyncio
async def test_deregister_sends_service_key():
    """Test that deregistration includes X-Service-Key header."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.delete = AsyncMock(return_value=mock_response)

        await deregister_service(
            service_id="01K83B5V85PQZ1HTH4DQ7NC9JM",
            orchestrator_url="http://orchestrator:9000/services/$register",
            timeout=5.0,
            service_key="deregister-secret-key",
        )

        # Verify DELETE was called with X-Service-Key header
        call_args = mock_client.return_value.__aenter__.return_value.delete.call_args
        headers = call_args[1].get("headers")
        assert headers is not None
        assert headers.get("X-Service-Key") == "deregister-secret-key"
