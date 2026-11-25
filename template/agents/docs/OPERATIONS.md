# Operating ADF

[日本語](OPERATIONS.ja.md) · [Framework maintenance](maintenance.md)

## Initialize a project

After Copier completes, open the destination as a Codex project and invoke `$initializer`.
Review its proposed local changes, tracker choice, and approvals. Existing instructions,
CI, Issue templates, and agent settings guide the plan. Python 3.12+, Git, and a POSIX
environment are required for the runtime. GitHub mode also requires `gh`.

`agents/config.example.toml` provides the defaults. Copy it to `agents/config.toml` for
project overrides and review that policy before writes. Select `tracker.backend = "github"`
and set `tracker.github.repository` to the intended `owner/name` to use GitHub as the task
source. Keep credentials in the host's credential manager. Set `CODEX_CLI_PATH` in the
environment when a machine needs a specific standalone CLI.

In GitHub mode inspect current Issues, labels and templates before changing them.
`python3 agents/tools/research.py github label-plan` shows missing, matching, and
conflicting definitions. After approval, `github setup-labels --approved` creates
missing labels and preserves existing ones. Conflicts stop the batch. Agree on a
separate migration if an existing classification or Issue needs modification.
[Tracker commands and semantics](tracker.md)

## Start and recover

Open independent sessions for `$coordinator` and `$developer` in the same checkout.
Coordinator evaluates proposals and manages the tracker. Developer claims a unique
owner ID, recovers the checkpoint and current Git state, implements, verifies, and
commits. Coordinator never starts or wakes Developer. Run the status command in the
intended session to recover current work.

```sh
python3 agents/tools/research.py status
python3 agents/tools/runner.py capabilities
python3 agents/tools/runner.py list
```

State and inbox entries for the local tracker live under `agents/research/` and can
be reviewed for version control. Ownership, the GitHub execution checkpoint, job
logs and artifacts live under ignored `agents/runtime/`; preserve them separately
when moving between machines. Reports belong in project-selected paths outside
template management. Keep private data outside commits. See the
[Developer role](roles/developer.md) for stop, transfer and recovery commands.

For an optional bounded delegation, verify the Codex client recognizes `adf-worker`
and the available model before using it. Follow the current project's agent policy.
A one-worker limit is enforced by the role and can also be set via
`[agents] max_concurrent_threads_per_session = 1` in the project Codex configuration
if compatible with existing agents. Delegation requires authorization and forbids
further delegation. [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## Permissions and acceptance

```sh
python3 agents/tools/inspect_environment.py
python3 agents/tools/inspect_environment.py --github OWNER/NAME
python3 -m unittest discover -s agents/tools/tests
```

The first two commands inspect local capabilities and optional GitHub reads without
creating state. OS access hints are advisory. Repository policy (`allow`, `ask`,
`deny`) supplements the effective sandbox, approval policy, and service permissions.
An authenticated GitHub read and viewer role do not prove label or Issue write access.
Record the actual Desktop version, active sandbox/approval policy, and absent or
blocked capabilities in the current session. Recheck before using each role's
capabilities. For missing access use the host's supported approvals and GitHub
repository permissions. [Codex permissions](https://developers.openai.com/codex/agent-approvals-security)

| Capability | Required access and acceptance evidence |
| --- | --- |
| Coordinator local | Repository and research reads, plus permission to write a local inbox entry if requested. |
| Developer local | Repository, runtime and research writes, plus Git metadata writes for commits. Use disposable Git repositories for verification. |
| GitHub tracker | Network and authenticated repository/Issue reads. Label and Issue changes require both appropriate service permissions and approval under project policy. Verify writes only on an authorized test target. |
| Runner | Local Git archive, runtime writes, and OS process execution. Verify detached completion with a time-bounded harmless command. |
| Notification and resume | Queue support, permitted access to the intended CLI session and app server, and owner consent for a future turn. Verify delivery and turn start separately. |
| Worker | Native subagent recognition, authorized delegation, and model availability. Test using a bounded read-only task if authorized. |

Capture evidence and the next action per check. Use success, failure, unverified,
insufficient permission, environment constraint, or unnecessary. Fixture tests can
verify local lifecycle and simulated GitHub and Queue behavior. For live checks use
the [runner acceptance procedure](runner.md#live-acceptance).
