# Auto-generated improvement — Iteration 105
# Suggestion: Write function get_response_time_stats() that reads iteration_stats.jsonl and returns avg/p95 elapsed_s per backend

def get_response_time_stats():
    """Return avg and p95 elapsed seconds per backend from iteration_stats.jsonl."""
    from pathlib import Path
    import json, statistics
    data = Path("iteration_stats.jsonl").read_text().splitlines()
    stats = {}
    for line in data:
        if not line: continue
        rec = json.loads(line)
        b = rec.get("backend")
        t = rec.get("elapsed_s")
        if b is None or t is None: continue
        stats.setdefault(b, []).append(t)
    result = {}
    for b, times in stats.items():
        avg = sum(times) / len(times)
        p95 = statistics.quantiles(times, n=100)[94]  # 95th percentile (index 94)
        result[b] = {"avg_elapsed_s": avg, "p95_elapsed_s": p95}
    return result
