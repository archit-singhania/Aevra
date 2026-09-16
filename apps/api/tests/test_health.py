from fastapi.testclient import TestClient

from aevra_api.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "aevra-api", "phase": 6}
