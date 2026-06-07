# Self-modification proposal — Iteration 80
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
    """Generate a concrete, single-step code modification suggestion."""
    import os
    import json

    try:
        py_files = []
        for root, _, files in os.walk(self.repo_path):
            for f in files:
                if f.endswith('.py') and not f.startswith('.'):
                    rel = os.path.relpath(os.path.join(root, f), self.repo_path)
                    py_files.append(rel)
            if len(py_files) >= 10:
                break
        files_list = "\n".join(py_files[:10]) or "No Python files found"
    except Exception as e:
        files_list = f"Error scanning repo: {e}"

    prompt = f"""Goal: {goal}

Repository Python files:
{files_list}

Return a JSON object with exactly these keys:
- "file": relative path to modify
- "change": single concrete modification (e.g., "Add retry logic to fetch_data()", "Fix type hint in process()")
- "reason": one-sentence justification

Respond ONLY with valid JSON."""
    
    return prompt
