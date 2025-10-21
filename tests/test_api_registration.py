"""Tests for service registration with orchestrator."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from servicekit.api.registration import register_service
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
