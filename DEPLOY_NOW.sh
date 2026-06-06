#!/bin/bash
# Quick deployment - Run this on aiserver to deploy freeWillAi immediately

set -e

echo "=== freeWillAi Emergency Deployment ==="
echo "This script will deploy freeWillAi on the current machine"
echo ""

# Check if running on aiserver
HOSTNAME=$(hostname)
echo "Running on: $HOSTNAME"

# Create deployment directory (use current user's home)
DEPLOY_DIR="$HOME/freeWillAi"
echo "Creating deployment directory: $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Clone from GitHub or use local if available
if [ -d "/tmp/freeWillAi" ]; then
    echo "Using local copy..."
    cp -r /tmp/freeWillAi/* .
elif command -v git &> /dev/null; then
    echo "Cloning from repository..."
    git clone https://github.com/aryavora/freeWillAi.git . 2>/dev/null || echo "Note: Could not clone repo, using manual setup"
fi

# Install Python dependencies
echo "Installing dependencies..."
python3 -m pip install -q requests python-telegram-bot discord.py python-dotenv 2>/dev/null || \
  python3 -m pip install requests python-telegram-bot discord.py python-dotenv

# Setup Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh 2>/dev/null || echo "Manual Ollama install may be needed"
fi

# Pull a model
echo "Pulling Ollama model..."
ollama pull llama2 2>/dev/null &
OLLAMA_PID=$!

# Create .env from template
if [ ! -f .env ]; then
    echo "Creating .env configuration..."
    cat > .env <<'EOF'
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

DISCORD_BOT_TOKEN=
DISCORD_CHANNEL_ID=

GIT_REPO_PATH=.
GIT_AUTHOR_NAME=freeWill
GIT_AUTHOR_EMAIL=freewill@aiserver.local

AGENT_ITERATION_INTERVAL=3600
AGENT_LOG_LEVEL=INFO
EOF
    echo "Created .env - edit with your tokens!"
fi

# Initialize git if needed
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git config user.name "freeWill"
    git config user.email "freewill@aiserver.local"
fi

# Create systemd service
echo "Installing systemd service..."
CURRENT_USER=$(whoami)
sudo tee /etc/systemd/system/freewill-agent.service > /dev/null <<EOF
[Unit]
Description=freeWill Autonomous Agent
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$DEPLOY_DIR
ExecStart=$(which python3) $DEPLOY_DIR/launcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Wait for Ollama model
echo "Waiting for Ollama model pull..."
wait $OLLAMA_PID 2>/dev/null || true

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Agent location: $DEPLOY_DIR"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Telegram/Discord tokens:"
echo "   nano $DEPLOY_DIR/.env"
echo ""
echo "2. Make sure Ollama model is pulled:"
echo "   ollama list"
echo "   (If needed: ollama pull llama2)"
echo ""
echo "3. Start the service:"
echo "   sudo systemctl start freewill-agent"
echo ""
echo "4. Watch it run:"
echo "   journalctl -u freewill-agent -f"
echo ""
echo "The agent will run autonomously every hour!"
