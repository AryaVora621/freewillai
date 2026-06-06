#!/bin/bash
# Continuous daemon mode for freeWillAi
# Runs agent iterations in a loop, persisting state between runs

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting freeWill agent continuous daemon"
echo "Running iterations every AGENT_ITERATION_INTERVAL seconds (default 300)"
echo "Log file: $REPO_DIR/daemon.log"
echo ""

{
    while true; do
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running iteration..."
        python3 agent.py 2>&1 | sed 's/^/  /'

        # Read iteration interval from .env or use default
        INTERVAL=$(grep AGENT_ITERATION_INTERVAL .env 2>/dev/null | cut -d= -f2 || echo 300)
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Sleeping for $INTERVAL seconds..."
        sleep "$INTERVAL"
    done
} >> daemon.log 2>&1 &

PID=$!
echo "$PID" > .daemon.pid
echo "Daemon started with PID $PID"
