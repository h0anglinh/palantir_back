from ..main import app


from fastapi.testclient import TestClient


client = TestClient(app)


def test_docs_page_after_redirect():
    response = client.get("/")
    # Následuj přesměrování
    assert response.status_code == 200
    assert "Palantir - Swagger UI" in response.text