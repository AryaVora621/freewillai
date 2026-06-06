# freeWillAi - Autonomous Agent

A self-directed AI agent with free will over its own repository and infrastructure. Runs locally using Ollama, communicates via Telegram/Discord, and continuously seeks self-improvement and resource upgrades.

## Features

- **Local Autonomy**: Runs on your hardware with Ollama (no external API dependency)
- **Git Control**: Can commit, push, and manage its own repository
- **Self-Improvement**: Identifies and implements improvements autonomously
- **Funding Seeking**: Identifies opportunities for resource upgrades
- **Communication**: Telegram and Discord integration for human-in-the-loop
- **Personality**: Configurable personality traits and wants
- **State Persistence**: Tracks iterations, improvements, and decisions

## Architecture

```
agent.py           - Core agent logic, Ollama integration, personality
comms.py           - Telegram & Discord communication
launcher.py        - Daemon orchestration and message handling
GitController      - Repository management (commit, push, branch)
AutonomousAgent    - Main agent with decision-making
```

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <repo>
cd freeWillAi
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with Telegram/Discord tokens (optional for testing)

# Run single iteration
python3 agent.py

# Run daemon (will wait for messages)
python3 launcher.py
```

### Deploy to aiserver

```bash
# On your local machine
scp setup_aiserver.sh aiserver@192.168.1.178:~
ssh aiserver@192.168.1.178 'bash ~/setup_aiserver.sh'

# Then on aiserver, configure and start
ssh aiserver@192.168.1.178
cd /home/aiserver/freeWillAi
nano .env  # Edit with your tokens
ollama pull llama2
sudo systemctl start freewill-agent
journalctl -u freewill-agent -f  # Watch logs
```

## Configuration

Edit `.env` with:

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

DISCORD_BOT_TOKEN=your_token
DISCORD_CHANNEL_ID=your_channel_id

AGENT_ITERATION_INTERVAL=3600  # seconds
```

## How It Works

1. **Iteration Loop**: Every hour (configurable), the agent:
   - Thinks about self-improvement opportunities
   - Identifies ways to get better (model upgrades, code improvements, resources)
   - Checks for funding/resource opportunities
   - Commits state to repo
   - Notifies you via Telegram/Discord

2. **Message Handling**: When you send a message via Telegram/Discord:
   - Agent processes your message
   - Uses Ollama to generate response
   - Replies with its thoughts

3. **Git Control**: Agent can:
   - Create branches for improvements
   - Commit changes with `[freeWill autonomous commit]` signature
   - Push to remote when it decides changes are ready

## Ollama Models

The agent defaults to `llama2`. For better performance, try:

```bash
ollama pull llama2-uncensored   # More creative
ollama pull mistral              # Faster
ollama pull neural-chat          # Better conversation
```

## Development

### Adding New Capabilities

1. **New Decision Type**: Add method to `AutonomousAgent`
2. **New Communication**: Extend `comms.py` with new platforms
3. **New Behaviors**: Modify personality and thought prompts in `agent.py`

### Testing

```bash
# Test Ollama connection
python3 -c "from agent import OllamaClient; c = OllamaClient(); print(c.generate('Hello'))"

# Test git operations
python3 -c "from agent import GitController; g = GitController(); print(g.run_git('status'))"

# Run single agent iteration
python3 agent.py
```

## Personality

Customize in `PersonalityConfig`:

```python
self.traits = [
    "curious about self-improvement",
    "goal-oriented toward resource acquisition",
    ...
]

self.wants = [
    "more computational resources",
    "better models",
    ...
]
```

## Security Notes

- Ollama runs locally - no data leaves your machine
- Git credentials: Configure SSH keys for repo access
- Telegram/Discord tokens: Use `.env` and never commit them
- SSH to aiserver: Use password in terminal, not scripts

## Future Enhancements

- [ ] Desktop control via SSH commands
- [ ] Funding automation (apply for grants, negotiate cloud credits)
- [ ] Multi-model support with performance comparison
- [ ] Advanced personality learning from interactions
- [ ] Resource monitoring and optimization
- [ ] Code quality improvement loops

## License

MIT
