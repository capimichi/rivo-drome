import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from starlette.requests import Request

from rivo_drome.config.navidrome_config import NavidromeConfig
from rivo_drome.logger.proxy_logger import ProxyLogger
from rivo_drome.manager.navidrome_sample_response_manager import NavidromeSampleResponseManager
from rivo_drome.service.navidrome_proxy_service import NavidromeProxyService


@pytest.fixture
def proxy_service():
    logger = MagicMock(spec=ProxyLogger)
    sample_manager = MagicMock(spec=NavidromeSampleResponseManager)
    config = NavidromeConfig(url="http://localhost:4533")
    svc = NavidromeProxyService.__new__(NavidromeProxyService)
    svc.navidrome_url = config.url.rstrip("/")
    svc.proxy_logger = logger
    svc.sample_manager = sample_manager
    svc.client = AsyncMock(spec=httpx.AsyncClient)
    return svc


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.method = "GET"
    req.query_params = {}
    req.headers = {"host": "test", "accept": "*/*"}
    req.body = AsyncMock(return_value=b"")
    return req


class TestNavidromeProxyService:

    @pytest.mark.asyncio
    async def test_proxy_request_json_response(self, proxy_service, mock_request):
        json_body = json.dumps({"subsonic-response": {"status": "ok"}}).encode()

        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.aread = AsyncMock(return_value=json_body)
        mock_resp.aclose = AsyncMock()

        proxy_service.client.build_request = MagicMock()
        proxy_service.client.send = AsyncMock(return_value=mock_resp)

        result = await proxy_service.proxy_request(mock_request, "rest/ping.view")

        import starlette.responses
        assert isinstance(result, starlette.responses.JSONResponse)
        body = json.loads(result.body)
        assert body["subsonic-response"]["status"] == "ok"

        proxy_service.proxy_logger.log_call.assert_called_once()
        proxy_service.sample_manager.save_sample.assert_called_once_with("rest/ping.view", json_body)
        mock_resp.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_proxy_request_streaming_response(self, proxy_service, mock_request):
        audio_data = b"fake audio data"

        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "audio/mpeg"}
        mock_resp.aiter_bytes.return_value = AsyncMock(__aiter__=lambda: iter([audio_data]))
        mock_resp.aclose = AsyncMock()

        proxy_service.client.build_request = MagicMock()
        proxy_service.client.send = AsyncMock(return_value=mock_resp)

        result = await proxy_service.proxy_request(mock_request, "rest/stream.view")

        import starlette.responses
        assert isinstance(result, starlette.responses.StreamingResponse)
        proxy_service.proxy_logger.log_call.assert_called_once()
        proxy_service.sample_manager.save_sample.assert_not_called()

    @pytest.mark.asyncio
    async def test_proxy_request_target_url(self, proxy_service, mock_request):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.aread = AsyncMock(return_value=b"{}")
        mock_resp.aclose = AsyncMock()

        proxy_service.client.build_request = MagicMock()
        proxy_service.client.send = AsyncMock(return_value=mock_resp)

        await proxy_service.proxy_request(mock_request, "rest/ping.view")

        proxy_service.client.build_request.assert_called_once()
        call_kwargs = proxy_service.client.build_request.call_args.kwargs
        assert "http://localhost:4533/rest/ping.view" in str(call_kwargs["url"])

    @pytest.mark.asyncio
    async def test_forward_headers_strips_host_and_content_length(self, proxy_service, mock_request):
        mock_request.headers = {
            "host": "originalhost",
            "content-length": "42",
            "authorization": "Bearer token",
            "accept": "application/json",
        }
        mock_request.body = AsyncMock(return_value=b"{}")

        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.aread = AsyncMock(return_value=b"{}")
        mock_resp.aclose = AsyncMock()

        proxy_service.client.build_request = MagicMock()
        proxy_service.client.send = AsyncMock(return_value=mock_resp)

        await proxy_service.proxy_request(mock_request, "rest/ping.view")

        call_kwargs = proxy_service.client.build_request.call_args.kwargs
        forwarded = call_kwargs["headers"]
        assert "host" not in forwarded
        assert "content-length" not in forwarded
        assert forwarded.get("authorization") == "Bearer token"
        assert forwarded.get("accept") == "application/json"
