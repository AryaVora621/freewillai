# Self-modification proposal — Iteration 40
# Source: self_modify() in agent.py

def think(self, goal: str) -> str:
        """Generate a concrete, single-step code modification suggestion."""
        import os as _os
        import json as _json

        # Gather a short snapshot of the repository files
        try:
            py_files = [f for f in _os.listdir(self.repo_path) if f.endswith('.py')]
            # Limit to the first few files to keep prompt size manageable
            py_files = py_files[:5]
            files_content = {}
            for f in py_files:
                try:
                    with open(_os.path.join(self.repo_path, f), 'r', encoding='utf-8') as fh:
                        files_content[f] = fh.read()
                except Exception:
                    files_content[f] = "<unreadable>"
        except Exception:
            # Fallback to a generic placeholder if listing fails
            files_content = {
                "agent.py": "<placeholder>",
                "inference.py": "<placeholder>",
                "tools.py": "<placeholder>"
            }

        # Summarize recent test outcome (truncated)
        recent_test = self.state.get('last_test_result', 'none')
        recent_test = recent_test[:200]  # keep a reasonable length

        # Build a concise, structured prompt for the local model
        prompt_dict = {
            "task": goal,
            "repo_snapshot": files_content,
            "recent_test_result": recent_test,
            "instruction": (
                "Propose ONE concrete code change that moves the agent closer to the task. "
                "Return a JSON object with exactly these fields:\n"
                "  - file: relative path to the file to edit\n"
                "  - line_range: \"start-end\" (1‑based inclusive) of lines to replace\n"
                "  - change: the new code snippet (preserve indentation)\n"
                "  - rationale: one sentence why this change helps"
            )
        }
        prompt = _json.dumps(prompt_dict, ensure_ascii=False, indent=2)

        # Call the local model (assume self.model has a .generate method)
        try:
            raw_output = self.model.generate(prompt, max_tokens=300, temperature=0.2)
        except Exception as e:
            return f"Error: model generation failed – {e}"

        # Parse and validate the model's JSON response
        try:
            suggestion = _json.loads(raw_output)
            required_keys = {"file", "line_range", "change", "rationale"}
            if not required_keys.issubset(suggestion.keys()):
                raise ValueError("Missing required fields")
            # Ensure line_range format
            start_end = suggestion["line_range"].split("-")
            if len(start_end) != 2 or not all(part.isdigit() for part in start_end):
                raise ValueError("Invalid line_range format")
            # Return a clean, single‑line instruction for downstream execution
            return _json.dumps(suggestion, ensure_ascii=False)
        except Exception:
            # Fallback to a raw text suggestion if JSON parsing fails
            return raw_output.strip()
