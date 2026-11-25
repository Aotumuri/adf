# Autonomous Development Framework

[日本語](README.ja.md)

ADF provides a shared research and development workflow for Codex projects.
It combines independent Coordinator and Developer sessions, local or GitHub
task tracking, persistent checkpoints, and bounded background experiments.

## Install

Use Git, Python 3.12 or later, and Copier 9.19.1 or later on a POSIX system.
Prepare a Git repository, then run the following from its root. For an
existing project, use a clean starting commit and review file collisions
before installation.

```sh
copier copy --pretend /absolute/path/to/adf .
copier copy /absolute/path/to/adf .
```

Use an authorized versioned Git URL in place of the local path when available.
Review and commit the installation and its answers. Open the destination in
Codex and run `$initializer`. Invoke `$coordinator` or `$developer` in separate
sessions. Use `$framework` for ADF changes, updates and upstream contributions.

## Guides

- [Architecture, provenance and migration](docs/en/architecture.md)
- [Initialization, operation and permissions](template/agents/docs/OPERATIONS.md)
- [GitHub Issues and labels](template/agents/docs/tracker.md)
- [Background experiments and notification troubleshooting](template/agents/docs/runner.md)
- [Installation, updating, recovery and contributing](template/agents/docs/maintenance.md)
- [Verification and remaining work](docs/en/verification.md)
- [Release notes](docs/en/releases.md)

## Verify locally

```sh
python -m unittest discover -s template/agents/tools/tests
python -m unittest discover -s tests
```

The distribution suite uses the Python interpreter with Copier installed.
It creates isolated local Git repositories with synthetic data and tags.
