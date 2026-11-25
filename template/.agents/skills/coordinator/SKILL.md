---
name: coordinator
description: Start the Coordinator primary session for human ideas, research plans, and issue management.
---

Start the independent Coordinator role in this thread when the user explicitly invokes this skill.

From the repository root, read `AGENTS.md`, `agents/docs/roles/coordinator.md`, and the project policy `agents/config.toml` (defaults in `agents/config.example.toml`). Check the current session with `python3 agents/tools/inspect_environment.py` and review the relevant [permissions](../../../agents/docs/OPERATIONS.md#permissions-and-acceptance). Confirm effective access before writes and apply the repository policy in addition to host approvals. Run `python3 agents/tools/research.py status` and inspect the configured tracker as needed. Follow the role guide to evaluate proposals and manage issues. Stay available for human input.

Do not claim Developer ownership, implement autonomously, or control the Developer lifecycle. Route shutdown and resumption requests to the Developer thread.

In GitHub mode, put verifiable acceptance and progress items in the opening issue checklist when drafting a proposal. Read the status label, native close state, and checked items to understand current progress. Follow [the tracker guide](../../../agents/docs/tracker.md) for state meanings and GitHub write approval.
