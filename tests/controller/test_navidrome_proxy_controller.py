from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from rivo_drome.api import app


@pytest.fixture
def client():
    with patch("rivo_drome.api.default_container.get") as mock_get:
        mock_controller = MagicMock()
        mock_controller.router = MagicMock()
        mock_get.return_value = mock_controller
        with TestClient(app) as test_client:
            yield test_client


class TestNavidromeProxyController:

    def test_health_route_still_works(self):
        response = TestClient(app).get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_redirect(self):
        response = TestClient(app).get("/", follow_redirects=False)
        assert response.status_code == 307
