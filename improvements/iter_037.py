# Auto-generated improvement — Iteration 37
# Suggestion: 1. **Input Validation**: The `run_git` method assumes that the input will always be a valid Git command. However, if an invalid argument is passed (e.

def run_git(command):
    """Execute a validated git command and return its output or an error message."""
    import subprocess, shlex

    # Ensure command is a non‑empty string or list/tuple of arguments
    if isinstance(command, str):
        # Disallow chaining multiple commands with ';' or '&&'
        if any(op in command for op in (';', '&&', '|')):
            return "Error: multiple commands detected; only a single git command is allowed."
        args = shlex.split(command)
    elif isinstance(command, (list, tuple)):
        args = list(command)
        if any(isinstance(a, str) and any(op in a for op in (';', '&&', '|')) for a in args):
            return "Error: command arguments contain illegal chaining operators."
    else:
        return "Error: command must be a string or a list/tuple of arguments."

    # Must start with 'git'
    if not args or args[0] != "git":
        return "Error: command must start with 'git'."

    # Disallow empty arguments after git
    if len(args) == 1:
        return "Error: no git subcommand provided."

    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Git error: {e.stderr.strip()}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
