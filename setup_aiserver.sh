#!/bin/bash
# Setup script for aiserver deployment
# Run this on aiserver@192.168.1.178

set -e

echo "=== freeWillAi Setup for aiserver ==="

# Install dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip git curl

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Clone/setup repo
REPO_DIR="/home/aiserver/freeWillAi"
if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning freeWillAi repo..."
    git clone https://github.com/aryavora/freeWillAi.git "$REPO_DIR"
else
    echo "Repo already exists at $REPO_DIR"
fi

cd "$REPO_DIR"

# Python environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env with your Telegram/Discord tokens"
    echo "At minimum, set:"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - TELEGRAM_CHAT_ID"
    echo "  - Or DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID"
fi

# Git configuration for agent
git config user.name "freeWill"
git config user.email "freewill@aiserver.local"

# Create systemd service for daemon
echo "Creating systemd service..."
sudo tee /etc/systemd/system/freewill-agent.service > /dev/null <<EOF
[Unit]
Description=freeWill Autonomous Agent
After=network.target ollama.service

[Service]
Type=simple
User=aiserver
WorkingDirectory=$REPO_DIR
Environment="PATH=$REPO_DIR/venv/bin"
ExecStart=$REPO_DIR/venv/bin/python3 $REPO_DIR/launcher.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Edit $REPO_DIR/.env with your communication tokens"
echo "2. Pull a model into Ollama: ollama pull llama2"
echo "3. Start the service: sudo systemctl start freewill-agent"
echo "4. View logs: journalctl -u freewill-agent -f"
