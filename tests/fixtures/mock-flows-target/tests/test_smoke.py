"""Smoke test to verify the app starts and basic endpoint works."""
import pytest


def test_app_imports():
    """Test that app can be imported."""
    try:
        from app.main import app
        assert app.title == "mock-flows-target"
    except ImportError as e:
        pytest.skip(f"fastapi not available: {e}")


def test_reports_admin_header(app_client):
    """Test GET /reports with admin role header returns 200."""
    try:
        from app.main import app
    except ImportError:
        pytest.skip("fastapi not available")

    response = app_client.get("/reports", headers={"X-Role": "admin"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_reports_missing_header(app_client):
    """Test GET /reports without X-Role header returns 401."""
    try:
        from app.main import app
    except ImportError:
        pytest.skip("fastapi not available")

    response = app_client.get("/reports")
    assert response.status_code == 401
