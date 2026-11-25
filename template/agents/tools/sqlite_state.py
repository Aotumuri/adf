"""Transactional runtime state storage for ADF."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from storage import RUNTIME, ROOT, now, read


SCHEMA_VERSION = 1
DB = RUNTIME / "adf.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lifecycle (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL,
    generation TEXT NOT NULL,
    reason TEXT NOT NULL,
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS developers (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    owner TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    revision TEXT,
    manifest_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS wake_receipts (
    job_id TEXT PRIMARY KEY,
    generation TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    received_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS operations (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    repository TEXT,
    status TEXT NOT NULL,
    request_json TEXT NOT NULL,
    result_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL
);
"""


def connect(path=DB):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


@contextmanager
def transaction(path=DB):
    connection = connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(path=DB):
    with transaction(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        connection.execute(
            "INSERT OR IGNORE INTO lifecycle(id, mode, generation, reason, state_json, updated_at) "
            "VALUES (1, 'running', 'initial', 'Initial state', '{}', ?)",
            (now(),),
        )
        connection.execute(
            "INSERT OR IGNORE INTO developers(id, owner, updated_at) VALUES (1, NULL, ?)",
            (now(),),
        )
    return path


def lifecycle(connection):
    row = connection.execute(
        "SELECT mode, generation, reason, state_json, updated_at FROM lifecycle WHERE id = 1"
    ).fetchone()
    if row is None:
        return None
    value = json.loads(row["state_json"])
    value.update(mode=row["mode"], generation=row["generation"], reason=row["reason"],
                 updated_at=row["updated_at"])
    return value


def owner(connection):
    row = connection.execute("SELECT owner FROM developers WHERE id = 1").fetchone()
    return row["owner"] if row and row["owner"] else None


def set_lifecycle(connection, state, reason, *, previous=None):
    current = lifecycle(connection)
    if previous is not None and current is not None and current["generation"] != previous:
        raise ValueError("Lifecycle generation changed; recheck state")
    connection.execute(
        "UPDATE lifecycle SET mode=?, generation=?, reason=?, state_json=?, updated_at=? WHERE id=1",
        (state["mode"], state["generation"], state["reason"],
         json.dumps(state, ensure_ascii=False, sort_keys=True), now()),
    )
    connection.execute(
        "INSERT INTO transitions(entity, entity_id, old_value, new_value, reason, created_at) "
        "VALUES ('lifecycle','1',?,?,?,?)",
        (json.dumps(current, ensure_ascii=False, sort_keys=True) if current else None,
         state["mode"], reason, now()),
    )
    return state


def set_owner(connection, owner_id, reason):
    old = owner(connection)
    connection.execute(
        "UPDATE developers SET owner=?, updated_at=? WHERE id=1",
        (owner_id, now()),
    )
    connection.execute(
        "INSERT INTO transitions(entity, entity_id, old_value, new_value, reason, created_at) "
        "VALUES ('developer','1',?,?,?,?)",
        (old, owner_id, reason, now()),
    )


def save_job(connection, manifest):
    connection.execute(
        "INSERT INTO jobs(job_id,status,revision,manifest_json,updated_at) "
        "VALUES(?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET "
        "status=excluded.status, revision=excluded.revision, manifest_json=excluded.manifest_json, "
        "updated_at=excluded.updated_at",
        (manifest["id"], manifest["status"], manifest.get("revision"),
         json.dumps(manifest, ensure_ascii=False, sort_keys=True), now()),
    )


def save_wake_receipt(connection, job_id, generation):
    connection.execute(
        "INSERT OR IGNORE INTO wake_receipts(job_id,generation,receipt_json,received_at) "
        "VALUES(?,?,?,?)",
        (job_id, generation,
         json.dumps({"job": job_id, "generation": generation}, ensure_ascii=False, sort_keys=True),
         now()),
    )


def begin_operation(connection, operation_id, kind, repository, request):
    row = connection.execute("SELECT status,result_json FROM operations WHERE id=?", (operation_id,)).fetchone()
    if row:
        return dict(row)
    connection.execute(
        "INSERT INTO operations(id,kind,repository,status,request_json,created_at,updated_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (operation_id, kind, repository, "intent",
         json.dumps(request, ensure_ascii=False, sort_keys=True), now(), now()),
    )
    return {"status": "intent", "result_json": None}


def finish_operation(connection, operation_id, status, result=None):
    connection.execute(
        "UPDATE operations SET status=?, result_json=?, updated_at=? WHERE id=?",
        (status, json.dumps(result, ensure_ascii=False, sort_keys=True) if result is not None else None,
         now(), operation_id),
    )
