# Auto-generated improvement — Iteration 44
# Suggestion: 1. **Error Handling**: The current implementation does not handle potential errors that may occur when executing the `git` command. It assumes that ev

def run_git_command(args, cwd=None, timeout=30):
    """Execute git command with error handling and return (success, output)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, f"Git failed ({result.returncode}): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, f"Git command timed out after {timeout}s
