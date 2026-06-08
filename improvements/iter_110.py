# Auto-generated improvement — Iteration 110
# Suggestion: Add /code Telegram command showing last 3 self-edit commits: file changed, function name, git diff summary

def get_last_edits():
    """Return summary of last 3 self-edit git commits for /code command."""
    import subprocess, json, re, os, sys
    try:
        # Get last 3 commits authored by the current user
        user = subprocess.check_output(['git', 'config', 'user.email']).decode().strip()
        log = subprocess.check_output(['git', 'log', '--author=' + user, '--pretty=%H', '-n', '3']).decode().splitlines()
        entries = []
        for rev in log:
            diff = subprocess.check_output(['git', 'show', '--name-only', '--pretty=format:', rev]).decode().splitlines()
            files = [f for f in diff if f]
            for f in files:
                # extract function name via simple regex on added lines
                show = subprocess.check_output(['git', 'show', rev, '--', f]).decode()
                funcs = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', show)
                summary = subprocess.check_output(['git', 'show', '--stat', rev, '--', f]).decode().splitlines()[-1]
                entries.append(f"{rev[:7]} {f}: {', '.join(funcs) or 'no func'} – {summary}")
        return "\n".join(entries[:3])
    except Exception as e:
        return f"Error: {e}"
