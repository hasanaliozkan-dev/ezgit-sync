![PyPI version](https://img.shields.io/pypi/v/ezgit-sync.svg) [![License - MIT 3-Clause](https://img.shields.io/pypi/l/ezgit-sync.svg)](https://github.com/hasanaliozkan-dev/ezgit-sync/blob/main/LICENSE) [![PyPI Downloads](https://static.pepy.tech/badge/ezgit-sync?label=PyPI%20Downloads)](https://pepy.tech/projects/ezgit-sync) ![Visitors](https://visitor-badge.laobi.icu/badge?page_id=hasanaliozkan-dev/ezgit-sync)


![PyPI version](https://img.shields.io/pypi/v/ezgit-sync.svg) [![License - MIT 3-Clause](https://img.shields.io/pypi/l/ezgit-sync.svg)](https://github.com/hasanaliozkan-dev/ezgit-sync/blob/main/LICENSE) [![PyPI Downloads](https://static.pepy.tech/badge/ezgit-sync?label=PyPI%20Downloads)](https://pepy.tech/projects/ezgit-sync) ![Visitors](https://visitor-badge.laobi.icu/badge?page_id=hasanaliozkan-dev/ezgit-sync)


# ezgit-sync
```
  ___ ______ _(_) |_      ___ _   _ _ __   ___ 
 / _ \_  / _` | | __|____/ __| | | | '_ \ / __|
|  __// / (_| | | ||_____\__ \ |_| | | | | (__ 
 \___/___\__, |_|\__|    |___/\__, |_| |_|\___|
         |___/                |___/          
```

### Description

Designed for data scientists and ML/DL practitioners, this library automates routine Git operations to accelerate your development cycle.

### Features

*   **Automated Git Workflow**: Pulls remote changes, commits local work, and pushes to the remote repository in a single command.
*   **Branch Awareness**: Automatically detects and operates on your current Git branch.
*   **Intelligent Syncing**: Checks for local modifications before committing and avoids unnecessary operations if there's nothing to sync.
*   **Custom Commit Messages**: Specify a commit message for your sync via the command line.
*   **User-Friendly Logging**: Provides clear, color-coded terminal output for success, warnings, and info.
*   **Detailed Error Handling**: Offers descriptive error messages with common reasons and suggested solutions to help you troubleshoot quickly.

### Installation
You can install ezgit-sync directly from PyPI using standard package managers:

```bash
pip install ezgit-sync
```

If you are using uv (as in your development environment), you can also install it via:

```bash
uv pip install ezgit-sync
```

### Usage Examples
##### Basic Usage
```sync_local_changes(repo_root, branch, commit_message)```

Stages all current modifications (git add -A), creates a commit with the provided message, and pushes the commits to the remote branch.

```python
try:
    sync_local_changes(Path("."), "main", "Automated model weights update")
    print("Sync complete!")
except Exception:
    print("Sync failed during push.")
```
##### CLI Usage
```bash
ezgit-sync
```
Under the hood, this will:
 * Verify you are in a Git repository (verify_git_repository).
 * Identify your current branch (get_current_branch).
 * Pull the latest remote changes (pull_remote_changes).
 * Stage all local modifications (has_local_changes).
Commit with a default message (e.g., "Auto-sync via ezgit-sync") and push to the remote (sync_local_changes).


##### Complete Workflow Example
```python
from pathlib import Path

def run_ezgit_sync(message: str = "Automated sync"):
    repo_root = Path.cwd()
    
    # 1. Ensure we are in a Git repository
    if not verify_git_repository(repo_root):
        return

    # 2. Get the current branch
    try:
        branch = get_current_branch(repo_root)
    except Exception:
        return

    # 3. Pull latest changes to avoid conflicts
    if not pull_remote_changes(repo_root, branch):
        return

    # 4. Check for local changes and push if necessary
    if has_local_changes(repo_root):
        try:
            sync_local_changes(repo_root, branch, message)
            log_success(f"Successfully synced branch '{branch}'!")
        except Exception:
            # The function already logged the specific error
            pass
    else:
        log_info("Everything is up-to-date. Nothing to commit.")

# Execute the workflow
run_ezgit_sync(message="Update ResNet training script")
```
### Development

To set up for local development:

```sh
# Clone your fork
git clone git@github.com:your_username/ezgit-sync.git
cd ezgit-sync

# Install dependencies
uv sync

# Create a branch for development
git checkout -b feature/new-awesome-feature
```

### Author
ezgit-sync was created in 2026 by Hasan Ali Özkan.

### Credits
Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.