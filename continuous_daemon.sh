#!/bin/bash
# Continuous daemon mode for freeWillAi
# Supports trigger file for on-demand iteration

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIGGER="$REPO_DIR/.run_now"
PIDFILE="$REPO_DIR/.daemon.pid"
cd "$REPO_DIR"

# Kill any existing daemon (shell + all its python3 agent.py children)
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing daemon (PID $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null
        sleep 1
    fi
fi
# Also kill stray agent.py processes
pkill -f "python3 agent.py" 2>/dev/null
sleep 1

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
        PYTHONUNBUFFERED=1 python3 agent.py 2>&1 | sed 's/^/  /'

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
echo "$PID" > "$PIDFILE"
echo "Daemon started with PID $PID"
