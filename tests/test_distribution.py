"""Integration tests using Copier and isolated local Git repositories."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
ANSWERS = ".copier-answers.yml"
FRAMEWORK = ".agents/skills/framework/SKILL.md"
WORKER = ".codex/agents/adf-worker.toml"
OPERATIONS = "agents/docs/OPERATIONS.md"


class DistributionTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="adf-distribution-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.upstream = self.root / "upstream"
        shutil.copytree(ROOT / "template", self.upstream / "template",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "copier.yml", self.upstream)
        self.init(self.upstream)
        self.commit(self.upstream, "Fixture upstream")
        self.git(self.upstream, "tag", "v0.1.0")

    def run_command(self, cwd, *args, check=True):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=45)
        if check:
            self.assertEqual(result.returncode, 0, f"{args}\n{result.stdout}\n{result.stderr}")
        return result

    def git(self, cwd, *args, check=True):
        return self.run_command(cwd, "git", *args, check=check).stdout

    def init(self, path):
        path.mkdir(exist_ok=True)
        self.git(path, "init", "--quiet", "--initial-branch=main")
        self.git(path, "config", "user.name", "ADF Fixture")
        self.git(path, "config", "user.email", "adf@example.invalid")
        self.git(path, "config", "commit.gpgsign", "false")

    def commit(self, path, message):
        self.git(path, "add", "--all")
        self.git(path, "commit", "--quiet", "-m", message)
        return self.git(path, "rev-parse", "HEAD").strip()

    def copier(self, path, *args, check=True):
        return self.run_command(path, sys.executable, "-m", "copier", *args, check=check)

    def answers(self, path):
        return yaml.safe_load((path / ANSWERS).read_text())

    def write(self, path, relative, content):
        file = path / relative
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_text(content, encoding="utf-8")

    def install(self, name, existing=None):
        project = self.root / name
        self.init(project)
        if existing:
            for path, contents in existing.items():
                self.write(project, path, contents)
            self.commit(project, "Existing project")
        self.copier(project, "copy", "--defaults", str(self.upstream), ".")
        self.assertEqual(self.answers(project), {"_commit": "v0.1.0", "_src_path": str(self.upstream)})
        self.commit(project, "Install ADF")
        return project

    def contribute(self, project, patch_name, *paths):
        result = self.run_command(project, sys.executable, "agents/tools/contribution.py", *paths)
        self.assertIn("diff --git a/template/", result.stdout)
        patch = self.root / patch_name
        patch.write_text(result.stdout, encoding="utf-8")
        self.git(self.upstream, "apply", "--check", str(patch))
        self.git(self.upstream, "apply", "--3way", str(patch))
        self.commit(self.upstream, patch_name)

    def test_local_roles_bootstrap_and_preserve_checkpoint(self):
        project = self.install("local")
        task = ("agents/tools/research.py",)
        state_path = project / "agents/research/state.json"
        self.assertFalse(state_path.exists())

        def research(*args, proposal=None, check=True):
            if proposal is None:
                return self.run_command(project, sys.executable, *task, *args, check=check)
            result = subprocess.run([sys.executable, *task, *args], cwd=project,
                                    input=proposal, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result

        idea = research("submit", "Local proposal", "--assessment", "ready",
                        proposal="Add a targeted verification.").stdout.strip()
        status = json.loads(research("status").stdout)
        self.assertIsNone(status["owner"])
        self.assertEqual(status["unreviewed"][0]["id"], idea)
        self.assertFalse(state_path.exists())
        research("claim", "developer")
        race = research("claim", "other-session", check=False)
        self.assertNotEqual(race.returncode, 0)
        research("review", "developer", idea, "ready", "Criteria agreed")
        research("checkpoint", "developer", idea, "active", "Run the targeted verification")
        saved = state_path.read_bytes()
        research("release", "developer")
        research("claim", "next-session")
        self.assertEqual(state_path.read_bytes(), saved)
        restored = json.loads(research("status").stdout)
        self.assertEqual(restored["tasks"][idea]["next"], "Run the targeted verification")

    def test_distributed_changes_and_safe_updates(self):
        new = self.install("new")
        self.assertFalse((new / "agents/runtime").exists())
        self.assertFalse((new / "agents/config.toml").exists())
        preserved = {
            "AGENTS.md": "Project rules\n",
            ".codex/config.toml": "[agents]\nmax_concurrent_threads_per_session = 2\n",
            ".github/ISSUE_TEMPLATE/task.md": "Project checklist\n",
            "agents/config.toml": "[git]\ncommit = 'deny'\n[tracker]\nbackend = 'local'\n",
            "agents/research/state.json": '{"version":1,"tasks":{},"reviews":{}}',
        }
        project = self.install("existing", preserved)
        self.write(project, "agents/runtime/preserved.json", '{"checkpoint": "fixture"}')
        for _ in range(2):
            probe = self.run_command(project, sys.executable, "agents/tools/inspect_environment.py")
            self.assertEqual(json.loads(probe.stdout)["policy"]["git"]["commit"], "deny")
            self.assertEqual(self.git(project, "status", "--porcelain"), "")
        denied = self.run_command(project, sys.executable, "agents/tools/control.py",
                                  "permission", "git", "commit", check=False)
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("denied", denied.stderr)
        self.copier(project, "update", "--defaults")
        self.assertEqual(self.git(project, "status", "--porcelain"), "")

        with (new / FRAMEWORK).open("a") as file:
            file.write("\nRead the release summary at each update.\n")
        self.write(new, "agents/docs/delta.md", "Extra shared documentation\n")
        self.contribute(new, "framework.patch", FRAMEWORK, "--new", "agents/docs/delta.md")
        with (project / WORKER).open("a") as file:
            file.write("\n# Keep the delegated revision available for review.\n")
        self.contribute(project, "worker.patch", WORKER)
        old = (project / OPERATIONS).read_text()
        line = "# Operating ADF"
        self.write(self.upstream, "template/" + OPERATIONS,
                   old.replace(line, "# Operating the shared framework"))
        self.commit(self.upstream, "Upstream operations change")
        self.git(self.upstream, "tag", "v0.2.0")

        # Keep an independent downstream edit and force an overlap in the other project.
        with (project / OPERATIONS).open("a") as file:
            file.write("\nProject operations note.\n")
        baseline = self.commit(project, "Project operations note and accepted worker change")
        self.copier(project, "update", "--pretend", "--defaults", "--vcs-ref", "v0.2.0")
        self.assertEqual(self.git(project, "status", "--porcelain"), "")
        self.copier(project, "update", "--defaults", "--conflict", "inline")
        self.assertEqual(self.answers(project)["_commit"], "v0.2.0")
        self.assertIn("Project operations note.", (project / OPERATIONS).read_text())
        self.assertIn("# Operating the shared framework", (project / OPERATIONS).read_text())
        self.assertIn("release summary", (project / FRAMEWORK).read_text())
        self.assertTrue((project / "agents/docs/delta.md").is_file())
        for path, contents in preserved.items():
            self.assertEqual((project / path).read_text(), contents)
        self.assertEqual((project / "agents/runtime/preserved.json").read_text(),
                         '{"checkpoint": "fixture"}')
        self.assertEqual(self.git(project, "ls-files", "--unmerged"), "")
        self.git(project, "diff", "--check")
        update = self.commit(project, "Verified update")
        self.assertNotEqual(update, baseline)
        self.copier(project, "update", "--defaults")
        self.assertEqual(self.git(project, "status", "--porcelain"), "")

        self.write(new, OPERATIONS, old.replace(line, "# Local operation"))
        original = self.commit(new, "Local conflicting preferences")
        candidate = self.root / "candidate"
        self.git(self.root, "clone", "--quiet", "--no-hardlinks", str(new), str(candidate))
        invalid = self.copier(candidate, "update", "--defaults", "--vcs-ref", "not-a-tag", check=False)
        self.assertNotEqual(invalid.returncode, 0)
        self.copier(candidate, "update", "--defaults", "--conflict", "inline", check=False)
        conflict = (candidate / OPERATIONS).read_text()
        self.assertIn("<<<<<<<", conflict)
        self.assertTrue(self.git(candidate, "ls-files", "--unmerged"))
        self.assertEqual(self.git(new, "rev-parse", "HEAD").strip(), original)
        self.assertEqual(self.git(new, "status", "--porcelain"), "")
        self.assertEqual(self.answers(new)["_commit"], "v0.1.0")
        self.write(candidate, OPERATIONS, old.replace(line, "# Operating the local shared framework"))
        self.git(candidate, "add", "--", OPERATIONS)
        self.assertEqual(self.git(candidate, "ls-files", "--unmerged"), "")
        self.git(candidate, "diff", "--cached", "--check")
        self.git(candidate, "config", "user.name", "ADF Fixture")
        self.git(candidate, "config", "user.email", "adf@example.invalid")
        self.git(candidate, "config", "commit.gpgsign", "false")
        resolved = self.commit(candidate, "Resolve template conflict")
        self.git(new, "fetch", str(candidate), resolved)
        self.git(new, "cherry-pick", resolved)
        self.assertEqual(self.answers(new)["_commit"], "v0.2.0")
        self.assertIn("local shared framework", (new / OPERATIONS).read_text())
        self.write(new, "independent.txt", "Work done after updating")
        self.commit(new, "Independent later work")
        self.write(new, "agents/runtime/result.txt", "Durable result")
        self.git(new, "revert", "--no-edit", resolved)
        self.assertEqual(self.answers(new)["_commit"], "v0.1.0")
        self.assertEqual((new / "independent.txt").read_text(), "Work done after updating")
        self.assertEqual((new / "agents/runtime/result.txt").read_text(), "Durable result")
        self.assertEqual((new / OPERATIONS).read_text(), old.replace(line, "# Local operation"))


if __name__ == "__main__":
    unittest.main()
