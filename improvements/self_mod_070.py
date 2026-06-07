# Self-modification proposal — Iteration 70
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
    """Generate a concrete, single-step code modification suggestion."""
    import os
    import json

    try:
        py_files = [f for f in os.listdir(self.repo_path) if f.endswith('.py')][:5]
    except Exception:
        return "Error: Cannot access repository files"

    context = []
    for f in py_files:
        path = os.path.join(self.repo_path, f)
        try:
            with open(path) as fp:
                content = fp.read()[:2000]
            context.append(f"=== {f} ===\n{content}")
        except Exception:
            continue

    prompt = f"""Goal: {goal}

Repository files:
{chr(10).join(context)}

Return a JSON object with exactly these fields:
- "file": target filename
- "action": "replace" | "insert_after" | "delete"
- "target": exact code snippet to find (for replace/insert_after) or delete (for delete)
- "replacement": new code snippet (for replace/insert_after) or empty string (for delete)
- "reasoning": one-sentence explanation

Choose the single most impactful change. Output ONLY valid JSON."""

    return prompt
