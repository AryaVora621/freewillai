# Auto-generated improvement — Iteration 42
# Suggestion:         *args: Additional Git commands (e.g., add, sign)

def run_git_commands(*args):
    """Execute git with optional extra commands (e.g., add, sign) and return output."""
    import subprocess

    # Base git command
    cmd = ["git"] + list(args)

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Return error details for debugging
        return f"Error: {e.stderr.strip()}"
