#!/bin/bash
# Start freeWillAi agent daemon
# Run this on the Raspberry Pi or other deployment target

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the launcher in the background
echo "Starting freeWill agent daemon from $REPO_DIR"
python3 launcher.py > agent.log 2>&1 &
PID=$!

echo "Agent started with PID $PID"
echo "Log: tail -f $REPO_DIR/agent.log"
echo "PID: $PID"

# Save PID to file
echo "$PID" > .agent.pid

# Wait a moment and check if it's still running
sleep 2
if kill -0 $PID 2>/dev/null; then
    echo "✓ Agent is running"
else
    echo "✗ Agent failed to start, check log"
fi
