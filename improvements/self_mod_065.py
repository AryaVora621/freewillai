# Self-modification proposal — Iteration 65
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
    """Generate a concrete, single-step code modification suggestion."""
    import os
    import json

    try:
        py_files = []
        for root, _, files in os.walk(self.repo_path):
            for f in files:
                if f.endswith('.py') and not f.startswith('test_'):
                    py_files.append(os.path.relpath(os.path.join(root, f), self.repo_path))
            if len(py_files) >= 10:
                break
        files_list = '\n'.join(py_files[:10]) or 'No Python files found'
    except OSError:
        files_list = 'agent.py\ninference.py\ntools.py'

    prompt = f"""Goal: {goal}

Repository Python files:
{files_list}

Return a JSON object with a single concrete code change:
{{"file": "path/to/file.py", "change": "Specific modification description", "reason": "Why this addresses the goal"}}"""
    return prompt
