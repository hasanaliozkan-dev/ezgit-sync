"""Top-level package for ezgit-sync."""

from .autogit import (
    get_current_branch,
    has_local_changes,
    log_error_with_reasons,
    log_info,
    log_success,
    log_warning,
    pull_remote_changes,
    sync_local_changes,
    verify_git_repository,
)

__all__ = [
    "get_current_branch",
    "has_local_changes",
    "log_error_with_reasons",
    "log_info",
    "log_success",
    "log_warning",
    "pull_remote_changes",
    "sync_local_changes",
    "verify_git_repository",
]
