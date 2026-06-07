# Auto-generated improvement — Iteration 50
# Suggestion: Add a `try`-`except` block around the request to catch any exceptions that might occur during the request.

def fetch_url(url, timeout=10):
    import urllib.request, urllib.error
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.URLError as e:
        return f"URL error: {e.reason}"
    except TimeoutError:
        return "Request timed out"
    except Exception as e:
        return f"Unexpected error: {e}"
