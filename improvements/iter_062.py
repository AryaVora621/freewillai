# Auto-generated improvement — Iteration 62
# Suggestion: Add a check to ensure the response from the API is not empty before proceeding

def import urllib.request
import json

def fetch_api_data(url):
    """Fetch JSON data from API, return None if empty or error."""
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            raw = resp.read().decode()
            if not raw:
                return None
            return json.loads(raw)
    except Exception:
        return None
