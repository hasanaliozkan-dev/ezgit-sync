"""Tests for `ezgit-sync` package."""

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

import ezgit_sync
from ezgit_sync.autogit import (
    COLOR_RED,
    _paint,
    get_current_branch,
    has_local_changes,
    pull_remote_changes,
    sync_local_changes,
    verify_git_repository,
)
from ezgit_sync.cli import main

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content)
    git(repo, "add", name)
    git(repo, "commit", "-m", message)


def remote_log(origin: Path, branch: str = "main") -> list[str]:
    return git(origin, "log", "--format=%s", branch).splitlines()


def add_hook(repo: Path, name: str, script: str) -> None:
    hook = repo / ".git" / "hooks" / name
    hook.write_text(f"#!/bin/sh\n{script}\n")
    hook.chmod(0o755)


@pytest.fixture(autouse=True)
def isolated_git(tmp_path, monkeypatch):
    """Keep the user's global git config (signing, hooks, aliases) out of the tests."""
    config = tmp_path / "gitconfig"
    config.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[init]\n\tdefaultBranch = main\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.delenv("NO_COLOR", raising=False)


@pytest.fixture
def repos(tmp_path):
    """A bare `origin` with one commit on main, a working clone, and a second clone acting as a teammate."""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    other = tmp_path / "other"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(work))
    commit_file(work, "README.md", "hello\n", "initial")
    git(work, "push", "-q", "-u", "origin", "main")
    git(tmp_path, "clone", "-q", str(origin), str(other))
    return origin, work, other


def test_import():
    """Verify the package can be imported."""
    assert ezgit_sync.sync_local_changes


# autogit helpers


def test_verify_git_repository_inside_repo(repos):
    _, work, _ = repos
    assert verify_git_repository(work)


def test_verify_git_repository_outside_repo(tmp_path, capsys):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert not verify_git_repository(plain)
    assert "not a valid Git repository" in capsys.readouterr().err


def test_verify_git_repository_when_git_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    assert verify_git_repository(tmp_path) is False


def test_get_current_branch(repos):
    _, work, _ = repos
    assert get_current_branch(work) == "main"


def test_get_current_branch_detached_head_raises(repos):
    _, work, _ = repos
    git(work, "checkout", "-q", "--detach")
    with pytest.raises(RuntimeError):
        get_current_branch(work)


def test_has_local_changes(repos):
    _, work, _ = repos
    assert not has_local_changes(work)
    (work / "README.md").write_text("changed\n")
    assert has_local_changes(work)


def test_has_local_changes_counts_untracked_files(repos):
    _, work, _ = repos
    (work / "new.txt").write_text("x\n")
    assert has_local_changes(work)


def test_pull_remote_changes_brings_in_teammate_commit(repos):
    _, work, other = repos
    commit_file(other, "team.txt", "from teammate\n", "teammate change")
    git(other, "push", "-q")
    assert pull_remote_changes(work, "main")
    assert (work / "team.txt").read_text() == "from teammate\n"


def test_pull_error_message_names_the_branch(repos, capsys):
    _, work, _ = repos
    git(work, "remote", "set-url", "origin", str(work.parent / "missing.git"))
    assert not pull_remote_changes(work, "main")
    err = capsys.readouterr().err
    assert "{branch}" not in err
    assert "origin/main" in err


def test_pull_skips_branch_missing_on_origin(repos):
    _, work, _ = repos
    assert pull_remote_changes(work, "feature-x")


def test_paint_keeps_colors_on_a_terminal():
    class Terminal(io.StringIO):
        def isatty(self):
            return True

    assert _paint("x", COLOR_RED, stream=Terminal()) == f"{COLOR_RED}x\033[0m"


def test_sync_local_changes_commits_and_pushes(repos):
    origin, work, _ = repos
    (work / "data.csv").write_text("a,b\n")
    sync_local_changes(work, "main", "add data")
    assert remote_log(origin)[0] == "add data"


# CLI


def test_cli_full_sync(repos, monkeypatch):
    origin, work, _ = repos
    monkeypatch.chdir(work)
    (work / "model.py").write_text("print('train')\n")
    assert main(["-m", "train script"]) == 0
    assert remote_log(origin)[0] == "train script"


def test_cli_default_message_matches_readme(repos, monkeypatch):
    origin, work, _ = repos
    monkeypatch.chdir(work)
    (work / "model.py").write_text("x = 1\n")
    assert main([]) == 0
    assert remote_log(origin)[0] == "Auto-sync via ezgit-sync"


def test_cli_nothing_to_do(repos, monkeypatch, capsys):
    _, work, _ = repos
    monkeypatch.chdir(work)
    assert main([]) == 0
    assert "No new local changes" in capsys.readouterr().out


def test_cli_not_a_repo(tmp_path, monkeypatch):
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)
    assert main([]) == 1


def test_cli_works_from_subdirectory(repos, monkeypatch):
    origin, work, _ = repos
    sub = work / "notebooks"
    sub.mkdir()
    (sub / "eda.py").write_text("import pandas\n")
    monkeypatch.chdir(sub)
    assert main(["-m", "from subdir"]) == 0
    assert remote_log(origin)[0] == "from subdir"


def test_cli_pushes_unpushed_commits_when_tree_is_clean(repos, monkeypatch):
    origin, work, _ = repos
    commit_file(work, "local.txt", "x\n", "committed but never pushed")
    monkeypatch.chdir(work)
    assert main([]) == 0
    assert remote_log(origin)[0] == "committed but never pushed"


def test_cli_retry_after_failed_push_pushes_the_commit(repos, monkeypatch):
    origin, work, _ = repos
    monkeypatch.chdir(work)
    (work / "weights.txt").write_text("v1\n")
    add_hook(work, "pre-push", "exit 1")
    assert main(["-m", "weights v1"]) == 1
    (work / ".git" / "hooks" / "pre-push").unlink()
    assert main(["-m", "retry"]) == 0
    assert "weights v1" in remote_log(origin)


def test_cli_push_failure_is_reported_once(repos, monkeypatch, capsys):
    _, work, _ = repos
    monkeypatch.chdir(work)
    (work / "weights.txt").write_text("v1\n")
    add_hook(work, "pre-push", "exit 1")
    assert main([]) == 1
    assert capsys.readouterr().err.count("[ERROR]") == 1


def test_cli_commit_failure_shows_git_output(repos, monkeypatch, capsys):
    _, work, _ = repos
    monkeypatch.chdir(work)
    (work / "notes.txt").write_text("x\n")
    add_hook(work, "pre-commit", "echo 'pre-commit hook rejected this' >&2; exit 1")
    assert main([]) == 1
    assert "pre-commit hook rejected this" in capsys.readouterr().err


def test_cli_first_sync_of_new_local_branch(repos, monkeypatch):
    origin, work, _ = repos
    git(work, "checkout", "-q", "-b", "experiment")
    (work / "exp.py").write_text("lr = 0.1\n")
    monkeypatch.chdir(work)
    assert main(["-m", "start experiment"]) == 0
    assert remote_log(origin, "experiment")[0] == "start experiment"


def test_cli_local_edit_and_teammate_edit_to_same_file(repos, monkeypatch):
    origin, work, other = repos
    commit_file(work, "train.py", "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n", "train script")
    git(work, "push", "-q")
    git(other, "pull", "-q")
    # Teammate edits the first line and pushes, we edit the last line without committing
    commit_file(other, "train.py", "a = 10\nb = 2\nc = 3\nd = 4\ne = 5\n", "teammate tweak")
    git(other, "push", "-q")
    (work / "train.py").write_text("a = 1\nb = 2\nc = 3\nd = 4\ne = 50\n")
    monkeypatch.chdir(work)
    assert main(["-m", "my tweak"]) == 0
    git(other, "pull", "-q")
    assert (other / "train.py").read_text() == "a = 10\nb = 2\nc = 3\nd = 4\ne = 50\n"


def test_cli_conflict_aborts_rebase_and_keeps_local_commit(repos, monkeypatch, capsys):
    _, work, other = repos
    commit_file(other, "README.md", "theirs\n", "teammate rewrite")
    git(other, "push", "-q")
    (work / "README.md").write_text("mine\n")
    monkeypatch.chdir(work)
    assert main(["-m", "my rewrite"]) == 1
    assert "conflict" in capsys.readouterr().err
    assert git(work, "log", "-1", "--format=%s") == "my rewrite"
    assert git(work, "status", "--porcelain") == ""
    assert not Path(work, git(work, "rev-parse", "--git-path", "rebase-merge")).exists()


def test_cli_diverged_branch(repos, monkeypatch):
    origin, work, other = repos
    commit_file(work, "mine.txt", "x\n", "my unpushed commit")
    commit_file(other, "theirs.txt", "y\n", "teammate commit")
    git(other, "push", "-q")
    monkeypatch.chdir(work)
    assert main([]) == 0
    log = remote_log(origin)
    assert "my unpushed commit" in log and "teammate commit" in log


def test_no_color_env_disables_ansi_codes(repos, monkeypatch, capsys):
    _, work, _ = repos
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.chdir(work)
    main([])
    captured = capsys.readouterr()
    assert "\033[" not in captured.out + captured.err


def test_python_dash_m_returns_failure_exit_code(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(SRC_DIR), os.environ.get("PYTHONPATH")]))}
    result = subprocess.run([sys.executable, "-m", "ezgit_sync"], cwd=plain, capture_output=True, text=True, env=env)
    assert result.returncode == 1
