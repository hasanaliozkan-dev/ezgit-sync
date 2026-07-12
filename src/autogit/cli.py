"""Console script for autogit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autogit.autogit import (
    get_current_branch,
    has_local_changes,
    log_error,
    log_success,
    log_warning,
    pull_remote_changes,
    sync_local_changes,
    verify_git_repository,
)


def main(argv: list[str] | None = None) -> int:
    """Console script for autogit."""
    parser = argparse.ArgumentParser(
        description="Pull remote updates, stage, commit, and push the current repository to GitHub."
    )
    parser.add_argument(
        "-m",
        "--message",
        default="Sync updates",
        help="Commit message to use when creating the commit.",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    if not verify_git_repository(repo_root):
        log_error(f"The current directory '{repo_root}' is not a valid Git repository.")
        return 1

    try:
        branch = get_current_branch(repo_root)

        if not pull_remote_changes(repo_root, branch):
            return 1

        if not has_local_changes(repo_root):
            log_warning("No new local changes to commit after pulling updates.")
            return 0

        sync_local_changes(repo_root, branch, args.message)

        log_success(f"Successfully synchronized repository with origin/{branch}.")
        return 0

    except Exception as exc:
        log_error(f"An error occurred during synchronization: {exc}")
        return 1

app = main
if __name__ == "__main__":
    sys.exit(main())