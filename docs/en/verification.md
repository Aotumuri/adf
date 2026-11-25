# Verification and roadmap

[日本語](../ja/verification.md) · [Home](../../README.md)

## 2026-11-25

| Area | Result |
| --- | --- |
| Reference review and extraction | Success. The source HEAD remained `982560d0e3dc6d598643ee3b4814e74f7fa0aa28` with a clean status at both boundaries. Only committed framework files were used. |
| Core runtime | Success on Python 3.12. The Python suite covers read-only environment diagnostics, the local tracker, competing claims, stop/drain/resume, durable checkpoints, detached jobs, process-group cancellation with SIGKILL escalation, job recovery, fake Queue delivery, generation guards and deduplication. |
| GitHub tracking | Success using the fake transport. Tests cover lifecycle labels, read-only label planning, conflicting descriptions/colors, idempotent setup, approval denial, dependencies, checklist updates and stable mutation keys. Live reads and writes in a designated test repository are unverified. |
| Copier distribution | Success with Copier 9.19.1 on macOS. Disposable repos verified first install, a versioned install at the local `v0.1.0` tag, `check-update`, existing configuration and Issue template preservation, repeated read-only preflight, and repeat updates. |
| Framework changes and rollback | Success locally. Two independent downstream patches applied to the upstream fixture, including a new file and a Skill change. A patch from the `v0.1.0` installation also applied cleanly to a fresh clone of the source repository. Updates retained local edits, tracked configuration and research state, and ignored runtime output. Inline conflict detection, semantic resolution, isolated failed update and revert with later work were exercised. Remote PR creation is unverified. |
| Coordinator and Developer | Success through the local command workflow for intake, claim, review, checkpoint and transfer. Full role execution through interactive model turns and repeated application of the initializer Skill remain unverified. |
| Codex Skills | Success. All four manifests passed the Skill validator. Local app-server `skills/list` detected them using standalone CLI 0.172.0 and bundled CLI 0.171.0-alpha.13.2 from ChatGPT Desktop 26.1120.41243. The first managed invocation failed with a local state/OS permissions error. The approved isolated local retry succeeded. No model turns were started. |
| Worker, live Queue and resume | Unverified. Both CLI variants exposed Queue help. The Skill discovery checkout was untrusted and project-local config was disabled there. Actual Worker spawn, model access, detached Queue delivery and same-thread automatic turns still require live acceptance. |
| Managed Git metadata | Direct writes were denied. Authorized local Git operations used the formal approval mechanism. No publication, push, PR or isekai-sim changes were made. |

Reproduce with `python -m unittest discover -s template/agents/tools/tests`
and `python -m unittest discover -s tests`. Use the Copier interpreter for the
second command. Tests use isolated local repositories and synthetic data. The
`v0.1.0` tag exists only in the local repository; publishing it or any remote
URL is outside the verified scope.
[Copier update behavior](https://copier.readthedocs.io/en/stable/updating/) ·
[Codex Skill discovery](https://learn.chatgpt.com/docs/build-skills)

## Remaining roadmap

1. Run both primary roles and repeat the initializer in an approved disposable
   Codex project. Verify the Worker and actual permissions with the active host.
2. In an explicitly designated GitHub test repository, confirm authenticated
   reads, the approved label and Issue round trip, and a fork/PR workflow with
   authorized destinations. The repository and write scope are owner decisions.
3. Run the time-bounded same-thread notification test from the intended
   standalone Developer environment. Keep auto-resume disabled until the
   target environment accepts it.
4. Decide remote hosting and visibility independently of the local release.
   Plan isekai-sim adoption later using the [migration plan](architecture.md#future-migration-of-isekai-sim).

The extraction kept its original lifecycle implementation. Installation and
updates use Copier with no template Tasks or Migrations. Initialization is a
Skill backed by read-only diagnostics and the existing write-gated tracker.
Update failure recovery uses a separate clone, based on the observed unmerged
index without a Git merge operation. A small custom patch extractor fills
the upstream contribution gap.
