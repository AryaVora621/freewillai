# Auto-generated improvement — Iteration 112
# Suggestion: Write function generate_test_case(func_code) that produces a minimal assert-based test for a given function definition

def generate_test_case(func_code):
    """Return a simple assert test string for the given function code."""
    import ast, textwrap, random, string
    tree = ast.parse(func_code)
    func = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    name = func.name
    args = [arg.arg for arg in func.args.args]
    defaults = [None]*(len(args)-len(func.args.defaults)) + func.args.defaults
    def gen_val(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        return 0
    sample_vals = []
    for d in defaults:
        if d is None:
            sample_vals.append(0)
        else:
            sample_vals.append(gen_val(d))
