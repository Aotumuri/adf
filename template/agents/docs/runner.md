# Experiment runner

[日本語](runner.ja.md) · [Operations](OPERATIONS.md)

```sh
python3 agents/tools/runner.py start probe-1 --timeout 90 -- python3 -c 'print("ok")'
python3 agents/tools/runner.py list
python3 agents/tools/runner.py status probe-1
python3 agents/tools/runner.py cancel probe-1
python3 agents/tools/runner.py recover probe-1
```

Use a fresh job ID for each run. Jobs use a Git archive of the committed revision
(`--revision` defaults to HEAD). The runner stores the manifest, experiment and
supervisor logs, and an artifacts directory exposed as `EXPERIMENT_ARTIFACTS`.
A POSIX detached supervisor manages timeouts and process-group cancellation.
Optional CPU and per-file limits are available; host lifetime, memory and overall
disk usage are host constraints. Use `recover --relaunch-queued` only for a job
known to have stopped while queued. Never expose secrets in `--env` or command
arguments recorded in the manifest. `--reuse-node-modules` is optional and requires
the same lockfile as the existing dependencies.

Notification defaults to off. `runner.py capabilities` checks executable help.
`CODEX_CLI_PATH` overrides CLI discovery. Otherwise ADF tries the project-configured
path, PATH, and the Desktop runtime. Queue support is a prerequisite. A delivery
marked `accepted` indicates a successful CLI exit. Actual session delivery
and new turn start require separate evidence. Persisted results survive delivery
failure. Automatic wake must pass the notification's `validate-wake` command,
which checks the current owner, generation, job, and receipt. Graceful stop limits
an eligible wake to finishing shutdown. A paused session needs explicit resume.

## Live acceptance

1. Use an authorized standalone Developer session and disposable project checkout.
   Check repository policy, Git state, CLI help, and current owner. Limit the
   probe's duration and obtain authorization for a future turn.
2. Record the tracked task, pinned revision, unique job ID, next verification step,
   and thread ID. In the actual owner session start a harmless job, e.g.
   `runner.py start ID --timeout 60 --notify-thread THREAD --acceptance-probe -- sh -c 'sleep 20 && echo ADF_ACCEPTANCE_COMPLETED'`.
   The probe requires a positive timeout and owner match. Record the job in the
   checkpoint, then end the first turn.
3. Observe whether the same thread starts a new turn without human input. Run the
   notification's wake validation first, then confirm the exit code, marker,
   ordering, scope, and absence of duplicate processing. Update any Issue only
   within the approved scope.
4. If Queue does not reach the thread, inspect the manifest and notification log.
   Record the environment error or missing permission. Recover from the checkpoint
   on explicit resume. Leave `execution.auto_resume` disabled until live accepted.
