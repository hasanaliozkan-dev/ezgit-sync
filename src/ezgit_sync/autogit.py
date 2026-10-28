"""Main module for ezgit-sync."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ANSI Escape Sequences for Terminal Styling
COLOR_RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"


def log_success(message: str) -> None:
    """Prints a styled success message."""
    print(f"{COLOR_GREEN}{BOLD}[SUCCESS]{COLOR_RESET} {message}")


def log_warning(message: str) -> None:
    """Prints a styled warning message."""
    print(f"{COLOR_YELLOW}{BOLD}[WARNING]{COLOR_RESET} {message}")


def log_info(message: str) -> None:
    """Prints a styled info message."""
    print(f"{COLOR_CYAN}{BOLD}[INFO]{COLOR_RESET} {message}")


def log_error_with_reasons(title: str, reasons: list[str], raw_error: str | None = None) -> None:
    """Formats and prints error explanations with probable causes and solutions."""
    sys.stderr.write(f"\n{COLOR_RED}{BOLD}[ERROR] {title}{COLOR_RESET}\n")
    sys.stderr.write(f"{BOLD}Possible Reasons & Solutions:{COLOR_RESET}\n")
    for reason in reasons:
        sys.stderr.write(f"  • {reason}\n")
    
    if raw_error:
        sys.stderr.write(f"\n{DIM}Raw Git Error Details:\n{raw_error.strip()}{COLOR_RESET}\n")
    sys.stderr.write("\n")


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
        raw_err = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        log_error_with_reasons(
            title="Failed to determine active Git branch.",
            reasons=[
                "This repository might be completely empty (no commits yet). Create an initial commit first: 'git add . && git commit -m \"initial commit\"'",
                "Your repository might be in a 'detached HEAD' state. Switch to a branch using 'git checkout <branch-name>'.",
            ],
            raw_error=raw_err,
        )
        raise exc


def pull_remote_changes(repo_root: Path, branch: str) -> bool:
    """Pulls recent changes from the remote repository."""
    log_info(f"Pulling latest updates from origin/{branch}...")
    try:
        run_git(["pull", "origin", branch], repo_root)
        return True
    except subprocess.CalledProcessError as exc:
        log_error_with_reasons(
            title=f"Failed to pull changes from origin/{branch}.",
            reasons=[
                "There might be merge conflicts between local and remote files. Resolve conflicts manually.",
                "The remote branch 'origin/{branch}' might not exist yet on the remote server.",
                "You might be offline or lack permission to access the remote repository.",
            ],
            raw_error=exc.stderr,
        )
        return False


def has_local_changes(repo_root: Path) -> bool:
    """Checks if there are uncommitted local modifications."""
    status = run_git(["status", "--porcelain"], repo_root)
    return bool(status)


def sync_local_changes(repo_root: Path, branch: str, commit_message: str) -> None:
    """Stages, commits, and pushes local changes to the remote repository."""
    log_info("Staging and committing local changes...")
    run_git(["add", "-A"], repo_root)
    run_git(["commit", "-m", commit_message], repo_root)

    log_info(f"Pushing updates to origin/{branch}...")
    try:
        run_git(["push", "origin", branch], repo_root)
    except subprocess.CalledProcessError as exc:
        log_error_with_reasons(
            title=f"Failed to push changes to origin/{branch}.",
            reasons=[
                "Remote contains commits that you do not have locally. Try pulling first.",
                "You may not have write permissions for this remote repository.",
                "Your authentication credentials (SSH key or GitHub token) might be missing or expired.",
            ],
            raw_error=exc.stderr,
        )
        raise exc