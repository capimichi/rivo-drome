from fastapi import APIRouter
from injector import inject
from starlette.requests import Request

from rivo_drome.service.navidrome_proxy_service import NavidromeProxyService


class NavidromeProxyController:

    @inject
    def __init__(self, proxy_service: NavidromeProxyService):
        self.proxy_service = proxy_service
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "/{path:path}",
            self.proxy,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        )

    async def proxy(self, request: Request, path: str):
        return await self.proxy_service.proxy_request(request, path)
