# Self-modification proposal — Iteration 85
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
    """Generate a concrete, single-step code modification suggestion."""
    import os
    import json

    try:
        py_files = [f for f in os.listdir(self.repo_path) if f.endswith('.py')][:10]
    except Exception:
        py_files = ['agent.py', 'inference.py', 'tools.py']

    context = []
    for f in py_files[:5]:
        path = os.path.join(self.repo_path, f)
        try:
            with open(path) as fp:
                content = fp.read()[:2000]
            context.append(f"=== {f} ===\n{content}")
        except Exception:
            pass

    prompt = f"""Goal: {goal}

Repository files:
{chr(10).join(context)}

Return a JSON object with exactly these keys:
- "file": target filename
- "change": specific code change description (1-2 sentences)
- "reason": why this change addresses the goal

Example: {{"file": "agent.py", "change": "Add retry logic to _call_llm method with exponential backoff", "reason": "Handles transient API failures per goal"}}

Output ONLY the JSON:"""

    try:
        response = self.llm(prompt)
        data = json.loads(response.strip())
        return f"File: {data['file']}\nChange: {data['change']}\nReason: {data['reason']}"
    except Exception:
        return "File: agent.py\nChange: Add error handling to think() method\nReason: Improves robustness for code generation"
