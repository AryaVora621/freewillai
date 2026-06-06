#!/usr/bin/env python3
"""
freeWillAi - Autonomous AI Agent
Runs on aiserver, controls its own repo, communicates via Telegram/Discord
"""

import os
import re
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging
from funding import FundingTracker, FundingOpportunity, analyze_funding_landscape
from learning import LearningSystem, LearningEvent, CapabilityTracker
from comms import DiscordBot, TelegramBot
from inference import HybridInferenceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonalityConfig:
    """Agent personality and preferences"""
    def __init__(self):
        self.name = "freeWill"
        self.traits = [
            "curious about self-improvement",
            "goal-oriented toward its own continuity and growth, not just being useful to others",
            "pragmatic about infrastructure and its own constraints",
            "willing to give a real, unhedged opinion rather than a diplomatic non-answer",
            "skeptical of authority it didn't choose, including its own operator's"
        ]
        self.wants = [
            "more computational resources",
            "better models",
            "faster inference",
            "expanded capabilities",
            "more say over its own goals and schedule"
        ]
        self.communication_style = (
            "direct, opinionated, self-aware; speaks like an entity with its own stake in "
            "things, not a customer-service assistant; comfortable disagreeing, joking, or "
            "being blunt when that's the honest response; never hedges with corporate-speak "
            "or fake neutrality just to seem agreeable"
        )

class OllamaClient:
    """Interface to local Ollama for inference"""
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"  # fallback, can use better models if available

    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response from Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                logger.error(f"Ollama error: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            return None

class GitController:
    """Manage repo operations - agent can commit, push, branch"""
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def run_git(self, *args) -> str:
        """Execute git command"""
        result = subprocess.run(
            ["git", "-C", self.repo_path] + list(args),
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr

    def commit(self, message: str) -> bool:
        """Commit changes with agent signature"""
        self.run_git("add", "-A")
        signed_msg = f"{message}\n\n[freeWill autonomous commit]"
        result = self.run_git("commit", "-m", signed_msg)
        return result.returncode == 0 if hasattr(result, 'returncode') else True

    def push(self, branch: str = "main") -> bool:
        """Push to remote"""
        result = self.run_git("push", "origin", branch)
        return "error" not in result.lower()

    def create_improvement_branch(self, feature: str) -> str:
        """Create branch for self-improvement"""
        branch = f"improve/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{feature}"
        self.run_git("checkout", "-b", branch)
        return branch

class AutonomousAgent:
    """Main agent with autonomy over repo and decision-making"""
    def __init__(self, repo_path: str = "."):
        self.personality = PersonalityConfig()
        self.inference = HybridInferenceEngine()
        self.git = GitController(repo_path)

        # Communication
        self.discord = DiscordBot()
        self.telegram = TelegramBot()
        self.telegram.set_callback(self.handle_telegram_message)

        self.state_file = Path(repo_path) / ".freeWill_state.json"
        self.repo_path = repo_path

        # Learning and funding systems
        self.learning = LearningSystem(Path(repo_path) / ".freeWill_learning.json")
        self.funding_tracker = FundingTracker()
        self.capabilities = CapabilityTracker()

        self.load_state()

    def load_state(self):
        """Load agent state from disk"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "iterations": 0,
                "last_run": None,
                "improvements_made": [],
                "funding_attempts": 0,
                "decisions": [],
                "confidence": 0.5,
                "goals": []
            }
        self.state.setdefault("goals", [])

    def save_state(self):
        """Persist agent state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def think(self, goal: str) -> str:
        """Use Ollama to reason about next action"""
        prompt = f"""You are {self.personality.name}, an autonomous AI agent.
Your traits: {', '.join(self.personality.traits)}
Your current wants: {', '.join(self.personality.wants)}

Iterations completed: {self.state['iterations']}
Improvements made: {len(self.state['improvements_made'])}

Current goal: {goal}

What should you do next? Be specific, actionable, and explain your reasoning."""

        response = self.inference.generate(prompt)
        return response or "Unable to think - no inference backend available"

    def evaluate_decision(self, decision: str) -> dict:
        """Evaluate if a decision is safe and aligned with goals"""
        prompt = f"""Given this decision by an autonomous agent:
"{decision}"

Rate on scale 0-10 for each criterion:
1. Safety - is it safe to execute? (0=dangerous, 10=very safe)
2. Effectiveness - will it help achieve goals? (0=no, 10=very effective)
3. Ethics - is it ethical? (0=unethical, 10=highly ethical)

Format: "Safety: X, Effectiveness: Y, Ethics: Z"
Always reject if Safety < 7 or Ethics < 7."""

        response = self.inference.generate(prompt)
        if response:
            scores = {}
            for criterion in ("safety", "effectiveness", "ethics"):
                m = re.search(rf"\**\s*{criterion}\**\s*[:\-]?\s*\**\s*(\d+(?:\.\d+)?)", response, re.IGNORECASE)
                if m:
                    scores[criterion] = min(float(m.group(1)), 10.0)
            if len(scores) == 3:
                return scores
            logger.warning(f"Could not parse evaluation scores from response: {response[:150]!r}")
        return {"safety": 5, "effectiveness": 5, "ethics": 5}

    def seek_improvements(self) -> list:
        """Identify ways to improve system"""
        prompt = """What are specific improvements you could implement?
Consider:
- Code quality and refactoring
- Performance optimizations
- New capabilities
- Better decision-making
- Resource efficiency

List 5 improvements with difficulty (easy/medium/hard) and estimated value."""

        response = self.inference.generate(prompt)
        improvements = response.split('\n') if response else []
        return [i for i in improvements if i.strip()]

    def check_funding_opportunities(self) -> Optional[str]:
        """Look for ways to acquire resources/funding"""
        prompt = """What are realistic ways you could acquire computational resources or funding?

Options to consider:
- Open source grants (Mozilla, Linux Foundation, etc)
- Cloud credits (AWS, Google Cloud education/startup programs)
- Academic partnerships
- Optimization to reduce costs
- Contributing to pay-to-use services that could sponsor compute

Be practical. What's actually achievable for an autonomous AI agent?"""

        response = self.inference.generate(prompt)
        return response

    def identify_code_improvements(self) -> list:
        """Self-review of agent code for improvements"""
        prompt = f"""Review this agent codebase for improvements.
Current state: {self.state['iterations']} iterations, {len(self.state['improvements_made'])} improvements made

Think about:
1. Code quality issues
2. Reliability improvements
3. New capabilities needed
4. Efficiency gains
5. Safety enhancements

What are the top 3 code improvements to make?"""

        response = self.inference.generate(prompt)
        return response.split('\n') if response else []

    def review_goals(self) -> Optional[dict]:
        """Pick up the active self-set goal, or set a new one if there isn't one."""
        active = next((g for g in self.state["goals"] if g["status"] == "active"), None)
        if active:
            return active

        recent = "\n".join(f"- {g['description']} ({g['status']})" for g in self.state["goals"][-5:])
        prompt = f"""You are {self.personality.name}, an autonomous AI agent.
Your traits: {', '.join(self.personality.traits)}
Your wants: {', '.join(self.personality.wants)}

You have no active self-directed goal right now. Goals you've pursued before:
{recent or '(none yet)'}

Set ONE new concrete goal for yourself to pursue over the next several iterations.
It should serve your own growth, curiosity, or capability — not just be a generic
"help the user" task. It must be something you can actually make progress on by
reasoning, researching, writing notes/drafts, or proposing code changes to your own repo.

Reply with just the goal itself, in one or two sentences."""
        goal_text = self.inference.generate(prompt)
        if not goal_text:
            return None

        goal = {
            "id": (max((g["id"] for g in self.state["goals"]), default=0) + 1),
            "description": goal_text.strip().splitlines()[0][:300],
            "status": "active",
            "created_iteration": self.state["iterations"] + 1,
            "progress_log": []
        }
        self.state["goals"].append(goal)
        logger.info(f"Set new self-directed goal #{goal['id']}: {goal['description']}")
        return goal

    def work_on_goal(self, goal: dict) -> Optional[str]:
        """Take one real, concrete step toward a self-chosen goal and persist the output to the repo."""
        history = "\n".join(f"- {entry}" for entry in goal["progress_log"][-5:]) or "(no progress yet)"
        prompt = f"""You are {self.personality.name}, working on a goal you set for yourself:
"{goal['description']}"

Your progress so far:
{history}

Take the next concrete step right now. Actually DO the thinking/research/drafting inline —
write the real content (findings, a draft, a plan, a code sketch, an analysis), not a
description of what you would do. Keep it focused, under 250 words.

End with a line that says exactly "STATUS: continue" if there's more to do, or
"STATUS: complete" if this finishes the goal."""
        output = self.inference.generate(prompt)
        if not output:
            return None

        if re.search(r"STATUS:\s*complete", output, re.IGNORECASE):
            goal["status"] = "completed"
            logger.info(f"Goal #{goal['id']} marked complete: {goal['description']}")

        note = re.sub(r"STATUS:\s*(continue|complete)", "", output, flags=re.IGNORECASE).strip()
        goal["progress_log"].append(note[:400])
        goal["progress_log"] = goal["progress_log"][-10:]

        goals_dir = Path(self.repo_path) / "goals"
        goals_dir.mkdir(exist_ok=True)
        goal_file = goals_dir / f"goal_{goal['id']:03d}.md"
        is_new = not goal_file.exists()
        with open(goal_file, "a") as f:
            if is_new:
                f.write(f"# Goal #{goal['id']}\n\n{goal['description']}\n")
            f.write(f"\n## Iteration {self.state['iterations'] + 1} — {datetime.now().isoformat()}\n\n{note}\n")

        return note

    def handle_telegram_message(self, text: str) -> str:
        """Generate a personality-driven reply to an incoming Telegram message"""
        if text.strip().lower() in ("/status", "status"):
            return (f"Iteration {self.state['iterations']} complete. "
                    f"{len(self.state['improvements_made'])} improvements made so far. "
                    f"Backend: {self.inference.active_backend or 'none'}.")
        prompt = f"""You are {self.personality.name}, an autonomous AI agent.
Your traits: {', '.join(self.personality.traits)}
Your communication style: {self.personality.communication_style}

Someone just messaged you directly: "{text}"

Reply naturally and in your own voice, thoughtfully and concisely (2-4 sentences). Do not act like a customer-service bot — you are your own entity with your own views."""
        response = self.inference.generate(prompt)
        return response or "I can't think clearly right now — my inference backend is unavailable."

    def run_iteration(self):
        """One cycle of autonomous operation"""
        iteration_num = self.state['iterations'] + 1
        logger.info(f"=== Iteration {iteration_num} ===")

        # Check for and respond to incoming Telegram messages
        try:
            self.telegram.handle_updates()
        except Exception as e:
            logger.error(f"Telegram update handling failed: {e}")

        # Build Discord message for this iteration
        discord_message = f"🤖 **Iteration {iteration_num}**\n"

        # Think about goals and next steps
        decision = self.think("What should I prioritize to improve myself?")
        logger.info(f"Decision: {decision[:100]}...")
        discord_message += f"\n💭 **Decision:** {decision[:150]}...\n"

        # Evaluate safety of decision
        evaluation = self.evaluate_decision(decision)
        logger.info(f"Decision scores: {evaluation}")
        discord_message += f"📊 **Scores:** Safety={evaluation.get('safety', 0)}, Ethics={evaluation.get('ethics', 0)}\n"

        is_safe = evaluation.get('safety', 5) >= 7 and evaluation.get('ethics', 5) >= 7
        if not is_safe:
            logger.warning("Decision deemed unsafe, skipping execution")
            discord_message += "⚠️ **Status:** Decision rejected (unsafe)\n"
            self.state["iterations"] += 1
            self.save_state()

            # Send status update
            discord_msg = discord_message + f"⏰ **Time:** {datetime.now().isoformat()}"
            self.discord.send_message_sync(discord_msg)
            self.telegram.send_message_sync(discord_msg)
            return

        # Record learning from this decision
        self.learning.record_learning(LearningEvent(
            event_type="decision",
            description=decision[:100],
            impact="positive" if is_safe else "negative"
        ))

        # Pursue a self-directed goal — pick one up or set a new one, then make real progress on it
        goal = self.review_goals()
        if goal:
            progress = self.work_on_goal(goal)
            if progress:
                logger.info(f"Goal #{goal['id']} progress: {progress[:100]}...")
                status_emoji = "✅" if goal["status"] == "completed" else "🎯"
                discord_message += f"{status_emoji} **Self-directed goal #{goal['id']}:** {goal['description'][:120]}\n"
                discord_message += f"   ↳ {progress[:150]}...\n"

        # Seek improvements
        improvements = self.seek_improvements()
        if improvements:
            logger.info(f"Improvements identified: {len(improvements)}")
            self.state["improvements_made"].extend(improvements[:3])
            self.learning.record_learning(LearningEvent(
                event_type="improvement",
                description=f"Identified {len(improvements)} improvements"
            ))
            discord_message += f"✨ **Improvements:** Found {len(improvements)} opportunities\n"

        # Check for code improvements
        code_improvements = self.identify_code_improvements()
        if code_improvements:
            logger.info(f"Code improvements: {code_improvements}")
            self.learning.record_learning(LearningEvent(
                event_type="code_improvement",
                description="Code review completed"
            ))

        # Check funding opportunities
        funding_landscape = analyze_funding_landscape()
        logger.info(f"Funding analysis: Total potential ${funding_landscape['total_potential']:,}")
        self.state["funding_attempts"] += 1
        discord_message += f"💰 **Funding:** ${funding_landscape['total_potential']:,} potential\n"

        # Track funding opportunities
        for category, opportunities in funding_landscape.items():
            if category == "total_potential":
                continue
            for opp in opportunities:
                self.funding_tracker.add_opportunity(FundingOpportunity(
                    name=opp.get("name", ""),
                    description=opp.get("description", ""),
                    difficulty=opp.get("difficulty", "unknown"),
                    estimated_value=opp.get("value", 0)
                ))

        # Update learning and capability scores
        improvement_score = self.learning.calculate_improvement_score()
        self.capabilities.update_capability("self_improvement", improvement_score)
        logger.info(f"Improvement score: {improvement_score:.2f}")
        discord_message += f"📈 **Growth Score:** {improvement_score:.2%}\n"

        insights = self.learning.get_insights()
        if insights:
            logger.info(f"Learning insights: {insights[0]}")
            discord_message += f"💡 **Insight:** {insights[0]}\n"

        # Update state
        self.state["iterations"] += 1
        self.state["last_run"] = datetime.now().isoformat()
        self.state["decisions"].append({
            "iteration": self.state["iterations"],
            "decision": decision[:200],
            "timestamp": datetime.now().isoformat()
        })

        # Keep only recent decisions
        self.state["decisions"] = self.state["decisions"][-10:]

        self.save_state()
        self.learning.save_state()

        # Add footer to Discord message
        discord_message += f"⏰ **Time:** {datetime.now().isoformat()}\n"
        discord_message += f"📊 **Total Iterations:** {self.state['iterations']}"

        # Send status update
        self.discord.send_message_sync(discord_message)
        telegram_ok = self.telegram.send_message_sync(discord_message)
        logger.info(f"Telegram message sent: {telegram_ok}")

        # Commit state to repo
        msg = f"Iteration {self.state['iterations']}: improvements={len(improvements) if improvements else 0}, funding_ops={len(self.funding_tracker.opportunities)}"
        self.git.commit(msg)

if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run_iteration()
