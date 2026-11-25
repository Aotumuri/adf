---
name: developer
description: Start or explicitly resume the Developer primary session with the saved research checkpoint.
---

Start the independent Developer role in this thread when the user explicitly invokes this skill.

From the repository root, read `AGENTS.md`, `agents/docs/roles/developer.md`, and the project policy `agents/config.toml` (defaults in `agents/config.example.toml`). Check the current session with `python3 agents/tools/inspect_environment.py` and review the relevant [permissions](../../../agents/docs/OPERATIONS.md#permissions-and-acceptance). Confirm effective access before writes and apply the repository policy in addition to host approvals. Inspect `python3 agents/tools/research.py status` and recover the relevant Git, tracker, and job context using the role guide.

- A bare invocation does not lift a stop or take another thread's ownership. In a running lifecycle, establish the current thread's own ownership with the existing claim command before doing work. Stop if the claim fails.
- On an explicit resume request, follow the role guide's recovery and resume procedure. Transfer ownership only after confirming that the previous Developer has ended. Continue the recovered work within its authorized scope.
- Handle direct shutdown requests using the role guide. Treat wake notifications as events subject to the existing wake guard.
- In GitHub mode, follow [the tracker guide](../../../agents/docs/tracker.md) to synchronize the opening issue checklist and status label at implementation start, experiment launch, verification after resumption, and completion. Check each item once its evidence is available. Keep an active job marked `status:experimenting` when ending the turn to wait for it. Use `github candidates` to review dependency-aware candidates after recovering any existing work. Follow the configured GitHub write policy. Obtain explicit approval for operations configured as `ask`.
