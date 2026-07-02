import json
from typing import Any

from rivo_drome.logger.abstract_logger import AbstractLogger


class ProxyLogger(AbstractLogger):

    def __init__(self, log_dir: str):
        super().__init__(log_dir)

    def get_logger_name(self) -> str:
        return "proxy"

    def log_call(
        self,
        method: str,
        url: str,
        params: dict | None,
        headers: dict | None,
        request_body: Any,
        status_code: int,
        response_headers: dict | None,
        response_body: Any,
    ) -> None:
        safe_headers = self._sanitize_headers(headers)
        safe_response_headers = self._sanitize_headers(response_headers)

        entry = {
            "method": method,
            "url": url,
            "params": params,
            "headers": safe_headers,
            "request_body": request_body,
            "status_code": status_code,
            "response_headers": safe_response_headers,
            "response_body": response_body,
        }
        self.logger.info(json.dumps(entry, default=str))

    @staticmethod
    def _sanitize_headers(headers: dict | None) -> dict | None:
        if headers is None:
            return None
        sensitive_keys = {"authorization", "cookie", "x-auth-token"}
        return {k: ("***" if k.lower() in sensitive_keys else v) for k, v in headers.items()}
