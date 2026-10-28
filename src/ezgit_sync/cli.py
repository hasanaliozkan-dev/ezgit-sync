"""Console script for ezgit-sync."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ezgit_sync.autogit import (
    commit_local_changes,
    get_current_branch,
    has_local_changes,
    has_unpushed_commits,
    log_error_with_reasons,
    log_success,
    log_warning,
    pull_remote_changes,
    push_changes,
    verify_git_repository,
)


def main(argv: list[str] | None = None) -> int:
    """Console script for ezgit-sync."""
    parser = argparse.ArgumentParser(
        description="Commit local changes, pull remote updates, and push the current branch to origin."
    )
    parser.add_argument(
        "-m",
        "--message",
        default="Auto-sync via ezgit-sync",
        help="Commit message to use when creating the commit.",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    if not verify_git_repository(repo_root):
        return 1

    try:
        branch = get_current_branch(repo_root)

        # Commit before pulling so incoming commits are rebased onto saved work instead of clashing with it
        committed = has_local_changes(repo_root)
        if committed:
            commit_local_changes(repo_root, args.message)

        if not pull_remote_changes(repo_root, branch):
            return 1

        if not committed and not has_unpushed_commits(repo_root):
            log_warning("No new local changes to commit or push.")
            return 0

        push_changes(repo_root, branch)

        log_success(f"Successfully synchronized repository with origin/{branch}.")
        return 0

    except (subprocess.CalledProcessError, RuntimeError):
        return 1  # the failing step has already reported the error
    except Exception as exc:
        log_error_with_reasons("An unexpected error occurred during synchronization.", [str(exc)])
        return 1


if __name__ == "__main__":
    sys.exit(main())
