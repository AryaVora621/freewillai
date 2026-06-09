# Auto-generated improvement — Iteration 82
# Suggestion: Add a docstring to describe the purpose of the `OllamaClient` class

def create_ollama_client():
    """Factory function that returns an OllamaClient class with docstring."""
    class OllamaClient:
        """Client for interacting with Ollama LLM API on Raspberry Pi."""
        def __init__(self, host="localhost", port=11434):
            self.base_url = f"http://{host}:{port}"
        def generate(self, model, prompt):
            import urllib.request, json
            data = json.dumps({"model": model, "prompt": prompt}).encode()
            req = urllib.request.Request(f"{self.base_url}/api/generate", data=data)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
    return OllamaClient
