# Auto-generated improvement — Iteration 106
# Suggestion: Write function get_response_time_stats() that reads iteration_stats.jsonl and returns avg/p95 elapsed_s per backend

def get_response_time_stats():
    """Return average and 95th percentile elapsed_s per backend from iteration_stats.jsonl."""
    import json, os, math
    path = os.path.join(os.path.dirname(__file__), "iteration_stats.jsonl")
    data = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            b = rec.get("backend")
            t = rec.get("elapsed_s")
            if b is None or t is None:
                continue
            data.setdefault(b, []).append(t)
    result = {}
    for b, times in data.items():
        n = len(times)
        avg = sum(times) / n
        times.sort()
        idx = math.ceil(0.95 * n) - 1
        p95 = times[max(0, min(idx, n - 1))]
        result[b] = {"average_elapsed_s": avg, "p95_elapsed_s": p95}
    return result
