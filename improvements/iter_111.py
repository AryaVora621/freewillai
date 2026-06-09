# Auto-generated improvement — Iteration 111
# Suggestion: Add /diff Telegram command showing git diff --stat HEAD~3..HEAD to summarize last 3 commits of changes

def git_diff_summary():
    """Return git diff --stat for last 3 commits as a string."""
    import subprocess, shlex, os
    cwd = os.path.abspath(os.path.dirname(__file__))
    cmd = shlex.split('git diff --stat HEAD~3..HEAD')
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip() or "No changes in last 3 commits."
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip() or e}"
