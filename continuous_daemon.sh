#!/bin/bash
# Continuous daemon mode for freeWillAi
# Supports trigger file for on-demand iteration

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIGGER="$REPO_DIR/.run_now"
cd "$REPO_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting freeWill agent continuous daemon"
echo "Log file: $REPO_DIR/daemon.log"
echo "Trigger file: $TRIGGER (touch to run immediately)"
echo ""

{
    while true; do
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running iteration..."
        python3 agent.py 2>&1 | sed 's/^/  /'

        INTERVAL=$(grep AGENT_ITERATION_INTERVAL .env 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo 600)
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Sleeping ${INTERVAL}s (touch .run_now to skip)..."

        # Sleep in 5s chunks, checking for trigger file
        elapsed=0
        while [ $elapsed -lt $INTERVAL ]; do
            if [ -f "$TRIGGER" ]; then
                rm -f "$TRIGGER"
                echo "[$(date +'%Y-%m-%d %H:%M:%S')] Trigger file detected -- running now"
                break
            fi
            sleep 5
            elapsed=$((elapsed + 5))
        done
    done
} >> daemon.log 2>&1 &

PID=$!
echo "$PID" > .daemon.pid
echo "Daemon started with PID $PID"
