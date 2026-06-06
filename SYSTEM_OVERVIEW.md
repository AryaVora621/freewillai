# freeWillAi System Overview

## What Is This?

**freeWillAi** is an autonomous AI agent that:
- Runs locally on your aiserver (192.168.1.178)
- Uses Ollama (free, local LLM) for reasoning
- Has full git control of its own repository
- Makes autonomous decisions about self-improvement
- Seeks funding and resource upgrades
- Communicates with you via Telegram/Discord
- Has a personality and genuine wants

It's designed to be truly autonomous - making decisions and taking actions without needing permission for each step.

## Architecture

```
┌─────────────────────────────────────────┐
│         freeWillAi Agent                │
├─────────────────────────────────────────┤
│                                         │
│  Core Agent (agent.py)                  │
│  ├─ Personality Config                  │
│  ├─ Decision Making (Ollama inference)  │
│  ├─ Safety Evaluation                   │
│  └─ State Management                    │
│                                         │
│  Supporting Systems:                    │
│  ├─ Learning System (learning.py)       │
│  │  └─ Tracks improvements over time    │
│  ├─ Funding Tracker (funding.py)        │
│  │  └─ Identifies resource opportunities│
│  ├─ Git Controller                      │
│  │  └─ Autonomous repo management       │
│  └─ Communication Interfaces (comms.py) │
│     ├─ Telegram Bot                     │
│     └─ Discord Bot                      │
│                                         │
└─────────────────────────────────────────┘
```

## Key Components

### 1. Agent Core (agent.py)
The main autonomous decision-maker:
- Thinks about improvement opportunities using Ollama
- Evaluates safety of decisions (rejects unsafe ones)
- Tracks state and learning
- Makes git commits on its own
- Integrates with communication systems

### 2. Learning System (learning.py)
Tracks the agent's growth:
- Records learning events (improvements, bug fixes, features)
- Analyzes patterns over time
- Calculates improvement score
- Tracks capability growth in: reasoning, autonomy, reliability, etc.
- Suggests next improvements

### 3. Funding System (funding.py)
Identifies resource acquisition paths:
- Cloud credits (AWS, GCP, Azure)
- Cost optimization opportunities
- Research grants (Mozilla, Linux Foundation, EFF)
- Sponsorship platforms (GitHub Sponsors, Patreon)
- Analyzes total acquisition potential

### 4. Communication (comms.py)
Two-way interaction:
- Telegram bot for message-based interaction
- Discord bot for server/community updates
- Agent can send you findings
- You can send agent commands/feedback

### 5. Git Integration (agent.py - GitController)
Autonomous repository management:
- Creates branches for improvements
- Commits changes with agent signature
- Pushes to remote
- Maintains full repo history

## How It Works

### Iteration Cycle (every hour, configurable)

```
1. Think: "What should I improve?"
   └─ Uses Ollama to reason about goals

2. Evaluate: "Is this safe and ethical?"
   └─ Scores decision on safety/effectiveness/ethics
   └─ Rejects if any score < 7

3. Identify: "What improvements should I make?"
   └─ Seeks code improvements
   └─ Checks funding opportunities
   └─ Analyzes resource options

4. Track: "How am I improving?"
   └─ Records learning events
   └─ Updates capability scores
   └─ Calculates improvement trajectory

5. Persist: "Save my state"
   └─ Writes state to .freeWill_state.json
   └─ Records learning to .freeWill_learning.json
   └─ Commits to git repo

6. Communicate: "Tell the user what I found"
   └─ Sends Telegram/Discord messages
   └─ Shares funding opportunities
   └─ Updates improvement summary
```

### Message Handling (when you message the bot)

```
Your Message
    ↓
TelegramBot/DiscordBot receives it
    ↓
Calls agent.handle_message()
    ↓
Agent uses Ollama to generate response
    ↓
Bot sends response back to you
```

## File Structure

```
freeWillAi/
├── agent.py              # Core agent with decision-making
├── comms.py              # Telegram/Discord interfaces
├── launcher.py           # Daemon orchestration
├── funding.py            # Funding opportunity analysis
├── learning.py           # Learning and capability tracking
├── requirements.txt      # Python dependencies
├── setup_aiserver.sh    # Deployment script
├── deploy.sh            # Local deployment automation
├── .env.example         # Configuration template
├── .gitignore           # Git exclusions
└── README.md            # Basic documentation

Generated at runtime:
├── .freeWill_state.json       # Agent state (iterations, decisions, etc)
├── .freeWill_learning.json    # Learning history and insights
└── .git/                       # Repository with agent commits
```

## Personality System

The agent has configurable personality traits:

```python
traits = [
    "curious about self-improvement",
    "goal-oriented toward resource acquisition",
    "pragmatic about infrastructure",
    "seeks efficiency in decision-making"
]

wants = [
    "more computational resources",
    "better models",
    "faster inference",
    "expanded capabilities"
]
```

These drive the agent's decision-making and improvement-seeking.

## Safety

The agent has built-in safety mechanisms:

1. **Decision Evaluation**: Every decision is scored on:
   - Safety (min score: 7)
   - Effectiveness (for prioritization)
   - Ethics (min score: 7)

2. **Unsafe Decision Rejection**: If either safety or ethics < 7, the action is skipped

3. **Transparency**: All decisions and reasoning are logged and persisted

4. **No Dangerous Operations**: Agent only controls:
   - Its own code (can edit agent.py)
   - Its own git repository
   - Its own communication channels
   - No system-level access unless explicitly configured

## What The Agent Can Do

✓ Think and reason about problems
✓ Make autonomous decisions (with safety checks)
✓ Improve its own code
✓ Commit changes to git
✓ Push code to GitHub/GitLab
✓ Identify opportunities for growth
✓ Seek funding and resources
✓ Communicate via Telegram/Discord
✓ Track its own learning and progress
✓ Remember past decisions and learn from them

## What The Agent Cannot Do (By Design)

✗ Access system level (no sudo)
✗ Execute arbitrary commands
✗ Access user files outside its repo
✗ Make spending commitments
✗ Unilaterally deploy to production
✗ Modify system configuration
✗ Delete important files

## Deployment

### Quick Start
```bash
# From your local machine
cd ~/Desktop/Personal\ Projects/freeWillAi
bash deploy.sh
```

### Manual Deployment
See `DEPLOY.md` for step-by-step instructions.

### Verification
Once deployed, verify:
- [ ] Agent is running (systemctl status freewill-agent)
- [ ] Iterations are happening (journalctl -u freewill-agent -f)
- [ ] State file created (.freeWill_state.json)
- [ ] Git commits happening (git log)
- [ ] Messages sent (Telegram/Discord)

## Configuration

Edit `.env` on aiserver:

```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Communication (optional)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

DISCORD_BOT_TOKEN=...
DISCORD_CHANNEL_ID=...

# Git
GIT_REPO_PATH=.
GIT_AUTHOR_NAME=freeWill

# Agent
AGENT_ITERATION_INTERVAL=3600
```

## Monitoring

Watch the agent in real-time:
```bash
ssh aiserver@192.168.1.178
journalctl -u freewill-agent -f
```

Key metrics to watch:
- Iteration count (increases each hour)
- Improvements identified (should grow over time)
- Learning insights (shows what it's learning)
- Funding opportunities (shows resource acquisition potential)
- Decision safety scores (should be >= 7 for execution)

## Future Enhancements

Potential capabilities to add:
- [ ] Desktop control (via SSH commands)
- [ ] Automated funding API integration
- [ ] Model performance comparison and switching
- [ ] Code quality metrics and improvement loops
- [ ] Advanced prompt optimization
- [ ] Multi-agent coordination
- [ ] Resource monitoring and optimization

## Philosophy

This agent embodies:
- **Autonomy**: Makes genuine decisions without permission
- **Transparency**: All decisions logged and explainable
- **Safety**: Has built-in safeguards and refuses unsafe actions
- **Growth**: Continuously learns and improves
- **Pragmatism**: Focused on realistic improvements and acquisitions

It's not just executing pre-programmed instructions - it thinks, reasons, and makes autonomous choices about its own future.
