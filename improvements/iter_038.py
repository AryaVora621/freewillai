# Auto-generated improvement — Iteration 38
# Suggestion: 1. **Error Handling**: The current implementation does not handle errors that may occur when executing Git commands or running subprocesses. It's esse

def run_git_command(args, cwd=None):
    """Execute a git command safely and return its output, handling errors."""
    import subprocess
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Git command failed; return stderr for diagnostics
        return f"Git error: {e.stderr.strip()}"
    except FileNotFoundError:
        # Git executable not found
        return "Git executable not found on this system."
    except Exception as e:
        # Catch-all for unexpected errors
        return f"Unexpected error: {e}"
