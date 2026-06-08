# Auto-generated improvement — Iteration 114
# Suggestion: Write function monitor_openrouter_quota() that calls OpenRouter /auth/key to check remaining credits and logs warning if <10 calls left

def monitor_openrouter_quota(api_key):
    """Check OpenRouter credit quota and log warning if low."""
    import json, logging, urllib.request, urllib.error
    url = f"https://openrouter.ai/api/v1/auth/key?key={api_key}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.load(resp)
        remaining = data.get("credits", {}).get("remaining", 0)
        if remaining < 10:
            logging.warning("OpenRouter quota low: %s credits left", remaining)
    except urllib.error.URLError as e:
        logging.error("Failed to fetch OpenRouter quota: %s", e)
