#!/bin/bash
# Automated deployment script
# Deploys freeWillAi to aiserver@192.168.1.178

set -e

AISERVER="aiserver@192.168.1.178"
REMOTE_DIR="/home/aiserver/freeWillAi"

echo "=== Deploying freeWillAi to $AISERVER ==="

# Check connectivity
echo "Testing SSH connection..."
if ! ssh -q "$AISERVER" exit; then
    echo "ERROR: Cannot connect to $AISERVER"
    echo "Check that aiserver is running and SSH is accessible"
    exit 1
fi

echo "✓ Connected to $AISERVER"

# Create remote directory if needed
echo "Creating remote directory..."
ssh "$AISERVER" "mkdir -p $REMOTE_DIR"

# Copy setup script
echo "Copying setup script..."
scp -q setup_aiserver.sh "$AISERVER:~/"

# Run setup (user will be prompted for password once)
echo ""
echo "Running setup on aiserver..."
echo "You may be prompted for the aiserver password (aiserver)"
echo ""
ssh "$AISERVER" "bash ~/setup_aiserver.sh"

# Copy agent code
echo ""
echo "Copying agent code..."
rsync -az \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='.env' \
    --exclude='__pycache__' \
    --exclude='.freeWill_state.json' \
    . "$AISERVER:$REMOTE_DIR/"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. SSH into aiserver: ssh $AISERVER"
echo "2. Configure .env: nano $REMOTE_DIR/.env"
echo "3. Pull a model: ollama pull llama2"
echo "4. Start the service: sudo systemctl start freewill-agent"
echo "5. Watch logs: journalctl -u freewill-agent -f"
echo ""
echo "See DEPLOY.md for detailed instructions"
