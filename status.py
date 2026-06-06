#!/usr/bin/env python3
"""Quick status check for freeWillAi agent."""
import json, os, subprocess
from pathlib import Path
from datetime import datetime

repo = '/home/pi/freeWillAi'

# State
state_file = Path(repo) / '.freeWill_state.json'
if state_file.exists():
    state = json.loads(state_file.read_text())
    print(f"Iterations: {state.get('iterations', 0)}")
    print(f"Improvements made: {len(state.get('improvements_made', []))}")
    goals = state.get('goals', [])
    active = [g for g in goals if g.get('status') == 'active']
    print(f"Goals: {len(goals)} total, {len(active)} active")
    if active:
        print(f"  Active: {active[0]['description'][:80]}")
    print(f"Last run: {state.get('last_run', 'unknown')}")
    print(f"Seen funding: {len(state.get('seen_funding_names', []))}/12")

print()

# Models
try:
    import requests
    r = requests.get('http://localhost:11434/api/tags', timeout=5)
    if r.status_code == 200:
        models = r.json().get('models', [])
        print(f"Local models: {[m['name'] for m in models]}")
except Exception as e:
    print(f"Ollama: {e}")

print()

# Daemon
r = subprocess.run(['pgrep', '-f', 'continuous_daemon.sh'], capture_output=True, text=True)
daemon_running = bool(r.stdout.strip())
print(f"Daemon: {'running' if daemon_running else 'NOT RUNNING'}")

# Last log line
log = Path(repo) / 'daemon.log'
if log.exists():
    lines = log.read_text().splitlines()
    print(f"Last log: {lines[-1][:100] if lines else '(empty)'}")

print()

# Recent improvements
imp_dir = Path(repo) / 'improvements'
if imp_dir.exists():
    files = sorted(imp_dir.glob('iter_*.py'))
    print(f"Code written: {len(files)} files")
    if files:
        print(f"  Latest: {files[-1].name}")

# KV memory
kv_file = Path(repo) / 'memory' / 'kv.json'
if kv_file.exists():
    kv = json.loads(kv_file.read_text())
    print(f"KV memory: {len(kv)} keys: {list(kv.keys())[:5]}")
