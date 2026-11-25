# Core reliability implementation plan

## Findings

The committed implementation uses JSON files for lifecycle, ownership, checkpoints,
job manifests and wake receipts. It preserves behavior across Copier updates, but
generation changes and owner transfers are separate writes, and external operations
are not represented in one durable transaction. The runner has separate supervisor
and notification paths, while GitHub mutations use a JSON journal.

## Adopted design

- Keep TOML, Git-tracked research, logs, artifacts, Copier answers and reports in
  their existing locations.
- Add `agents/runtime/adf.sqlite3` as the runtime state source when initialized.
- Until explicit migration completes, preserve the existing JSON files as the
  compatibility source. The migration is opt-in and re-runnable.
- Store lifecycle, owner, generation, job state, wake receipts and durable external
  operation intents in SQLite. Use short transactions and never hold transactions
  across GitHub or process operations.
- Preserve JSON mirrors only as compatibility artifacts during migration. SQLite
  becomes primary only after migration verification.
- Add a repository adapter boundary around Codex CLI detection and Queue delivery.
  ADF Core must remain usable for local state and jobs when Codex is absent.
- Add explicit GitHub issue transitions and repository-qualified operation identity.

## Migration and recovery

1. Detect JSON legacy state and record its schema.
2. Create a SQLite backup before the first migration.
3. Import lifecycle, owner, job manifests and wake receipts in one transaction.
4. Verify counts and sampled state, then mark migration complete.
5. Re-running migration is idempotent and does not overwrite completed operations.
6. Copier updates do not copy or remove runtime SQLite state.

## Completion criteria

- Concurrent owner/lifecycle changes are serialized and atomic.
- Stale generations cannot change lifecycle or receive wakes.
- Interrupted stop and handoff operations recover from durable state.
- A Supervisor exit leaves the job interrupted or unknown, not succeeded.
- Notification intent and receipt are durable and duplicate delivery is prevented.
- GitHub progress changes reject invalid transitions and repository mismatch.
- SQLite and JSON state migration has success, rollback and re-run tests.
- CI validates Python, SQLite, Copier, templates and Skill manifests.
