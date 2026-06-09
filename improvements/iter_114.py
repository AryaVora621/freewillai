# Auto-generated improvement — Iteration 114
# Suggestion: Write function monitor_openrouter_quota() that calls OpenRouter /auth/key to check remaining credits and logs warning if <10 calls left

def monitor_openrouter_quota():
    """Check OpenRouter API quota and log warning if low."""
    import os, json, logging, urllib.request
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logging.error('OPENROUTER_API_KEY not set')
        return
    try:
        req = urllib.request.Request('https://openrouter.ai/api/v1/auth/key', headers={'Authorization': f'Bearer {api_key}'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.load(resp)
        remaining = data.get('credits', {}).get('remaining')
        if remaining is not None and remaining < 10:
            logging.warning(f'OpenRouter quota low: {remaining} credits left')
    except Exception as e:
        logging.error(f'Failed to check OpenRouter quota: {e}')
