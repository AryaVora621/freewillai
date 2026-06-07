# Auto-generated improvement — Iteration 51
# Suggestion: **Consistent spacing and indentation**: The function `parse_tool_call` uses both spaces and tabs for indentation, which can make it harder to read for

def parse_tool_call(text: str) -> dict:
    import re, ast
    match = re.match(r'(\w+)\((.*)\)', text.strip())
    if not match:
        return {"error": "Invalid format"}
    name, args_str = match.groups()
    kwargs = {}
    if args_str:
        try:
            tree = ast.parse(f"f({args_str})", mode='eval')
            for kw in tree.body.keywords:
                kwargs[kw.arg] = ast.literal_eval(kw.value)
        except (SyntaxError, ValueError):
            return {"error": "Parse failed"}
    return {"name": name, "arguments": kwargs}
