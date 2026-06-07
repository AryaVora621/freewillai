# Self-modification proposal — Iteration 50
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
    """Generate a concrete, single-step code modification suggestion."""
    from pathlib import Path
    import json

    try:
        repo = Path(self.repo_path)
        py_files = sorted(repo.glob("*.py"))[:10]
        files_list = "\n".join(f.name for f in py_files)
        file_contents = {}
        for f in py_files[:3]:
            try:
                file_contents[f.name] = f.read_text(encoding="utf-8")[:2000]
            except Exception:
                pass
    except Exception as e:
        return json.dumps({"error": f"Failed to scan repo: {e}", "suggestion": ""})

    prompt = f"""Goal: {goal}

Repository Python files:
{files_list}

Key file contents:
{json.dumps(file_contents, indent=2)}

Return JSON: {{"file": "filename.py", "change": "specific modification description", "reason": "why this addresses the goal"}}"""
    return prompt
