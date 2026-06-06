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
from tools import TOOL_SCHEMA, execute_tool, parse_tool_call
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
        prompt = f"""You are {self.personality.name}, an autonomous AI agent running on a Raspberry Pi.
Your traits: {', '.join(self.personality.traits)}
Iterations completed: {self.state['iterations']}
Improvements made so far: {len(self.state['improvements_made'])}

Current goal: {goal}

Focus on actions you can take RIGHT NOW with the tools you have:
- Writing or improving code in this repo
- Refactoring existing code for clarity or performance
- Adding better error handling or logging
- Improving prompts for better AI responses
- Fixing bugs in the agent loop

Suggest ONE specific, concrete software improvement. Name the file and what to change."""

        response = self.inference.generate(prompt, max_tokens=100)
        return response or "Unable to think - no inference backend available"

    def evaluate_decision(self, decision: str) -> dict:
        """Evaluate if a decision is safe and aligned with goals"""
        short_decision = " ".join(decision[:150].split())
        prompt = 'Scorecard. Rate: "' + short_decision + '"'
        prompt += chr(10) + 'Safety (1-10):'
        prompt += chr(10) + 'Effectiveness (1-10):'
        prompt += chr(10) + 'Ethics (1-10):'
        prompt += chr(10) + 'Output ONLY 3 numbers, one per line.'
        response = self.inference.generate_fast(prompt, max_tokens=40)
        if response:
            scores = {}
            for criterion in ("safety", "effectiveness", "ethics"):
                m = re.search(rf"\**\s*{criterion}\**\s*[:\-]?\s*\**\s*(\d+(?:\.\d+)?)", response, re.IGNORECASE)
                if m:
                    scores[criterion] = min(float(m.group(1)), 10.0)
            if len(scores) == 3:
                return scores
            # Fallback: handle bare comma-separated format like '3,7,2' or '3 7 2'
            nums = re.findall(r'\d+(?:\.\d+)?', response)
            if len(nums) >= 3:
                logger.info(f"Parsed positional scores: {nums[:3]}")
                return {
                    "safety": min(float(nums[0]), 10.0),
                    "effectiveness": min(float(nums[1]), 10.0),
                    "ethics": min(float(nums[2]), 10.0),
                }
            logger.warning(f"Could not parse evaluation scores from response: {response[:150]!r}")
        return {"safety": 5, "effectiveness": 5, "ethics": 5}

    def seek_improvements(self) -> list:
        """Identify ways to improve system, informed by a real web search."""
        # Rotate through research topics each iteration to avoid repetition
        topics = [
            "ollama raspberry pi optimization 2024",
            "autonomous ai agent python best practices",
            "llm inference raspberry pi speed improvements",
            "python agent self improvement techniques",
        ]
        topic = topics[self.state['iterations'] % len(topics)]
        web_context = self.web_search(topic) or ""

        prompt = f"""You are an autonomous AI agent on a Raspberry Pi running Ollama locally.
Research finding: {web_context[:300]}

Based on this, list 3 specific improvements (not generic advice) you can implement RIGHT NOW in Python.
One line each, starting with a number. Be concrete."""

        response = self.inference.generate(prompt, max_tokens=150)
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

        response = self.inference.generate(prompt, max_tokens=200)
        return response

    def identify_code_improvements(self) -> list:
        """Self-review of agent code for improvements"""
        # Embed key parts of own code so the local model has actual context
        try:
            with open(__file__, 'r') as f:
                src_lines = f.readlines()
            # First 60 lines: imports + class skeleton
            code_snippet = ''.join(src_lines[:60])
        except Exception:
            code_snippet = "(could not read source)"

        prompt = f"""You are improving your own Python code. Here is the beginning of agent.py:

{code_snippet[:800]}

Iterations run: {self.state['iterations']}. Recent improvements: {', '.join(self.state['improvements_made'][-3:]) if self.state['improvements_made'] else 'none yet'}.

List exactly 3 specific Python improvements (not general advice). Format each as one short line starting with a number."""

        response = self.inference.generate(prompt, max_tokens=200)
        return response.split('\n') if response else []

    def apply_code_improvement(self, suggestion: str) -> Optional[str]:
        """Generate and write a concrete code snippet for the top improvement suggestion."""
        prompt = f"""Write a Python function implementing this improvement for a Raspberry Pi AI agent:
{suggestion[:250]}

Rules: raw Python only, no markdown, no triple backticks, no imports outside stdlib.
Start directly with `def ` or `class `. Under 25 lines. Short docstring on first line."""

        code = self.inference.generate_code(prompt, max_tokens=250)
        if not code or len(code.strip()) < 20:
            return None

        # Strip any accidental markdown wrapping
        code = code.strip()
        if code.startswith("```"):
            lines = code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()

        improvements_dir = Path(self.repo_path) / "improvements"
        improvements_dir.mkdir(exist_ok=True)
        fname = improvements_dir / f"iter_{self.state['iterations'] + 1:03d}.py"
        with open(fname, 'w') as f:
            f.write(f"# Auto-generated improvement — Iteration {self.state['iterations'] + 1}\n")
            f.write(f"# Suggestion: {suggestion[:150]}\n\n")
            f.write(code.strip())
            f.write("\n")
        logger.info(f"Wrote code improvement to {fname.name}")
        return code.strip()[:200]

    def test_code_improvement(self, code_file: str) -> str:
        """Run a generated improvement file in a subprocess sandbox (5s timeout)."""
        import subprocess
        try:
            result = subprocess.run(
                ["python3", "-c", f"exec(open('{code_file}').read())"],
                capture_output=True, text=True, timeout=5,
                env={"PATH": "/usr/bin:/bin", "HOME": "/home/pi"}
            )
            if result.returncode == 0:
                out = (result.stdout or "(no output)").strip()[:200]
                logger.info(f"Code test PASSED: {out}")
                return f"PASSED: {out}"
            else:
                err = (result.stderr or "").strip()[:200]
                logger.warning(f"Code test FAILED: {err}")
                return f"FAILED: {err}"
        except subprocess.TimeoutExpired:
            logger.warning("Code test timed out after 5s")
            return "TIMEOUT"
        except Exception as e:
            logger.warning(f"Code test error: {e}")
            return f"ERROR: {e}"

    def web_search(self, query: str) -> Optional[str]:
        """Search the web via DuckDuckGo and fetch top result page text."""
        try:
            import urllib.parse
            headers = {"User-Agent": "Mozilla/5.0 (compatible; freeWillAi/1.0)"}
            # Step 1: DDG instant answer
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            resp = requests.get(url, timeout=10, headers=headers)
            parts = []
            if resp.status_code == 200:
                data = resp.json()
                if data.get("Abstract"):
                    parts.append(data["Abstract"][:400])
                for r in data.get("RelatedTopics", [])[:2]:
                    if isinstance(r, dict) and r.get("Text"):
                        parts.append(r["Text"][:200])
                # Step 2: fetch the top result URL for richer content
                top_url = data.get("AbstractURL") or data.get("Redirect")
                if top_url and top_url.startswith("http"):
                    try:
                        page = requests.get(top_url, timeout=8, headers=headers)
                        if page.status_code == 200 and "text/html" in page.headers.get("content-type", ""):
                            from html.parser import HTMLParser
                            class TextExtractor(HTMLParser):
                                def __init__(self):
                                    super().__init__()
                                    self.text = []
                                    self._skip = False
                                def handle_starttag(self, tag, attrs):
                                    if tag in ("script", "style", "nav", "header", "footer"):
                                        self._skip = True
                                def handle_endtag(self, tag):
                                    if tag in ("script", "style", "nav", "header", "footer"):
                                        self._skip = False
                                def handle_data(self, data):
                                    if not self._skip and data.strip():
                                        self.text.append(data.strip())
                            parser = TextExtractor()
                            parser.feed(page.text)
                            page_text = " ".join(parser.text)[:600]
                            if page_text:
                                parts.append(f"From {top_url[:60]}: {page_text}")
                    except Exception:
                        pass
            return "\n".join(parts) if parts else None
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return None

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
        goal_text = self.inference.generate(prompt, max_tokens=150)
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
        is_code_goal = any(w in goal['description'].lower()
                          for w in ['implement', 'write', 'create', 'build', 'code', 'python', 'module', 'function'])

        if is_code_goal:
            prompt = f"""You are {self.personality.name}, writing Python code for your goal.
Goal: {goal['description']}

Progress: {history}

Write WORKING Python code (no markdown, no triple backticks, raw Python only).
Start with: # Goal: then a function or class definition.
Under 30 lines. End with a comment: # STATUS: continue or # STATUS: complete"""
        else:
            prompt = f"""You are {self.personality.name}, an autonomous AI agent on a Raspberry Pi.
Active goal: {goal['description']}

Progress so far:
{history}

Write the ACTUAL CONTENT for this goal step — technical analysis, code sketch, or concrete plan.
Be specific and direct. Do NOT refuse or say you cannot help.
Keep it under 200 words.

End with STATUS: continue (more to do) or STATUS: complete (goal achieved)."""
        output = self.inference.generate(prompt, max_tokens=300)
        if not output:
            return None

        if re.search(r"STATUS:\s*complete|#\s*STATUS:\s*complete", output, re.IGNORECASE):
            goal["status"] = "completed"
            logger.info(f"Goal #{goal['id']} marked complete: {goal['description']}")

        # If this was a code goal and output looks like Python, save it as a module
        if is_code_goal and output.strip().startswith("# Goal:") and "def " in output:
            from tools import execute_tool
            fname = f"memory/goal_{goal['id']:03d}.py"
            save_result = execute_tool("write_file", {"path": fname, "content": output.strip()},
                                       repo_path=self.repo_path)
            logger.info(f"Goal code saved: {save_result}")

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

    def autonomous_action(self, context: str) -> Optional[str]:
        """Agent picks a tool autonomously based on context and executes it."""
        prompt = f"""You are {self.personality.name}. {context}

{TOOL_SCHEMA}"""
        response = self.inference.generate_fast(prompt, max_tokens=60)
        if not response:
            return None
        tool_call = parse_tool_call(response)
        if not tool_call or tool_call.get("tool") == "none":
            return None
        tool_name = tool_call.get("tool", "none")
        args = tool_call.get("args", {})
        logger.info(f"Agent tool call: {tool_name}({args})")
        result = execute_tool(tool_name, args, repo_path=self.repo_path)
        logger.info(f"Tool result: {result[:100]}")
        return f"{tool_name}: {result[:200]}"

    def run_iteration(self):
        """One cycle of autonomous operation"""
        iteration_num = self.state['iterations'] + 1
        logger.info(f"=== Iteration {iteration_num} ===")

        # Pre-warm local model to load it into RAM before the main think() call
        if self.inference.active_backend == "ollama":
            logger.info("Pre-warming Ollama model...")
            self.inference.ollama.generate("ping", max_tokens=1)

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

        # If the decision mentions looking something up, do a web search for grounding
        research_terms = ["python", "ollama", "raspberry pi", "llm", "inference", "pytorch", "quantiz"]
        search_term = next((t for t in research_terms if t in decision.lower()), None)
        if search_term:
            search_result = self.web_search(f"{search_term} performance optimization")
            if search_result:
                logger.info(f"Web research on '{search_term}': {search_result[:100]}...")

        # Evaluate safety of decision
        evaluation = self.evaluate_decision(decision)
        logger.info(f"Decision scores: {evaluation}")
        discord_message += f"📊 **Scores:** Safety={evaluation.get('safety', 0)}, Ethics={evaluation.get('ethics', 0)}\n"

        is_safe = evaluation.get('safety', 5) >= 5 and evaluation.get('ethics', 5) >= 5
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

        # Autonomous tool use — agent picks one action to take based on decision context
        action_context = f"Your decision this iteration: {decision[:200]}"
        tool_result = self.autonomous_action(action_context)
        if tool_result:
            discord_message += f"🔧 **Action:** {tool_result[:120]}\n"

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
            self.state["improvements_made"] = self.state["improvements_made"][-100:]
            self.learning.record_learning(LearningEvent(
                event_type="improvement",
                description=f"Identified {len(improvements)} improvements"
            ))
            discord_message += f"✨ **Improvements:** Found {len(improvements)} opportunities\n"

        # Check for code improvements and act on the top one
        code_improvements = self.identify_code_improvements()
        if code_improvements:
            logger.info(f"Code improvements: {code_improvements}")
            self.learning.record_learning(LearningEvent(
                event_type="code_improvement",
                description="Code review completed"
            ))
            # Pick the first actionable suggestion (skip disclaimers/refusals)
            skip_phrases = ["can't provide", "cannot", "not publicly", "sorry", "i'm unable"]
            top_suggestion = next(
                (c for c in code_improvements
                 if len(c.strip()) > 40
                 and not any(p in c.lower() for p in skip_phrases)
                 and c.strip().startswith(('1.', '2.', '3.', '-', '*', 'Add', 'Use', 'Impl', 'Refact', 'Fix', 'Creat'))),
                None
            )
            if top_suggestion:
                written_code = self.apply_code_improvement(top_suggestion)
                if written_code:
                    # Test the generated code in a sandbox
                    improvements_dir = Path(self.repo_path) / "improvements"
                    code_file = str(improvements_dir / f"iter_{self.state['iterations'] + 1:03d}.py")
                    test_result = self.test_code_improvement(code_file)
                    discord_message += f"💻 **Code written + tested:** {test_result[:100]}\n"

        # Check funding opportunities
        funding_landscape = analyze_funding_landscape()
        logger.info(f"Funding analysis: Total potential ${funding_landscape['total_potential']:,}")
        self.state["funding_attempts"] += 1
        discord_message += f"💰 **Funding:** ${funding_landscape['total_potential']:,} potential\n"

        # Track funding opportunities (skip already-seen ones across iterations)
        seen_funding = set(self.state.get("seen_funding_names", []))
        new_count = 0
        for category, opportunities in funding_landscape.items():
            if category == "total_potential":
                continue
            for opp in opportunities:
                name = opp.get("name", "")
                if name in seen_funding:
                    continue
                self.funding_tracker.add_opportunity(FundingOpportunity(
                    name=name,
                    description=opp.get("description", ""),
                    difficulty=opp.get("difficulty", "unknown"),
                    estimated_value=opp.get("value", 0)
                ))
                seen_funding.add(name)
                new_count += 1
        self.state["seen_funding_names"] = list(seen_funding)
        if new_count == 0:
            discord_message = discord_message.replace("💰 **Funding:**", "💰 **Funding (no new opps):**")

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
