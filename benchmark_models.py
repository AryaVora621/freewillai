#!/usr/bin/env python3
"""
Quick model benchmark script -- the agent can run this to test its own inference speed.
Saves results to memory/kv.json under key 'model_benchmarks'.
"""
import subprocess
import time
import json
import sys
from pathlib import Path

REPO = Path("/home/pi/freeWillAi")
OLLAMA = "http://localhost:11434"

def bench_model(model: str, prompt: str = "What is 2+2? Answer with just the number.", max_tokens: int = 20):
    import urllib.request, json as _j
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "keep_alive": 30, "options": {"num_predict": max_tokens}}).encode()
    start = time.time()
    try:
        req = urllib.request.Request(f"{OLLAMA}/api/generate",
                                     data=payload, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = _j.loads(r.read())
        elapsed = time.time() - start
        tps = data.get("eval_count", 1) / max(data.get("eval_duration", 1) / 1e9, 0.001)
        return {"model": model, "tokens_per_sec": round(tps, 2),
                "latency_ms": round(elapsed * 1000), "output": data.get("response", "")[:40]}
    except Exception as e:
        return {"model": model, "error": str(e)}

models = ["llama3.2:1b", "qwen2.5:0.5b"]
results = {}
for m in models:
    print(f"Benchmarking {m}...")
    r = bench_model(m)
    results[m] = r
    print(f"  {m}: {r}")

# Save to KV store
kv_file = REPO / "memory" / "kv.json"
kv = json.loads(kv_file.read_text()) if kv_file.exists() else {}
kv["model_benchmarks"] = results
kv_file.write_text(json.dumps(kv, indent=2))
print("Results saved to memory/kv.json")

# Print summary
for m, r in results.items():
    if "error" not in r:
        print(f"{m}: {r['tokens_per_sec']} tok/s, {r['latency_ms']}ms")
