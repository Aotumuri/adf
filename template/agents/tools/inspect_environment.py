"""Collect read-only preflight evidence. Permission hints are not write tests."""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

from github_tracker import GitHubTracker
from policy import CONTROL, OWNER, config, control, owner
from runner import capabilities
from storage import ROOT, RUNTIME


def command(*args):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=12)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def github_evidence(repository, settings):
    gh = shutil.which("gh")
    if not gh or not repository:
        return {"status": "unverified", "reason": "gh and an explicit owner/name are required"}
    try:
        tracker = GitHubTracker({**settings, "tracker": {"github": {"repository": repository}}})
    except ValueError as error:
        return {"status": "failure", "reason": str(error)}
    if command(gh, "auth", "status", "--hostname", "github.com") is None:
        return {"status": "unverified", "reason": "gh auth or network check failed"}
    metadata = command(gh, "repo", "view", repository, "--json", "viewerPermission,hasIssuesEnabled")
    if metadata is None:
        return {"status": "unverified", "reason": "repository read or network check failed"}
    try:
        plan = tracker.label_plan()
    except (ValueError, OSError):
        return {"status": "failure", "repository_read": json.loads(metadata),
                "reason": "label listing failed"}
    return {"status": "success", "repository_read": json.loads(metadata), "labels": {
        group: [item["expected"]["name"] if group == "conflicts" else item["name"]
                for item in items] for group, items in plan.items()},
        "issue_and_label_write": "unverified"}


def evidence(repository):
    settings = config()
    git_dir = command("git", "rev-parse", "--absolute-git-dir")
    existing = ["AGENTS.md", ".agents/skills", ".codex/config.toml", ".codex/agents",
                ".github/ISSUE_TEMPLATE", ".github/workflows", "agents/config.toml",
                "agents/research", "agents/runtime"]
    tracker = settings.get("tracker", {})
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "tools": {name: bool(shutil.which(name)) for name in ("git", "gh", "copier", "codex")},
        "codex": capabilities(),
        "files_present": [name for name in existing if (ROOT / name).exists()],
        "access_hints": {"root_readable": os.access(ROOT, os.R_OK),
                         "root_writable": os.access(ROOT, os.W_OK),
                         "git_dir_writable": os.access(git_dir, os.W_OK) if git_dir else None,
                         "git_metadata_read": git_dir is not None,
                         "git_has_head": command("git", "rev-parse", "--verify", "HEAD") is not None},
        "lifecycle": {"mode": control()["mode"], "owner_present": owner() is not None,
                      "control_present": CONTROL.is_file(),
                      "runtime_present": RUNTIME.is_dir(), "owner_record_present": OWNER.is_file()},
        "policy": {"backend": tracker.get("backend", "local"), "git": settings.get("git", {}),
                   "github": {key: value for key, value in tracker.get("github", {}).items()
                              if key in {"create_issue", "create_label", "delete_label", "update_issue",
                                         "comment", "close_issue", "close_on"}},
                   "auto_resume_configured": settings.get("execution", {}).get("auto_resume") is True},
        "github": github_evidence(repository, settings) if repository else {"status": "not_requested"},
        "unverified": ["desktop app version", "sandbox and approval policy", "effective writes",
                       "detached process lifetime", "notification delivery", "automatic resume",
                       "subagent recognition and model access"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github", metavar="OWNER/NAME", help="Probe GitHub using read-only requests")
    args = parser.parse_args()
    try:
        print(json.dumps(evidence(args.github), indent=2))
    except (OSError, ValueError) as error:
        sys.exit(str(error))
