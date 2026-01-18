from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_rankings_endpoint_returns_success():
    response = client.get("/rankings")

    assert response.status_code == 200, "Status code is not 200"

    data = response.json()
    assert "rankings" in data, "rankings is not in the response"
    assert "updatedAtTimestamp" in data, "updatedAtTimestamp is not in the response"
    assert len(data["rankings"]) > 0, "rankings is empty/Null"