# Auto-generated improvement — Iteration 97
# Suggestion: Add a check for log file existence and create it if not

def ensure_log_file(path):
    """Ensure log file exists, create if missing."""
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch(exist_ok=True)
    return p
