# Self-modification proposal — Iteration 55
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
    """Generate a concrete, single-step code modification suggestion."""
    import os
    import json

    try:
        py_files = sorted(
            f for f in os.listdir(self.repo_path)
            if f.endswith('.py') and not f.startswith('.')
        )[:10]
    except OSError:
        py_files = ['agent.py', 'inference.py', 'tools.py']

    context = {
        "goal": goal,
        "files": py_files,
        "instruction": (
            "Propose ONE specific, atomic code change. "
            "Format: FILE:path/to/file.py\nCHANGE:description\nCODE:```python\n...```"
        )
    }
    return json.dumps(context, indent=2)
