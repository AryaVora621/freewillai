# Auto-generated improvement — Iteration 109
# Suggestion: Write function get_response_time_stats() that reads iteration_stats.jsonl and returns avg/p95 elapsed_s per backend

def get_response_time_stats():
    """Return avg and p95 elapsed_s per backend from iteration_stats.jsonl."""
    import json, os, math
    path = os.path.join(os.getcwd(), "iteration_stats.jsonl")
    if not os.path.isfile(path):
        return {}
    data = {}
    with open(path, "r") as f:
        for line in f:
            try:
                rec = json.loads(line)
                be = rec.get("backend")
                elapsed = rec.get("elapsed_s")
                if be is None or elapsed is None:
                    continue
                data.setdefault(be, []).append(elapsed)
            except json.JSONDecodeError:
                continue
    result = {}
    for be, times in data.items():
        n = len(times)
        avg = sum(times) / n
