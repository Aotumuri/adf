import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite_state
import migrate_state


class SQLiteStateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "runtime" / "adf.sqlite3"

    def test_initialize_is_idempotent_and_schema_is_current(self):
        sqlite_state.initialize(self.db)
        sqlite_state.initialize(self.db)
        with sqlite3.connect(self.db) as connection:
            version = connection.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            ).fetchone()[0]
            lifecycle = connection.execute(
                "SELECT mode,generation FROM lifecycle WHERE id=1"
            ).fetchone()
        self.assertEqual(version, "1")
        self.assertEqual(lifecycle, ("running", "initial"))

    def test_lifecycle_and_owner_changes_are_transactional(self):
        sqlite_state.initialize(self.db)
        with sqlite_state.transaction(self.db) as connection:
            state = {
                "mode": "stopping",
                "generation": "generation-1",
                "reason": "Test stop",
                "jobs": ["job-1"],
            }
            sqlite_state.set_lifecycle(connection, state, "Stop")
            sqlite_state.set_owner(connection, "developer-a", "Claim")

        with sqlite_state.transaction(self.db) as connection:
            self.assertEqual(sqlite_state.lifecycle(connection)["generation"], "generation-1")
            self.assertEqual(sqlite_state.owner(connection), "developer-a")

        with sqlite_state.transaction(self.db) as connection:
            with self.assertRaisesRegex(ValueError, "generation changed"):
                sqlite_state.set_lifecycle(
                    connection,
                    {"mode": "running", "generation": "generation-2", "reason": "Resume"},
                    "Resume",
                    previous="stale-generation",
                )

    def test_legacy_migration_backup_and_repeat_are_safe(self):
        root = Path(self.temp.name)
        runtime = root / "runtime"
        jobs = runtime / "jobs" / "fixture"
        jobs.mkdir(parents=True)
        (runtime / "control.json").write_text(json.dumps({
            "mode": "running",
            "generation": "legacy",
            "reason": "Legacy",
        }))
        (runtime / "developer.json").write_text(json.dumps({"id": "fixture-owner"}))
        manifest = {
            "id": "fixture",
            "status": "succeeded",
            "revision": "HEAD",
            "notification": {"status": "disabled"},
        }
        (jobs / "manifest.json").write_text(json.dumps(manifest))

        patches = (
            patch.object(migrate_state, "RUNTIME", runtime),
            patch.object(migrate_state, "DB", runtime / "adf.sqlite3"),
        )
        for change in patches:
            change.start()
            self.addCleanup(change.stop)

        first = migrate_state.migrate()
        second = migrate_state.migrate()
        self.assertEqual(first["status"], "complete")
        self.assertEqual(first["jobs_imported"], 1)
        self.assertEqual(second["status"], "already_complete")
        self.assertTrue(Path(first["backup"]).is_dir())
        with sqlite3.connect(first["database"]) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM jobs"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT owner FROM developers WHERE id=1"
            ).fetchone()[0], "fixture-owner")


if __name__ == "__main__":
    unittest.main()
