import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tools = self.root / "agents/tools"
        self.tools.mkdir(parents=True)
        self.research = self.root / "agents/research"
        self.research.mkdir()
        for path in TOOLS.glob("*.py"):
            shutil.copy(path, self.tools / path.name)
        settings = (TOOLS.parent / "config.example.toml").read_text()
        (self.tools.parent / "config.toml").write_text(
            settings.replace('backend = "github"', 'backend = "local"'))
        (self.research / "state.json").write_text(
            json.dumps({"version": 1, "tasks": {}, "reviews": {}}))
        self.git("init", "-q")
        (self.root / "source.txt").write_text("committed")
        self.git("add", "source.txt")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "Fixture")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True)

    def inspect(self):
        result = subprocess.run(
            [sys.executable, str(self.tools / "inspect_environment.py")],
            cwd=self.root, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_reports_local_evidence_without_creating_state(self):
        before = sorted(path.relative_to(self.root).as_posix()
                        for path in self.root.rglob("*") if path.is_file())
        report = self.inspect()
        self.assertEqual(report["policy"]["backend"], "local")
        self.assertEqual(report["policy"]["git"]["commit"], "allow")
        self.assertFalse(report["policy"]["auto_resume_configured"])
        self.assertEqual(report["github"], {"status": "not_requested"})
        self.assertTrue(report["access_hints"]["root_writable"])
        self.assertTrue(report["access_hints"]["git_has_head"])
        self.assertIn("agents/config.toml", report["files_present"])
        self.assertFalse(report["lifecycle"]["runtime_present"])
        self.assertFalse(report["lifecycle"]["owner_present"])
        self.assertIn("effective writes", report["unverified"])
        self.assertIsInstance(report["codex"]["codex"], list)
        after = sorted(path.relative_to(self.root).as_posix()
                       for path in self.root.rglob("*") if path.is_file())
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
