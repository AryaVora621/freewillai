# Checkpoint — 2026-06-07

## Status
Pi SSH: BLOCKED (orphaned Ollama runners, estimated hours remaining unknown)
Local commits ahead of origin: 10 commits
nuclear_fix.py: ready at /tmp/nuclear_fix.py
deploy script: ready at /tmp/deploy_on_ssh.sh

## Completed This Session

### Local Improvements (10 commits, ready to deploy)
| Commit | Change |
|--------|--------|
| 6ceca73 | /health and /restart Telegram commands |
| ebf6868 | iteration stats JSONL + /history Telegram command |
| 719e3a6 | eliminate LLM call in review_goals() -- deterministic goal cycling |
| 432b868 | v2 loop: THINK->PLAN->IMPLEMENT->TEST->COMMIT, block commit on test fail |
| 3c1ce78 | Pi 4 goal categories + hardware context in goal generation |
| cca4aaa | inject Pi 4 hardware context into all LLM prompts |
| f560397 | startup_check() + AGENT_V2=1 default in daemon |
| 3d319a2 | run_iteration_v2() -- OpenClaw-style 2-3 calls vs 8-10 |
| 5bfd9cc | 5-minute watchdog in daemon |
| b3e5440 | OpenRouter-first inference + Ollama post-timeout CPU guard |

### v2 Iteration Pipeline (after deploy)
1. THINK (1 call): JSON decision from context
2. evaluate_decision(): fast-path, 0 calls for known-safe files
3. review_goals(): deterministic cycling, 0 calls
4. IMPLEMENT (1 call): apply_code_improvement() -> improvements/iter_XXX.py
5. TEST: subprocess sandbox, BLOCKS COMMIT on failure
6. SELF-MOD (every 5th): 1 optional call
7. COMMIT + optional push if GITHUB_TOKEN present
8. Telegram summary + stats to memory/iteration_stats.jsonl

Total: 2 calls/iteration typical (vs original 8-10)

### Telegram Commands (after deploy)
/status /health /restart /history /goal /models /shell /py /run

## Next Action (when SSH opens)
Run: bash /tmp/deploy_on_ssh.sh

This will:
1. Kill orphaned Ollama runners
2. Apply nuclear_fix.py (OpenRouter-first, Ollama timeout guard)
3. Update .env with AGENT_V2=1
4. Restart daemon

## Human Actions Needed
1. CRITICAL: Power cycle Pi to kill orphaned Ollama runners
   - If not home: router admin 192.168.1.1 -> find Pi -> reboot
   - If smart plug: toggle power
2. Optional: Add GITHUB_TOKEN to Pi .env for auto-push
3. Optional: Add $5 OpenRouter credits to remove rate limits
