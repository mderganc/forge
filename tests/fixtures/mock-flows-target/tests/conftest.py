import pytest
from fastapi.testclient import TestClient

from app.main import app, get_db
from app import models


@pytest.fixture
def app_client() -> TestClient:
    """Provide a TestClient for the app."""
    return TestClient(app)


@pytest.fixture
def seeded_db():
    """Reset database and seed with test data.

    Seeds:
    - 2 admin records
    - 1 member record
    - 1 public record
    """
    # Reset the global connection to get a fresh DB
    import app.main as app_module
    app_module._db_conn = None

    db = get_db()
    models.init_db(db)

    # Seed admin records
    models.create_record(db, "admin_record_1", "data1", "admin")
    models.create_record(db, "admin_record_2", "data2", "admin")

    # Seed member record
    models.create_record(db, "member_record_1", "data3", "member")

    # Seed public record (marked differently in DB)
    # For simplicity, insert directly with is_public=1
    db.execute(
        "INSERT INTO records (name, data, role, is_public) VALUES (?, ?, ?, ?)",
        ("public_record_1", "data4", "public", 1),
    )
    db.commit()

    yield db
