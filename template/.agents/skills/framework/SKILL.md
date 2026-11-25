---
name: framework
description: Inspect, customize, update, recover, or contribute ADF itself in a downstream project or the upstream template. Use for framework maintenance as distinct from ordinary project work.
---

Treat [the maintenance guide](../../../agents/docs/maintenance.md) as the command reference. Preserve project configuration, tracked research, ignored runtime data and jobs.

If the Git root contains the upstream `copier.yml` and `template/`, work on the
source payload there. Verify changes with the upstream test suites and a fresh
render before tagging. To discover this Skill in that checkout, start Codex from
`template/`. For a deployed checkout follow the operations below.

- **Inspect.** Read Copier's recorded source/ref from `.copier-answers.yml` without modifying it. Inspect current Git changes, installed tools, operating permissions and active jobs/ownership. Review trusted upstream tags and release notes. Reproduce the installed files before comparing local customizations.
- **Modify.** Work directly on installed shared files. Classify changes as reusable improvement, project customization, experiment, or workaround. Verify local behavior and record evidence where useful. Upstream acceptance is independent.
- **Update.** Coordinate with Developer and confirm it has reached a quiet boundary with no live jobs or worktree writes. Keep uncommitted work in the original checkout. Start from an identified clean Git commit in a disposable clone and pin the chosen tag. Check the preview, run Copier there, then inspect Git diff, status, unmerged paths and conflict markers. Resolve semantically, retaining the user's intent and the new behavior as appropriate. Validate with fixtures and project checks. Integrate only the reviewed update commit with the original checkout ready. Confirm the new answers and preserved state.
- **Rollback.** If verification fails, leave the original checkout at its pre-update state and retain the candidate for diagnosis. For a committed update use a reviewed Git revert on a clean branch, preserving later edits and external or ignored state. See the guide for accidental in-place updates.
- **Contribute.** Select explicit shared paths and generate a patch from the recorded baseline using `agents/tools/contribution.py`. Inspect it for project identifiers, private data, credentials and experiment outputs before storing or sharing. Map nonliteral/generated changes into source templates by hand. In a separate upstream checkout apply the patch, reconcile with the current upstream, validate and prepare a focused Conventional Commit and PR description with evidence. Keep the patch and proposal locally if publishing is unavailable. Push or create a PR only after authorization for that destination and operation.
- **Self-update.** Finish this operation using the instructions read at the start. Verify the new Skill and scripts in the candidate checkout, then use the updated instructions on the next invocation.
