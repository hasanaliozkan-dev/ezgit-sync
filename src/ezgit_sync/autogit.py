"""Main module for ezgit-sync."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TextIO

# ANSI Escape Sequences for Terminal Styling
COLOR_RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"


def _paint(text: str, *codes: str, stream: TextIO) -> str:
    """Wraps text in ANSI codes unless the stream is not a terminal or NO_COLOR is set."""
    if os.environ.get("NO_COLOR") or not stream.isatty():
        return text
    return f"{''.join(codes)}{text}{COLOR_RESET}"


def log_success(message: str) -> None:
    """Prints a styled success message."""
    print(f"{_paint('[SUCCESS]', COLOR_GREEN, BOLD, stream=sys.stdout)} {message}")


def log_warning(message: str) -> None:
    """Prints a styled warning message."""
    print(f"{_paint('[WARNING]', COLOR_YELLOW, BOLD, stream=sys.stdout)} {message}")


def log_info(message: str) -> None:
    """Prints a styled info message."""
    print(f"{_paint('[INFO]', COLOR_CYAN, BOLD, stream=sys.stdout)} {message}")


def log_error_with_reasons(title: str, reasons: list[str], raw_error: str | None = None) -> None:
    """Formats and prints error explanations with probable causes and solutions."""
    err = sys.stderr
    err.write(f"\n{_paint(f'[ERROR] {title}', COLOR_RED, BOLD, stream=err)}\n")
    err.write(f"{_paint('Possible Reasons & Solutions:', BOLD, stream=err)}\n")
    for reason in reasons:
        err.write(f"  • {reason}\n")

    if raw_error and raw_error.strip():
        details = "Raw Git Error Details:\n" + raw_error.strip()
        err.write(f"\n{_paint(details, DIM, stream=err)}\n")
    err.write("\n")


def _git_error_output(exc: subprocess.CalledProcessError) -> str:
    """Git and its hooks report failures on either stream, so keep both."""
    return "\n".join(part.strip() for part in (exc.stderr, exc.stdout) if part and part.strip())


def run_git(args: list[str], repo_root: Path) -> str:
    """Executes a git command and returns its stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_git_repository(repo_root: Path) -> bool:
    """Checks if the current working directory is inside a valid Git repository."""
    try:
        run_git(["rev-parse", "--is-inside-work-tree"], repo_root)
        return True
    except FileNotFoundError:
        log_error_with_reasons(
            title="Git is not installed or not on your PATH.",
            reasons=["Install Git from https://git-scm.com/downloads, then open a new terminal."],
        )
        return False
    except subprocess.CalledProcessError:
        log_error_with_reasons(
            title=f"The directory '{repo_root.name}' is not a valid Git repository.",
            reasons=[
                "Git is not initialized in this directory. Run 'git init' to create a new repository.",
                "You might be running the command in the wrong folder. Navigate to your project root.",
            ],
        )
        return False


def get_current_branch(repo_root: Path) -> str:
    """Retrieves the name of the currently active branch."""
    try:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
        if branch == "HEAD":
            raise RuntimeError("DETACHED_HEAD")
        return branch
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        raw_err = _git_error_output(exc) if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        log_error_with_reasons(
            title="Failed to determine active Git branch.",
            reasons=[
                "This repository might be completely empty (no commits yet). "
                "Create an initial commit first: 'git add . && git commit -m \"initial commit\"'",
                "Your repository might be in a 'detached HEAD' state. "
                "Switch to a branch using 'git checkout <branch-name>'.",
            ],
            raw_error=raw_err,
        )
        raise


def has_local_changes(repo_root: Path) -> bool:
    """Checks if there are uncommitted local modifications, including untracked files."""
    try:
        return bool(run_git(["status", "--porcelain"], repo_root))
    except subprocess.CalledProcessError as exc:
        log_error_with_reasons(
            title="Failed to read the repository status.",
            reasons=["Another Git process may be running (.git/index.lock exists). Wait for it to finish."],
            raw_error=_git_error_output(exc),
        )
        raise


def has_unpushed_commits(repo_root: Path) -> bool:
    """Checks whether HEAD has commits that no branch on origin contains yet."""
    try:
        return run_git(["rev-list", "--count", "HEAD", "--not", "--remotes=origin"], repo_root) != "0"
    except subprocess.CalledProcessError as exc:
        log_error_with_reasons(
            title="Failed to compare local commits with origin.",
            reasons=["The repository history may be damaged. Run 'git fsck' to check it."],
            raw_error=_git_error_output(exc),
        )
        raise


def commit_local_changes(repo_root: Path, commit_message: str) -> None:
    """Stages every change (git add -A) and commits it."""
    log_info("Staging and committing local changes...")
    try:
        run_git(["add", "-A"], repo_root)
        run_git(["commit", "-m", commit_message], repo_root)
    except subprocess.CalledProcessError as exc:
        log_error_with_reasons(
            title="Failed to commit local changes.",
            reasons=[
                "A pre-commit hook rejected the commit. Fix what it reports and run again.",
                "Your Git identity is not set. Run 'git config --global user.name \"Your Name\"' "
                "and 'git config --global user.email you@example.com'.",
                "Another Git process may be running (.git/index.lock exists). Wait for it to finish.",
            ],
            raw_error=_git_error_output(exc),
        )
        raise


def pull_remote_changes(repo_root: Path, branch: str) -> bool:
    """Rebases local commits onto origin/<branch>. A branch missing on origin is left for push to create."""
    try:
        if not run_git(["ls-remote", "--heads", "origin", f"refs/heads/{branch}"], repo_root):
            log_info(f"origin/{branch} does not exist yet, it will be created on push.")
            return True
        log_info(f"Pulling latest updates from origin/{branch}...")
        run_git(["pull", "--rebase", "origin", branch], repo_root)
        return True
    except subprocess.CalledProcessError as exc:
        # A conflicting rebase stops halfway; abort it so the repo is back to the user's committed work
        subprocess.run(["git", "rebase", "--abort"], cwd=repo_root, capture_output=True)
        log_error_with_reasons(
            title=f"Failed to pull changes from origin/{branch}.",
            reasons=[
                f"Your changes conflict with new commits on origin/{branch}. They are committed locally and safe: "
                f"run 'git pull --rebase origin {branch}', resolve the conflicts, run 'git rebase --continue', "
                "then run ezgit-sync again.",
                "There is no remote named 'origin'. Add one with 'git remote add origin <url>'.",
                "You might be offline or lack permission to access the remote repository.",
            ],
            raw_error=_git_error_output(exc),
        )
        return False


def push_changes(repo_root: Path, branch: str) -> None:
    """Pushes the current branch to origin, creating it there if needed."""
    log_info(f"Pushing updates to origin/{branch}...")
    try:
        run_git(["push", "origin", branch], repo_root)
    except subprocess.CalledProcessError as exc:
        log_error_with_reasons(
            title=f"Failed to push changes to origin/{branch}.",
            reasons=[
                "Your commits are saved locally. Run ezgit-sync again once the problem is fixed to push them.",
                "Remote received new commits in the meantime. Run ezgit-sync again to pull them first.",
                "You may not have write permissions for this remote repository.",
                "Your authentication credentials (SSH key or GitHub token) might be missing or expired.",
            ],
            raw_error=_git_error_output(exc),
        )
        raise


def sync_local_changes(repo_root: Path, branch: str, commit_message: str) -> None:
    """Stages, commits, and pushes local changes to the remote repository."""
    commit_local_changes(repo_root, commit_message)
    push_changes(repo_root, branch)
