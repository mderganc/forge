import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            role TEXT NOT NULL,
            is_public INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()


def create_record(
    conn: sqlite3.Connection, name: str, data: str, role: str
) -> int:
    """Create a record and return its ID."""
    cursor = conn.execute(
        "INSERT INTO records (name, data, role, is_public) VALUES (?, ?, ?, ?)",
        (name, data, role, 0),
    )
    conn.commit()
    record_id = cursor.lastrowid
    assert record_id is not None
    return record_id


def list_records(conn: sqlite3.Connection, role: str) -> list[dict]:
    """List records based on role permissions."""
    cursor = conn.execute("SELECT id, name, role FROM records")
    rows = cursor.fetchall()

    records = []
    for row in rows:
        record_id, name, record_role = row
        # Admin sees all
        if role == "admin":
            records.append({"id": record_id, "name": name})
        # Member sees own
        elif role == "member" and record_role == "member":
            records.append({"id": record_id, "name": name})
        # Viewer sees public only
        elif role == "viewer" and record_role == "public":
            records.append({"id": record_id, "name": name})

    return records
