"""Re-render the installed ADF baseline and emit a patch for selected paths."""

import argparse
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

import yaml


MANAGED_PREFIXES = (".agents/skills/", ".codex/agents/", "agents/docs/", "agents/tools/")
MANAGED_FILES = {"agents/.gitignore", "agents/config.example.toml"}


def checked_path(value):
    path = PurePosixPath(value)
    if (path.as_posix() != value or path.is_absolute() or ".." in path.parts
            or any(part in {".git", "__pycache__"} or part.startswith(".env") for part in path.parts)
            or not (value in MANAGED_FILES or value.startswith(MANAGED_PREFIXES))):
        raise ValueError(f"Path outside the contribution scope: {value}")
    return Path(value)


def regular_file(root, path):
    for part in (*reversed(path.parents), path):
        if (root / part).is_symlink():
            raise ValueError(f"Symlink in selected path: {path}")
    file = root / path
    if file.exists() and not file.is_file():
        raise ValueError(f"Selected path is not a regular file: {path}")
    return file


def run(cwd, *args, capture=False):
    result = subprocess.run(args, cwd=cwd, check=True, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE if capture else sys.stderr)
    return result.stdout


def render(project, baseline):
    answers = project / ".copier-answers.yml"
    if answers.is_symlink():
        raise ValueError("Expected a regular Copier answers file")
    data = yaml.safe_load(answers.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or any(not isinstance(data.get(key), str) or not data[key]
                                         for key in ("_src_path", "_commit")):
        raise ValueError("Expected Copier's recorded template source and version")
    run(project, sys.executable, "-m", "copier", "copy", "--defaults", "--skip-tasks",
        "--vcs-ref", data["_commit"], "--data-file", str(answers),
        "--", data["_src_path"], str(baseline))


def contribution(project, paths, additions):
    selected = {checked_path(value): False for value in paths}
    for value in additions:
        path = checked_path(value)
        if path in selected:
            raise ValueError(f"Select {path} only once")
        selected[path] = True
    if not selected:
        raise ValueError("Select at least one path to compare")

    with tempfile.TemporaryDirectory(prefix="adf-contribution-") as temporary:
        root = Path(temporary)
        baseline = root / "baseline"
        render(project, baseline)
        workspace = root / "patch"
        workspace.mkdir()
        git = ("git", "-c", "core.autocrlf=false", "-c", "core.filemode=true")
        run(workspace, *git, "init", "--quiet")
        for path, new in selected.items():
            original = regular_file(baseline, path)
            if original.exists() == new:
                raise ValueError(f"Unexpected baseline presence for {path}. Check path selection")
            if not new:
                target = workspace / "template" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target)
        run(workspace, *git, "add", "--force", "--all")
        base = run(workspace, *git, "write-tree", capture=True).decode().strip()

        for path, new in selected.items():
            current = regular_file(project, path)
            target = workspace / "template" / path
            if current.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current, target)
            elif new:
                raise ValueError(f"New contribution file does not exist: {path}")
            else:
                target.unlink()
        run(workspace, *git, "add", "--force", "--all")
        return run(workspace, *git, "diff", "--cached", "--binary", "--no-ext-diff",
                   "--no-textconv", "--no-renames", "--full-index", "--no-color",
                   "--src-prefix=a/", "--dst-prefix=b/", base, "--", capture=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Existing template paths relative to the project root")
    parser.add_argument("--new", action="append", default=[], metavar="PATH", help="Explicitly select a new common file")
    args = parser.parse_args()
    try:
        patch = contribution(Path.cwd(), args.paths, args.new)
        sys.stdout.buffer.write(patch)
    except (OSError, ValueError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
