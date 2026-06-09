# Auto-generated improvement — Iteration 99
# Suggestion: **Extract `tool_name` variable into a constant**: The `elif tool_name == "none"` block can be extracted into its own constant:

def get_tool_status(tool_name: str) -> str:
    TOOL_NONE = "none"
    
    if tool_name == "drill":
        return "drilling"
    elif tool_name == "saw":
        return "cutting"
    elif tool_name == TOOL_NONE:
        return "idle"
    else:
        return "unknown"
