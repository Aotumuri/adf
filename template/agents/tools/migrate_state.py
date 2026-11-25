"""Migrate legacy JSON runtime state into SQLite without destructive writes."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from sqlite_state import DB, initialize, save_job, set_lifecycle, set_owner, transaction
from storage import RUNTIME, read


def backup(directory):
    target = RUNTIME / "migration-backup" / now_stamp()
    target.mkdir(parents=True)
    for path in (RUNTIME / "control.json", RUNTIME / "developer.json",
                 RUNTIME / "github-checkpoint.json", RUNTIME / "github-operations.json"):
        if path.is_file():
            shutil.copy2(path, target / path.name)
    jobs = RUNTIME / "jobs"
    if jobs.is_dir():
        shutil.copytree(jobs, target / "jobs", copy_function=shutil.copy2)
    return target


def now_stamp():
    from storage import now
    return now().replace(":", "").replace("-", "")


def migrate(force=False):
    initialize(DB)
    with transaction(DB) as connection:
        complete = connection.execute(
            "SELECT value FROM meta WHERE key='migration_status'"
        ).fetchone()
        if complete and complete["value"] == "complete" and not force:
            return {"status": "already_complete", "database": str(DB)}
        target = backup(RUNTIME)

        control_path = RUNTIME / "control.json"
        owner_path = RUNTIME / "developer.json"
        if control_path.is_file():
            state = read(control_path)
            if not isinstance(state, dict) or not isinstance(state.get("generation"), str):
                raise ValueError("Invalid legacy lifecycle state")
            set_lifecycle(connection, state, "Legacy JSON migration")
        if owner_path.is_file():
            owner = read(owner_path)
            if not isinstance(owner, dict) or not isinstance(owner.get("id"), str):
                raise ValueError("Invalid legacy Developer owner")
            set_owner(connection, owner["id"], "Legacy JSON migration")

        imported = 0
        for manifest in sorted((RUNTIME / "jobs").glob("*/manifest.json")):
            value = read(manifest)
            if not isinstance(value, dict) or not isinstance(value.get("id"), str):
                raise ValueError(f"Invalid legacy job manifest: {manifest}")
            save_job(connection, value)
            imported += 1

        connection.execute(
            "INSERT INTO meta(key,value) VALUES('migration_status','complete') "
            "ON CONFLICT(key) DO UPDATE SET value='complete'"
        )
        connection.execute(
            "INSERT INTO meta(key,value) VALUES('migration_backup',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(target),),
        )
    return {"status": "complete", "database": str(DB), "backup": str(target),
            "jobs_imported": imported}


def inspect():
    if not DB.exists():
        return {"status": "not_initialized", "database": str(DB)}
    initialize(DB)
    with transaction(DB) as connection:
        status = connection.execute(
            "SELECT value FROM meta WHERE key='migration_status'"
        ).fetchone()
        backup = connection.execute(
            "SELECT value FROM meta WHERE key='migration_backup'"
        ).fetchone()
        jobs = connection.execute("SELECT count(*) AS count FROM jobs").fetchone()["count"]
    return {"status": status["value"] if status else "legacy",
            "database": str(DB), "backup": backup["value"] if backup else None,
            "jobs": jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    action = actions.add_parser("migrate")
    action.add_argument("--force", action="store_true")
    actions.add_parser("inspect")
    args = parser.parse_args()
    try:
        result = inspect() if args.action == "inspect" else migrate(args.force)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
