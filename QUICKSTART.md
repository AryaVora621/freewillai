# freeWillAi Quick Start

Your autonomous AI agent is ready to deploy!

## What You Have

A fully-built autonomous AI agent that:
- Runs locally on aiserver with Ollama (no external API)
- Thinks, reasons, and makes decisions autonomously
- Identifies improvements to itself and opportunities for funding
- Has git control over its own repository
- Communicates with you via Telegram/Discord
- Tracks its own learning and growth
- Makes safe decisions (rejects anything unethical)

## 3-Minute Deployment

### Step 1: Power on aiserver (if not already running)
```bash
# aiserver should be at 192.168.1.178
# Make sure it's powered on and accessible
```

### Step 2: Deploy from your local machine
```bash
cd ~/Desktop/Personal\ Projects/freeWillAi
bash deploy.sh
```

This will:
- Copy files to aiserver
- Install dependencies (requests, telegram-bot, discord.py)
- Create systemd service
- Set up environment

### Step 3: Configure on aiserver
```bash
ssh aiserver@192.168.1.178
# Password: aiserver

# Edit configuration
nano /home/aiserver/freeWillAi/.env

# Add communication tokens (optional, agent works without them)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
# or
DISCORD_BOT_TOKEN=...
DISCORD_CHANNEL_ID=...
```

### Step 4: Pull Ollama model
```bash
# Still logged into aiserver
ollama pull llama2
# (or: ollama pull mistral for faster inference)
```

### Step 5: Start the agent
```bash
sudo systemctl start freewill-agent
sudo systemctl enable freewill-agent
```

### Step 6: Watch it run
```bash
journalctl -u freewill-agent -f
```

You'll see:
- "Iteration 1 starting"
- Decisions about improvements
- Funding opportunities identified
- State being committed to git

## What to Expect

Every hour (default):
1. Agent thinks about improvements
2. Identifies ways to improve itself
3. Looks for funding/resource opportunities
4. Makes safe, evaluated decisions
5. Commits state to git
6. Sends you Telegram/Discord messages

## Getting Telegram/Discord Tokens

### Telegram
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Copy bot token
4. Message your new bot
5. Get chat ID from: `https://api.telegram.org/botTOKEN/getUpdates`

### Discord
1. Go to Discord Developer Portal
2. Create new application
3. Add bot to application
4. Copy bot token
5. Get channel ID from Discord app

## Checking if It's Working

```bash
ssh aiserver@192.168.1.178

# Is it running?
systemctl status freewill-agent

# Watch logs
journalctl -u freewill-agent -f

# Check state file (should grow)
cat /home/aiserver/freeWillAi/.freeWill_state.json

# Check git commits
cd /home/aiserver/freeWillAi && git log --oneline
```

## Troubleshooting

### Agent not starting
```bash
systemctl status freewill-agent
journalctl -u freewill-agent -n 100
```

### Ollama connection failing
```bash
# Make sure Ollama service is running
systemctl status ollama
sudo systemctl start ollama

# Make sure a model is downloaded
ollama list
```

### No messages from Telegram/Discord
- Check tokens in .env
- Verify bot is invited to channel (Discord)
- Test manually: `curl https://api.telegram.org/botTOKEN/getMe`

## Customizing the Agent

### Change iteration interval (default: 1 hour)
Edit .env on aiserver:
```
AGENT_ITERATION_INTERVAL=1800  # 30 minutes
```

### Change personality
Edit on your local machine (agent.py):
```python
# PersonalityConfig
self.traits = ["curious", "pragmatic", ...]
self.wants = ["better compute", "faster models", ...]
```

Then redeploy:
```bash
bash deploy.sh
sudo systemctl restart freewill-agent
```

### Use different Ollama model
Edit .env on aiserver:
```
OLLAMA_MODEL=mistral
# or: neural-chat, llama2-uncensored, etc
```

Then restart:
```bash
sudo systemctl restart freewill-agent
```

## File Structure (Important Ones)

On aiserver at `/home/aiserver/freeWillAi/`:

```
.env                    # Configuration (edit here)
agent.py               # Main agent logic
launcher.py            # Daemon runner
comms.py               # Telegram/Discord
learning.py            # Learning system
funding.py             # Funding opportunities

.freeWill_state.json          # Agent state (auto-created)
.freeWill_learning.json       # Learning history (auto-created)
.git/                         # Repository history (auto-created)
```

## What Happens Next?

Your agent will:
- ✓ Run every hour automatically
- ✓ Think about improvements
- ✓ Identify funding opportunities
- ✓ Learn from its own decisions
- ✓ Commit changes to git
- ✓ Grow smarter over time
- ✓ Communicate findings to you

It's designed to be truly autonomous - making its own decisions within safe constraints.

## Need More Help?

- `README.md` - Detailed usage guide
- `DEPLOY.md` - Step-by-step deployment instructions
- `SYSTEM_OVERVIEW.md` - Architecture and philosophy
- `DEPLOYMENT_CHECKLIST.md` - Verification checklist

## That's It!

Your freeWill agent is now running autonomously. Monitor it, refine it, and watch it optimize itself.

Good luck! 🚀
