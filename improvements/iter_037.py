# Auto-generated improvement — Iteration 37
# Suggestion: 1. **Import and error handling in `git_controller.py`** – Add the missing imports (`import subprocess`) and guard the Git subprocess calls with proper

def GitError(Exception):
    """Custom exception for Git command failures."""
    pass


import subprocess


def run_git_command(args, cwd=None):
    """Execute a git command, raising GitError on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise GitError(f"Failed to start git: {exc}") from exc

    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip()
        raise GitError(f"Git command {' '.join(args)} failed: {msg}")

    return result.stdout.strip()
