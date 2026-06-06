#!/bin/bash
# Wrapper for systemd: runs agent.py in a loop (systemd handles the outer restart)
REPO_DIR="/home/pi/freeWillAi"
cd "$REPO_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

INTERVAL=${AGENT_ITERATION_INTERVAL:-300}

while true; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running iteration..."
    python3 agent.py 2>&1 | sed 's/^/  /'
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Sleeping ${INTERVAL}s..."
    sleep "$INTERVAL"
done
