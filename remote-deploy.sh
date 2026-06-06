#!/bin/bash
# Remote deployment script - Execute on local machine, deploys to aiserver
# Usage: bash remote-deploy.sh aiserver@192.168.1.178

REMOTE_HOST="${1:-aiserver@192.168.1.178}"
REMOTE_PASS="${2:-aiserver}"
LOCAL_REPO="/Users/aryavora/Desktop/Personal Projects/freeWillAi"

echo "Deploying freeWillAi to $REMOTE_HOST..."

# Install sshpass if needed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    brew install sshpass 2>/dev/null || echo "Please install sshpass manually"
    exit 1
fi

# Copy files to remote
echo "Copying files..."
sshpass -p "$REMOTE_PASS" scp -r -o StrictHostKeyChecking=no \
    "$LOCAL_REPO"/*.py \
    "$LOCAL_REPO"/*.sh \
    "$LOCAL_REPO"/.env.example \
    "$LOCAL_REPO"/.gitignore \
    "$LOCAL_REPO"/requirements.txt \
    "$REMOTE_HOST":~/freeWillAi/ || {
    echo "Failed to copy files - connection issue"
    exit 1
}

# Run deployment script on remote
echo "Running deployment on remote..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_HOST" "bash ~/freeWillAi/DEPLOY_NOW.sh"

echo "Deployment complete! SSH into aiserver to configure and start."
