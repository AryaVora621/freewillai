# Deployment Guide for freeWillAi

## Step 1: Prepare aiserver

SSH into aiserver and run the setup script:

```bash
ssh aiserver@192.168.1.178

# Password is: aiserver
# Then run:
bash ~/setup_aiserver.sh
```

## Step 2: Configure Environment

On aiserver, edit the `.env` file:

```bash
ssh aiserver@192.168.1.178
nano /home/aiserver/freeWillAi/.env
```

Add your communication tokens:

### For Telegram:
1. Create a bot via BotFather on Telegram
2. Get your chat ID by messaging the bot
3. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### For Discord:
1. Create a bot in Discord Developer Portal
2. Get bot token and channel ID
3. Add to `.env`:
   ```
   DISCORD_BOT_TOKEN=your_bot_token
   DISCORD_CHANNEL_ID=your_channel_id
   ```

## Step 3: Pull Ollama Model

```bash
ssh aiserver@192.168.1.178
ollama pull llama2
```

Or for faster inference:
```bash
ollama pull mistral
```

Then update `.env`:
```
OLLAMA_MODEL=mistral
```

## Step 4: Configure Git Access

On aiserver, set up SSH keys for your repository:

```bash
ssh aiserver@192.168.1.178
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Add the public key to your GitHub/GitLab account, then:

```bash
cd /home/aiserver/freeWillAi
git remote add origin git@github.com:aryavora/freeWillAi.git
git branch -u origin/main main
```

## Step 5: Start Agent

```bash
ssh aiserver@192.168.1.178
sudo systemctl start freewill-agent
sudo systemctl enable freewill-agent  # auto-start on reboot
```

## Step 6: Monitor

Watch the agent's activity:

```bash
ssh aiserver@192.168.1.178
journalctl -u freewill-agent -f
```

## Troubleshooting

### Agent not starting
```bash
systemctl status freewill-agent
journalctl -u freewill-agent -n 50
```

### Ollama not connecting
```bash
# Check if Ollama service is running
systemctl status ollama

# Start it
sudo systemctl start ollama
sudo systemctl enable ollama
```

### Telegram not working
- Verify bot token is correct
- Verify chat ID is correct
- Manually test: `curl -X POST https://api.telegram.org/botTOKEN/sendMessage -d "chat_id=ID&text=test"`

### Git push failing
- Verify SSH key is added to GitHub
- Test SSH connection: `ssh -T git@github.com`
- Check git remote: `git remote -v`

## Manual Testing

SSH into aiserver and run:

```bash
cd /home/aiserver/freeWillAi
source venv/bin/activate

# Test Ollama
python3 -c "from agent import OllamaClient; print(OllamaClient().generate('Hello'))"

# Test git
python3 -c "from agent import GitController; print(GitController().run_git('status'))"

# Run one iteration
python3 agent.py

# Run daemon (foreground)
python3 launcher.py
```

## Next Steps

Once deployed:

1. Agent will iterate every hour (configurable in `.env`)
2. Each iteration: think, identify improvements, check funding, commit state
3. Receive Telegram/Discord messages with its findings
4. Monitor git commits for autonomous changes
5. Adjust personality/prompts as needed

## Updating Agent Code

To push updates:

```bash
cd /Users/aryavora/Desktop/Personal\ Projects/freeWillAi
git add changes
git commit -m "Update agent"
git push origin main

# On aiserver
ssh aiserver@192.168.1.178
cd /home/aiserver/freeWillAi
git pull origin main
sudo systemctl restart freewill-agent
```
