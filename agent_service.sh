#!/bin/bash
# Systemd service script for freeWillAi autonomous agent
REPO_DIR="/home/pi/freeWillAi"
TRIGGER="$REPO_DIR/.run_now"
cd "$REPO_DIR"

if [ -d "venv" ]; then source venv/bin/activate; fi

INTERVAL=${AGENT_ITERATION_INTERVAL:-600}

while true; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running iteration..."
    python3 -u agent.py 2>&1 | sed -u 's/^/  /'
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Sleeping ${INTERVAL}s (touch .run_now to skip)..."
    elapsed=0
    while [ $elapsed -lt $INTERVAL ]; do
        if [ -f "$TRIGGER" ]; then
            rm -f "$TRIGGER"
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] Trigger detected -- running now"
            break
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
done
