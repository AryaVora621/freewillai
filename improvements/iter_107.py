# Auto-generated improvement — Iteration 107
# Suggestion: Write function get_response_time_stats() that reads iteration_stats.jsonl and returns avg/p95 elapsed_s per backend

def get_response_time_stats():
    """Return avg and 95th percentile elapsed_s per backend from iteration_stats.jsonl."""
    import json, os, math
    path = os.path.join(os.path.dirname(__file__), "iteration_stats.jsonl")
    data = {}
    counts = {}
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            be = rec.get("backend")
            et = rec.get("elapsed_s")
            if be is None or et is None:
                continue
            data.setdefault(be, []).append(et)
            counts[be] = counts.get(be, 0) + 1
    result = {}
    for be, vals in data.items():
        n = len(vals)
        avg = sum(vals) / n if n else 0
        vals.sort()
