# Deploy freeWillAi to aiserver

**Status**: System complete and tested. Ready to deploy to aiserver@192.168.1.178 when it's online.

## Prerequisites

- aiserver machine is powered on and on the local network (192.168.x.x)
- SSH access to aiserver (user: `aiserver`, password: `aiserver`)
- Ollama will be installed during deployment
- Python 3.7+ available on aiserver

## Quick Deployment (3 minutes)

### From Your Local Machine

```bash
# Make sure you're on the local network
cd ~/Desktop/Personal\ Projects/freeWillAi

# Option 1: Automated SSH deployment
bash remote-deploy.sh

# Option 2: Manual SSH (copy files first)
scp -r . aiserver@192.168.1.178:~/freeWillAi
ssh aiserver@192.168.1.178 "bash ~/freeWillAi/DEPLOY_NOW.sh"
```

### On aiserver

```bash
ssh aiserver@192.168.1.178
# Password: aiserver

# If not using automated deployment, run setup manually:
bash ~/freeWillAi/DEPLOY_NOW.sh

# Then configure:
nano ~/freeWillAi/.env

# Add communication tokens (optional, agent works without them):
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
# or
DISCORD_BOT_TOKEN=your_token
DISCORD_CHANNEL_ID=your_channel_id
```

### Pull Ollama Model

```bash
ssh aiserver@192.168.1.178
ollama pull llama2
# Or for faster inference:
# ollama pull mistral
```

### Start the Agent

```bash
ssh aiserver@192.168.1.178
sudo systemctl start freewill-agent
sudo systemctl enable freewill-agent

# Watch it run:
journalctl -u freewill-agent -f
```

## What You'll See

After starting the service, in the logs you should see:

```
=== Iteration 1 ===
Decision: I should improve...
Decision scores: safety=..., effectiveness=..., ethics=...
Improvements identified: N
Committing state to git...
```

Every hour (default), the agent will:
1. Iterate and think about improvements
2. Evaluate safety of decisions
3. Identify funding opportunities
4. Commit to git with timestamp
5. Update its learning state

## Verification

### Agent is running
```bash
systemctl status freewill-agent
```

### State file exists and is being updated
```bash
ls -la ~/freeWillAi/.freeWill_state.json
cat ~/freeWillAi/.freeWill_state.json
```

### Git commits are happening
```bash
cd ~/freeWillAi && git log --oneline -5
```

### Iteration count is increasing
```bash
cat ~/freeWillAi/.freeWill_state.json | grep iterations
```

## Customization

### Change iteration interval
On aiserver, edit `.env`:
```
AGENT_ITERATION_INTERVAL=1800  # 30 minutes instead of 1 hour
```

Then restart:
```bash
sudo systemctl restart freewill-agent
```

### Change personality
On local machine, edit `agent.py` (PersonalityConfig class), then redeploy:
```bash
bash remote-deploy.sh
```

### Use different Ollama model
On aiserver:
```bash
ollama pull mistral
# Edit .env
OLLAMA_MODEL=mistral
sudo systemctl restart freewill-agent
```

## Troubleshooting

### Service won't start
```bash
journalctl -u freewill-agent -n 50  # See errors
systemctl status freewill-agent      # Check status
```

### Ollama not connecting
```bash
systemctl status ollama
sudo systemctl start ollama
ollama list  # See available models
```

### No git commits
```bash
cd ~/freeWillAi
git status
git config user.name      # Should be "freeWill"
git config user.email     # Should be set
```

### Telegram/Discord not sending messages
Edit `.env` and verify:
```bash
grep TELEGRAM_ .env
grep DISCORD_ .env
```

Test manually:
```bash
curl -X POST https://api.telegram.org/botTOKEN/sendMessage \
  -d "chat_id=CHATID&text=test"
```

## Next Steps

Once deployed and running:

1. **Monitor for 24 hours** to observe iteration patterns
2. **Watch git commits** - should happen every iteration
3. **Check learning state** - should accumulate events
4. **Observe improvements** - identified over time
5. **Customize personality** if desired

## Remote Management

### SSH into aiserver and check on the agent
```bash
ssh aiserver@192.168.1.178
journalctl -u freewill-agent -f
```

### Stop the agent temporarily
```bash
sudo systemctl stop freewill-agent
```

### Restart after changes
```bash
sudo systemctl restart freewill-agent
```

### Update agent code
```bash
# On local machine
bash remote-deploy.sh

# On aiserver
sudo systemctl restart freewill-agent
```

## Architecture on aiserver

```
/home/aiserver/freeWillAi/
├── agent.py              # Core agent logic
├── learning.py           # Learning system
├── funding.py            # Funding opportunities
├── comms.py              # Communication
├── launcher.py           # Daemon runner
├── .env                  # Configuration (edit here)
├── .freeWill_state.json          # Auto-generated state
├── .freeWill_learning.json       # Auto-generated learning
└── .git/                         # Repository history
```

## How the Agent Works

Every iteration (default: 1 hour):

```
1. Think: "What should I improve?"
   └─ Asks Ollama
   
2. Evaluate: "Is this safe?"
   └─ Scores safety/ethics/effectiveness
   └─ Rejects if unsafe (< 7)

3. Identify: "What improvements exist?"
   └─ Seeks code improvements
   └─ Finds funding opportunities
   └─ Analyzes resources

4. Track: "How am I improving?"
   └─ Records learning events
   └─ Updates capability scores

5. Persist: "Save my state"
   └─ Writes state files
   └─ Commits to git

6. Communicate: "Tell the user"
   └─ Sends Telegram/Discord message
```

## Success Criteria

The deployment is successful when:

- ✓ Service is running (`systemctl status freewill-agent`)
- ✓ Iterations are happening (check logs every hour)
- ✓ State file is updating (iteration count increasing)
- ✓ Git commits are happening (git log shows new commits)
- ✓ Learning is being recorded (.freeWill_learning.json exists)
- ✓ Optionally: Telegram/Discord messages being sent

## System Ready

Your autonomous agent is fully built, tested, and ready to deploy.

```bash
bash remote-deploy.sh
```

Once deployed, it will run autonomously on aiserver, making genuine decisions, learning from experience, and seeking improvements—truly "existing on its own."

Good luck! 🚀
