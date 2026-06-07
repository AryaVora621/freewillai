# Auto-generated improvement — Iteration 71
# Suggestion: Add `subprocess.run` with the `stdout=subprocess.PIPE` argument to prevent output from being buffered

def run_command(cmd: list[str]) -> bytes:
    """Run command and return captured stdout."""
    import subprocess
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    return result.stdout
