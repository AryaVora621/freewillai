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

        # Watchdog: kill agent.py + Ollama if iteration exceeds 5 minutes
        PYTHONUNBUFFERED=1 python3 -u agent.py 2>&1 | sed -u 's/^/  /' &
        AGENT_PID=$!
        WATCHDOG_MAX=300  # 5 minutes max per iteration

        elapsed_watch=0
        while kill -0 $AGENT_PID 2>/dev/null && [ $elapsed_watch -lt $WATCHDOG_MAX ]; do
            sleep 5
            elapsed_watch=$((elapsed_watch + 5))
        done

        if kill -0 $AGENT_PID 2>/dev/null; then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] WATCHDOG: iteration exceeded ${WATCHDOG_MAX}s — killing agent + Ollama"
            kill -9 $AGENT_PID 2>/dev/null
            pkill -9 -f 'ollama runner' 2>/dev/null
            pkill -f 'ollama serve' 2>/dev/null
        fi
        wait $AGENT_PID 2>/dev/null

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
