# Auto-generated improvement — Iteration 56
# Suggestion: Add a check before calling `strip()` to remove leading and trailing whitespace, including spaces at the start of the string.

def clean_whitespace(text: str) -> str:
    if not isinstance(text, str):
        return text
    stripped = text.strip()
    return stripped if stripped != text else text
