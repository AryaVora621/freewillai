# Auto-generated improvement — Iteration 108
# Suggestion: Write function get_response_time_stats() that reads iteration_stats.jsonl and returns avg/p95 elapsed_s per backend

def get_response_time_stats(filepath="iteration_stats.jsonl"):
    """Return dict of backend -> {'avg': avg_elapsed, 'p95': p95_elapsed}."""
    import json, math
    data = {}
    with open(filepath) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            b = rec.get("backend")
            e = rec.get("elapsed_s")
            if b is None or e is None:
                continue
            data.setdefault(b, []).append(e)
    result = {}
    for b, vals in data.items():
        n = len(vals)
        avg = sum(vals) / n
        vals.sort()
        idx = min(math.ceil(0.95 * n) - 1, n - 1)
        p95 = vals[idx]
        result[b] = {"avg": avg, "p95": p95}
    return result
