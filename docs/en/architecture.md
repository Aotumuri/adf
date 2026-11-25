# Architecture and extraction

[日本語](../ja/architecture.md) · [Home](../../README.md)

## Source and scope

The read-only isekai-sim reference was clean on 2026-11-25 at
`982560d0e3dc6d598643ee3b4814e74f7fa0aa28`. ADF uses committed blobs from that
revision. The extraction includes Coordinator and Developer Skills, role
instructions, the native Worker role, local and GitHub tracking, ownership and
lifecycle, checkpoints, runner and its acceptance structure, and the applicable
tests. The source tree has no Issue templates for the tracker. The source
migration script changes legacy GitHub classification in place. It and its
dedicated testcase remain in the reference project for its legacy migration.
No source credentials, project identity configuration, task state, research
reports, or experiment outputs are distributed.

## Structure

| Location in downstream | Responsibility |
| --- | --- |
| `.agents/skills/` | Native startup and maintenance Skills. |
| `.codex/agents/adf-worker.toml` | Namespaced optional Worker with model selection inherited from the Codex session or its policy. |
| `agents/tools/` and `agents/docs/` | Lifecycle, tracker, experiments, diagnostics, contribution helper, and their instructions. |
| `agents/config.example.toml` | Managed default policy. The standalone default uses the local tracker and disables auto-resume. |
| `.copier-answers.yml` | Managed installation source and version. |
| `agents/config.toml`, `AGENTS.md`, `.codex/config.toml` | Project-controlled policy and configuration. |
| `agents/research/` and project reports | Project-controlled local tasks, proposal records and reproducible evidence. |
| `agents/runtime/` | Ignored durable lifecycle, ownership, checkpoints, job logs and artifacts. |
| Host-managed configuration and credentials | Effective permissions, tokens, machine-specific CLI selection, and Codex session state. |

ADF creates local research state when it first needs to save a task or review.
The tracker is a project choice. Both research and development can share the
same classification. Codex handles semantic judgments and authorization.
Python tools handle state transitions, locks, receipts, and GitHub operations.
Developer owns the project worktree and jobs. A validated completion wake is
bound to the saved owner, generation, job and receipt.

Extraction changes adapt the project identity, default policy, state bootstrap,
Worker name/model, and role guidance. New ADF functionality adds Copier
packaging, environment inspection, label previews, and selected reverse diffs.
Copier uses plain payload files and renders the answers filename. No Tasks,
Migrations, trust elevation, or service writes are required to render.
IDs, versioned local work, and upstream proposal history remain independently
usable. An experiment can stay local indefinitely.

## Future migration of isekai-sim

At an owner-approved quiet boundary, identify the current source commit and
completed jobs. Back up local state and reports, ignored runtime, and current
configuration using restricted storage. Evaluate a pinned ADF release in a
separate clone. Compare all overlaps, especially the existing roles, agent
policy, GitHub definitions, and notification settings. Preserve the source
repository's GitHub target, current Issues and labels, local research history,
and original lifecycle data. Integrate project-specific instructions into the
existing guidance and review the Worker name and effective policy. Verify
isolated behavior, then approve any live test separately. Integrate a reviewed
migration commit and use its revert plus the saved runtime backup for recovery
if needed.
