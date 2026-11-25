"""Runtime-neutral boundary for agent-runtime integrations."""

import os
import shutil
import subprocess


class RuntimeAdapter:
    def __init__(self, environment=None, settings=None):
        self.environment = os.environ if environment is None else environment
        self.settings = settings or {}

    def probe(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return result.stdout if result.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            return ""

    def cli_candidates(self):
        override = self.environment.get("CODEX_CLI_PATH")
        configured = self.settings.get("execution", {}).get("codex_cli_path")
        candidates = (override,) if override else (
            configured,
            "codex",
            self.environment.get("CODEX_APP_RUNTIME_CLI_PATH"),
        )
        paths = {}
        for candidate in filter(None, candidates):
            executable = shutil.which(
                os.path.expanduser(candidate),
                path=self.environment.get("PATH"),
            )
            if executable:
                paths[os.path.abspath(executable)] = None
        return list(paths)

    def supports_queue(self, cli):
        help_text = self.probe([cli, "help", "queue"])
        return "Queue a message for an existing session" in help_text and all(
            flag in help_text for flag in ("--thread", "--message", "--resume")
        )

    def capabilities(self):
        cli = [{
            "path": path,
            "version": self.probe([path, "--version"]).strip(),
            "queue": self.supports_queue(path),
            "resume": "SESSION_ID" in self.probe([path, "exec", "resume", "--help"]),
            "app_server": "--listen" in self.probe([path, "app-server", "--help"]),
        } for path in self.cli_candidates()]
        return {
            "codex": cli,
            "notification_cli": next((entry["path"] for entry in cli if entry["queue"]), None),
            "thread_hint_present": bool(self.environment.get("CODEX_THREAD_ID")),
            "desktop_runtime_present": bool(self.environment.get("CODEX_APP_RUNTIME_CLI_PATH")),
            "tmux": bool(shutil.which("tmux", path=self.environment.get("PATH"))),
            "background_method": "POSIX detached supervisor; host lifetime must be tested",
        }

    def queue(self, cli, thread, message, cwd, log):
        return subprocess.Popen(
            [cli, "queue", "--resume", "--thread", thread, "--message", message],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
