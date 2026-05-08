import sqlite3
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app import models


# In-memory database connection (shared for the app lifecycle)
_db_conn = None


def get_db() -> sqlite3.Connection:
    """Get or create the in-memory database connection."""
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(":memory:", check_same_thread=False)
        models.init_db(_db_conn)
    return _db_conn


app = FastAPI(title="mock-flows-target")


class UploadRequest(BaseModel):
    name: str
    data: str


class UploadResponse(BaseModel):
    id: int
    name: str


class ReportItem(BaseModel):
    id: int
    name: str


@app.post("/upload", response_model=UploadResponse)
def upload(
    body: UploadRequest,
    x_role: Optional[str] = Header(None),
) -> UploadResponse:
    """Upload a record. Requires X-Role header in {admin, member}."""
    if x_role not in ("admin", "member"):
        raise HTTPException(status_code=403, detail="Forbidden")

    db = get_db()
    record_id = models.create_record(db, body.name, body.data, x_role)
    return UploadResponse(id=record_id, name=body.name)


@app.get("/reports", response_model=list[ReportItem])
def reports(x_role: Optional[str] = Header(None)) -> list[ReportItem]:
    """List records based on role permissions.
    - admin: sees all
    - member: sees own
    - viewer: sees public only
    - anonymous (no header): 401
    """
    if x_role is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = get_db()
    records = models.list_records(db, x_role)
    return [ReportItem(**record) for record in records]
