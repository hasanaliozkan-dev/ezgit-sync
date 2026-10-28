"""Top-level package for ezgit-sync."""

from .autogit import (
    commit_local_changes,
    get_current_branch,
    has_local_changes,
    has_unpushed_commits,
    log_error_with_reasons,
    log_info,
    log_success,
    log_warning,
    pull_remote_changes,
    push_changes,
    sync_local_changes,
    verify_git_repository,
)

__all__ = [
    "commit_local_changes",
    "get_current_branch",
    "has_local_changes",
    "has_unpushed_commits",
    "log_error_with_reasons",
    "log_info",
    "log_success",
    "log_warning",
    "pull_remote_changes",
    "push_changes",
    "sync_local_changes",
    "verify_git_repository",
]
