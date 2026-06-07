# Auto-generated improvement — Iteration 40
# Suggestion: 1. **Error Handling**: The current implementation does not handle potential errors that may occur during execution, such as invalid Git commands or fi

def run_git_action(repo_path, command, *args):
    """Execute a git command in the given repository with error handling."""
    import subprocess
    import os

    if not os.path.isdir(repo_path):
        raise FileNotFoundError(f"Repository path not found: {repo_path}")

    full_cmd = ["git", "-C", repo_path, command] + list(args)
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
        return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "code": result.returncode}
    except subprocess.CalledProcessError as e:
        # Git command failed; return details without raising
        return {"stdout": e.stdout.strip() if e.stdout else "", "stderr": e.stderr.strip() if e.stderr else "", "code": e.returncode}
    except Exception as exc:
        # Unexpected error (e.g., permission issues)
        return {"stdout": "", "stderr": str(exc), "code": -1}
