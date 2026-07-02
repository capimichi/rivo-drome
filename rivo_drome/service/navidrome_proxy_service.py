import json
from typing import Any

import httpx
from fastapi.responses import JSONResponse, StreamingResponse
from injector import inject
from starlette.background import BackgroundTask
from starlette.requests import Request

from rivo_drome.config.navidrome_config import NavidromeConfig
from rivo_drome.logger.proxy_logger import ProxyLogger
from rivo_drome.manager.navidrome_sample_response_manager import NavidromeSampleResponseManager

class NavidromeProxyService:
    FORWARD_EXCLUDED_HEADERS = {"host", "content-length"}

    @inject
    def __init__(
        self,
        proxy_logger: ProxyLogger,
        sample_manager: NavidromeSampleResponseManager,
        config: NavidromeConfig,
    ):
        self.navidrome_url = config.url.rstrip("/")
        self.proxy_logger = proxy_logger
        self.sample_manager = sample_manager
        self.client = httpx.AsyncClient(timeout=60.0)

    @staticmethod
    def _forward_headers(headers: dict) -> dict:
        return {k: v for k, v in headers.items() if k.lower() not in NavidromeProxyService.FORWARD_EXCLUDED_HEADERS}

    async def proxy_request(self, request: Request, path: str) -> Any:
        target_url = f"{self.navidrome_url}/{path.lstrip('/')}"
        query_params = dict(request.query_params)
        forward_headers = self._forward_headers(dict(request.headers))
        body = await request.body()

        req = self.client.build_request(
            method=request.method,
            url=target_url,
            params=query_params,
            headers=forward_headers,
            content=body or None,
        )

        resp = await self.client.send(req, stream=True)
        status_code = resp.status_code
        resp_headers = dict(resp.headers)
        content_type = resp.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                resp_body = await resp.aread()
                self.proxy_logger.log_call(
                    method=request.method,
                    url=target_url,
                    params=query_params,
                    headers=forward_headers,
                    request_body=body,
                    status_code=status_code,
                    response_headers=resp_headers,
                    response_body=resp_body,
                )
                self.sample_manager.save_sample(path, resp_body)
                return JSONResponse(
                    content=json.loads(resp_body),
                    status_code=status_code,
                    headers=resp_headers,
                )
            finally:
                await resp.aclose()
        else:
            self.proxy_logger.log_call(
                method=request.method,
                url=target_url,
                params=query_params,
                headers=forward_headers,
                request_body=body,
                status_code=status_code,
                response_headers=resp_headers,
                response_body="<streaming>",
            )
            return StreamingResponse(
                content=resp.aiter_bytes(),
                status_code=status_code,
                media_type=content_type,
                headers=resp_headers,
                background=BackgroundTask(resp.aclose),
            )
