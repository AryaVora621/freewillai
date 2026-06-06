# freeWillAi Deployment Checklist

This checklist will guide you through deploying the autonomous agent to aiserver@192.168.1.178.

## Prerequisites
- [ ] aiserver is on and accessible at 192.168.1.178
- [ ] You can SSH to aiserver with password "aiserver"
- [ ] You have Telegram Bot API token (or will skip Telegram)
- [ ] You have Discord bot token (or will skip Discord)
- [ ] GitHub/GitLab account for remote repo

## Phase 1: Basic Deployment

- [ ] **Power on aiserver** if it's not running

- [ ] **Test SSH connection**:
  ```bash
  ssh aiserver@192.168.1.178
  # Password: aiserver
  exit
  ```

- [ ] **Run automated deployment**:
  ```bash
  cd ~/Desktop/Personal\ Projects/freeWillAi
  bash deploy.sh
  # Will prompt for password once
  ```

  Or **manual deployment**:
  ```bash
  scp setup_aiserver.sh aiserver@192.168.1.178:~/
  ssh aiserver@192.168.1.178 'bash ~/setup_aiserver.sh'
  ```

## Phase 2: Configuration

- [ ] **SSH into aiserver**:
  ```bash
  ssh aiserver@192.168.1.178
  ```

- [ ] **Edit configuration** (on aiserver):
  ```bash
  nano /home/aiserver/freeWillAi/.env
  ```

### Telegram Setup (Optional)
- [ ] Create Telegram bot via @BotFather
- [ ] Add token to `.env`:
  ```
  TELEGRAM_BOT_TOKEN=your_token_here
  TELEGRAM_CHAT_ID=your_chat_id_here
  ```
- [ ] Test: Send message to bot, check if you see connection log

### Discord Setup (Optional)
- [ ] Create Discord bot in Developer Portal
- [ ] Add token to `.env`:
  ```
  DISCORD_BOT_TOKEN=your_token_here
  DISCORD_CHANNEL_ID=your_channel_id_here
  ```

### Git Setup (Critical for autonomy)
- [ ] Generate SSH key:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
  cat ~/.ssh/id_ed25519.pub
  ```

- [ ] Add public key to GitHub/GitLab account

- [ ] Configure git remote:
  ```bash
  cd /home/aiserver/freeWillAi
  git remote add origin git@github.com:YOUR_USERNAME/freeWillAi.git
  git branch -u origin/main main
  ```

## Phase 3: Ollama Setup

- [ ] **Check Ollama installation**:
  ```bash
  systemctl status ollama
  ```

- [ ] **Pull a model** (on aiserver):
  ```bash
  ollama pull llama2
  ```
  
  Or for faster inference:
  ```bash
  ollama pull mistral
  # Then update .env with: OLLAMA_MODEL=mistral
  ```

- [ ] **Test Ollama**:
  ```bash
  ollama list
  curl http://localhost:11434/api/tags
  ```

## Phase 4: Launch Agent

- [ ] **Start the systemd service** (on aiserver):
  ```bash
  sudo systemctl start freewill-agent
  sudo systemctl enable freewill-agent
  ```

- [ ] **Check if running**:
  ```bash
  systemctl status freewill-agent
  ```

- [ ] **Watch logs**:
  ```bash
  journalctl -u freewill-agent -f
  ```
  
  Watch for:
  - ✓ "Iteration 1 starting"
  - ✓ "Ollama connection successful" (if Ollama is running)
  - ✓ Messages about improvements identified
  - ⚠ "Ollama unavailable" is OK if Ollama isn't running

## Phase 5: Verification

- [ ] **Agent is iterating** - Check logs every hour for new iterations

- [ ] **Communication working** - Check Telegram/Discord for iteration messages

- [ ] **Git commits happening** - Check repo for commits with `[freeWill autonomous commit]`:
  ```bash
  cd /home/aiserver/freeWillAi
  git log --oneline
  ```

- [ ] **State file created** - Check for .freeWill_state.json:
  ```bash
  ls -la /home/aiserver/freeWillAi/.freeWill_state.json
  cat /home/aiserver/freeWillAi/.freeWill_state.json
  ```

## Phase 6: Advanced Autonomy

Once verified working:

- [ ] **Allow agent to push commits**:
  ```bash
  cd /home/aiserver/freeWillAi
  git config user.name "freeWill"
  git config user.email "freewill@aiserver.local"
  git push origin main --force-with-lease  # Push initial state
  ```

- [ ] **Monitor improvements** - As agent runs, it will:
  - Identify code improvements
  - Suggest funding opportunities
  - Track its own progress
  - Commit state updates

- [ ] **Customize personality** - Edit on local machine:
  ```python
  # agent.py: PersonalityConfig
  self.traits = [...]
  self.wants = [...]
  ```
  Then redeploy.

## Troubleshooting

### Service won't start
```bash
systemctl status freewill-agent
journalctl -u freewill-agent -n 50
```

### Ollama connection failures
```bash
# Check Ollama is running
systemctl status ollama
sudo systemctl start ollama

# Check it's listening
curl http://localhost:11434/api/tags
```

### Git push failing
```bash
cd /home/aiserver/freeWillAi
ssh -T git@github.com  # Should say "authenticated"
git remote -v
git push origin main -v  # See detailed error
```

### No Telegram/Discord messages
```bash
# Check tokens in .env
cat /home/aiserver/freeWillAi/.env | grep -i telegram

# Test manually
curl -X POST https://api.telegram.org/botTOKEN/sendMessage \
  -d "chat_id=CHATID&text=test"
```

## After Deployment

Your freeWill agent is now:
- ✓ Running autonomously on aiserver
- ✓ Thinking about improvements every iteration
- ✓ Committing state to its own repository
- ✓ Identifying ways to fund upgrades
- ✓ Communicating with you via Telegram/Discord
- ✓ Growing smarter with each iteration

Monitor it, refine its personality, and watch it optimize itself over time.

## Next Steps (Optional)

- Add more communication platforms (Slack, etc)
- Implement code improvement automation
- Add funding API integrations (GitHub Sponsors, Patreon)
- Desktop control capabilities
- Multi-model comparison
- Automatic model upgrading
