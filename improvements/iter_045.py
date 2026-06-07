# Auto-generated improvement — Iteration 45
# Suggestion: 1. **Error Handling**: The current implementation assumes that the `git` command will always succeed. However, if the command fails for any reason (e.

def run_git_command(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Run a git command with error handling, returning (returncode, stdout, stderr)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "git command timed out after 30 seconds"
    except FileNot
