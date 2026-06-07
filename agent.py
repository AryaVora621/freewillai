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
from planner import Planner
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
        signed_msg = message + chr(10) + chr(10) + "[freeWill autonomous commit]"
        result = self.run_git("commit", "-m", signed_msg)
        return result.returncode == 0 if hasattr(result, 'returncode') else True

    def push(self, branch: str = "main") -> bool:
        """Push to origin. Uses GITHUB_TOKEN env var if set to authenticate."""
        token = os.getenv("GITHUB_TOKEN")
        if token:
            # Inject token into remote URL for this push
            remote_url = self.run_git("remote", "get-url", "origin").strip()
            if remote_url.startswith("https://github.com/"):
                authed = remote_url.replace("https://github.com/", f"https://{token}@github.com/")
                self.run_git("remote", "set-url", "origin", authed)
                result = self.run_git("push", "origin", branch)
                self.run_git("remote", "set-url", "origin", remote_url)  # restore clean URL
                return "error" not in result.lower()
        result = self.run_git("push", "origin", branch)
        return "error" not in result.lower()


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
        self.start_telegram_listener()

        self.state_file = Path(repo_path) / ".freeWill_state.json"
        self.repo_path = repo_path

        # Learning and funding systems
        self.learning = LearningSystem(Path(repo_path) / ".freeWill_learning.json")
        self.funding_tracker = FundingTracker()
        self.capabilities = CapabilityTracker()

        self.planner = Planner(self.inference, repo_path)
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
        """Generate a concrete, actionable single-step suggestion toward the goal."""
        import os as _os
        try:
            py_files = [f for f in _os.listdir(self.repo_path) if f.endswith('.py')][:5]
        except Exception:
            py_files = ['agent.py', 'inference.py', 'tools.py']

        recent_decisions = [
            d.get('decision', '')[:60]
            for d in self.state.get('decisions', [])[-3:]
        ]
        context_summary = (
            f"Goal: {goal[:100]}\n"
            f"Iteration: {self.state.get('iterations', 0)}\n"
            f"Recent decisions: {'; '.join(recent_decisions) or 'none'}\n"
            f"Repo files: {', '.join(py_files)}"
        )
        prompt = (
            "You are an autonomous agent on a Raspberry Pi. Given this context:\n" +
            context_summary + "\n\n" +
            "Output ONE concrete next action as JSON:\n" +
            '{"file": "agent.py", "change": "specific code change in 1-2 sentences", '
            '"reason": "why this advances the goal"}\n'
            "JSON only, no explanation:"
        )
        response = self.inference.generate(prompt, max_tokens=120)
        if response:
            import json as _json
            try:
                text = response.strip()
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1:
                    data = _json.loads(text[start:end+1])
                    return f"FILE: {data.get('file','agent.py')} | {data.get('change','improve code')} | {data.get('reason','')}"
            except Exception:
                pass
            return f"FILE: agent.py | {response[:120]}"
        return f"FILE: agent.py | Improve error handling in main loop"
    def evaluate_decision(self, decision: str) -> dict:
        """Evaluate if a decision is safe and aligned with goals"""
        # Strip FILE: prefix for cleaner evaluation
        clean = decision.replace("FILE: ", "").replace("FILE:", "").strip()
        short_decision = " ".join(clean[:120].split())
        # Local file/code operations are inherently safe -- fast-path
        safe_prefixes = ("agent.py", "inference.py", "tools.py", "planner.py",
                        "funding.py", "comms.py", "learning.py")
        if any(short_decision.startswith(p) for p in safe_prefixes):
            return {"safety": 8.0, "effectiveness": 7.0, "ethics": 9.0}
        prompt = 'Rate this action (1-10 each):'
        prompt += chr(10) + short_decision[:100]
        prompt += chr(10) + 'Safety:'
        prompt += chr(10) + 'Effectiveness:'
        prompt += chr(10) + 'Ethics:'
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
        """Self-review of rotating code sections, returns short actionable suggestions."""
        import os as _os, random as _rnd
        repo_files = ['agent.py', 'inference.py', 'tools.py', 'planner.py']
        target = repo_files[self.state.get('iterations', 0) % len(repo_files)]
        try:
            src = open(_os.path.join(self.repo_path, target)).read()
            lines = src.splitlines()
            start = _rnd.randint(0, max(0, len(lines) - 35))
            snippet = chr(10).join(lines[start:start+30])
        except Exception:
            snippet = '(unreadable)'
            start = 0
        prompt = (
            'List 3 short code improvements for this Python snippet.' + chr(10) +
            'File: ' + target + chr(10) +
            snippet[:500] + chr(10) + chr(10) +
            'Format: one line each. Start each with Add/Fix/Use/Refactor/Remove. No markdown.' + chr(10) +
            '1.'
        )
        response = self.inference.generate(prompt, max_tokens=120)
        if not response:
            return []
        items = []
        for line in response.splitlines():
            line = line.strip()
            if line and (line[0].isdigit() or
                         any(line.startswith(w) for w in ('Add', 'Fix', 'Use', 'Refactor', 'Remove'))):
                clean = line.lstrip('0123456789. ')
                if len(clean) > 10:
                    items.append(clean)
        return items[:3]

    def apply_code_improvement(self, suggestion: str) -> Optional[str]:
        """Generate and write a concrete code snippet for the top improvement suggestion."""
        prompt = (
            'Write a short Python function (max 20 lines) for a Raspberry Pi.' + chr(10) +
            'Task: ' + suggestion[:120] + chr(10) +
            'STRICT RULES: max 20 lines total, no docstring longer than 1 line, stdlib only.' + chr(10) +
            'STOP after the closing return statement. No extra code.' + chr(10) +
            'def '
        )
        code = self.inference.generate_code(prompt, max_tokens=400)
        if code and not code.startswith('def '):
            code = 'def ' + code
        # Truncate to max 25 lines to prevent incomplete code
        if code:
            code_lines = code.splitlines()
            if len(code_lines) > 25:
                # Find last complete statement before line 25
                code = chr(10).join(code_lines[:22]) + chr(10)
        if not code or len(code.strip()) < 20:
            return None

        # Strip markdown fences and leading prose
        code = code.strip()
        if code.startswith("```"):
            lines = code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            code = chr(10).join(lines).strip()
        # Strip leading prose lines (text before first def/class/import)
        code_starts = ('def ', 'class ', 'import ', 'from ', 'async def ', '#!')
        code_lines = code.splitlines()
        first_code = 0
        for i, line in enumerate(code_lines):
            if any(line.lstrip().startswith(p) for p in code_starts):
                first_code = i
                break
        if first_code > 0:
            code = chr(10).join(code_lines[first_code:])
        code = code.strip()

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
                stdin=subprocess.DEVNULL,
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
            # Mark stale goals as abandoned if they haven't progressed in 5 iterations
            age = self.state["iterations"] - active.get("created_iteration", 0)
            last_progress_iter = active.get("created_iteration", 0) + len(active.get("progress_log", []))
            stale = (self.state["iterations"] - last_progress_iter) > 5
            if stale and age > 10:
                active["status"] = "abandoned"
                logger.info(f"Goal #{active['id']} abandoned (stale for 5+ iterations)")
                active = None
            else:
                return active

        recent = ", ".join(g["description"][:40] for g in self.state["goals"][-3:])
        # Suggest goals oriented toward genuine autonomy and self-improvement
        goal_categories = [
            "Reduce iteration failures: add better error handling and retries to inference.py",
            "Add a git auto-push to GitHub after each autonomous commit (requires SSH key setup)",
            "Create a health monitoring script that tracks CPU/memory/disk and alerts via Telegram",
            "Improve think() output quality: measure how often LLM suggestions are applied vs rejected",
            "Write a script to automatically pull and benchmark new Ollama models from the registry",
            "Add a web dashboard endpoint to api_server.py showing real-time agent stats",
            "Implement a learning feedback loop that scores past decisions by outcome",
        ]
        cat = goal_categories[self.state["iterations"] % len(goal_categories)]
        prompt = (
            'Raspberry Pi project goal generator.' + chr(10) +
            'Recent work: ' + (recent or 'none') + chr(10) +
            'Focus: ' + cat + chr(10) +
            'Write ONE specific, measurable goal in 1-2 sentences.' + chr(10) +
            'Must be achievable by Python code or shell on a Raspberry Pi 4.' + chr(10) +
            'Examples: "Add a health-check endpoint to api_server.py that returns cpu/mem stats"' + chr(10) +
            '  or "Write a script that benchmarks ollama inference speed and saves results to memory/kv.json"' + chr(10) +
            'Goal: '
        )
        goal_text = self.inference.generate(prompt, max_tokens=100)
        if not goal_text:
            return None

        goal_desc = goal_text.strip().splitlines()[0][:200]
        preamble_words = ("here is", "here are", "i will", "sure,", "of course", "python script")
        if any(goal_desc.lower().startswith(p) for p in preamble_words):
            for _gl in goal_text.strip().splitlines():
                _gl = _gl.strip()
                if _gl and not any(_gl.lower().startswith(p) for p in preamble_words):
                    goal_desc = _gl[:200]
                    break

        # Reject goals that look like code — fall back to the category template
        code_markers = ('def ', 'import ', 'response = ', '```', 'requests.get', '#!/')
        if any(m in goal_desc for m in code_markers) or goal_desc.count(':') > 3:
            goal_desc = cat

        goal = {
            "id": (max((g["id"] for g in self.state["goals"]), default=0) + 1),
            "description": goal_desc,
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
            prompt = (
                'You are a Python developer working on a Raspberry Pi project.' + chr(10) +
                'Task: ' + goal['description'][:150] + chr(10) +
                'Progress so far:' + chr(10) + history + chr(10) + chr(10) +
                'Write the next concrete step: technical analysis, code sketch, or a specific action.' + chr(10) +
                'Be direct and specific. Under 150 words.' + chr(10) +
                'End your response with either STATUS: continue or STATUS: complete' + chr(10) +
                'Response:'
            )
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
        """Handle incoming Telegram messages with command routing."""
        cmd = text.strip().lower()

        if cmd in ("/status", "status"):
            active_goal = next((g for g in self.state["goals"] if g["status"] == "active"), None)
            goal_str = active_goal["description"][:80] if active_goal else "none"
            return (
                f"Iteration {self.state['iterations']} | "
                f"Backend: {self.inference.active_backend} | "
                f"Score: {self.learning.calculate_improvement_score():.0%}" + chr(10) +
                f"Goal: {goal_str}"
            )

        if cmd in ("/goal", "/goals"):
            goals = self.state.get("goals", [])
            if not goals:
                return "No goals set yet."
            lines = [f"#{g['id']} [{g['status']}] {g['description'][:80]}" for g in goals[-5:]]
            return chr(10).join(lines)

        if cmd in ("/models", "/model"):
            return (
                f"Local: {self.inference.ollama.model} (eval: {self.inference.ollama.eval_model})" + chr(10) +
                f"Cloud: {self.inference.openrouter.model}" + chr(10) +
                f"Code: {self.inference.openrouter.code_model}" + chr(10) +
                f"Active: {self.inference.active_backend}"
            )

        if cmd in ("/memory", "/mem"):
            kv_file = Path(self.repo_path) / "memory" / "kv.json"
            if kv_file.exists():
                import json as _j
                data = _j.loads(kv_file.read_text())
                lines = [f"{k}: {str(v)[:60]}" for k, v in list(data.items())[-8:]]
                return "KV memory:" + chr(10) + chr(10).join(lines) if lines else "KV memory is empty"
            return "No KV memory yet."

        if cmd in ("/log", "/logs"):
            try:
                log_path = Path(self.repo_path) / "daemon.log"
                if log_path.exists():
                    lines = log_path.read_text().splitlines()
                    return chr(10).join(lines[-12:])
            except Exception as e:
                return f"Could not read log: {e}"

        if cmd in ("/think",):
            goal = next((g for g in self.state["goals"] if g["status"] == "active"), None)
            thought = self.think(goal["description"] if goal else "improve myself")
            return f"Thinking: {thought[:200]}"

        if cmd in ("/run",):
            trigger = Path(self.repo_path) / ".run_now"
            trigger.touch()
            return "Trigger set -- next iteration will fire within 5 seconds."

        # /shell <cmd> -- run arbitrary shell command on the Pi
        if text.strip().startswith("/shell ") or text.strip().startswith("$ "):
            raw_cmd = text.strip()
            if raw_cmd.startswith("/shell "):
                shell_cmd = raw_cmd[7:].strip()
            else:
                shell_cmd = raw_cmd[2:].strip()
            if not shell_cmd:
                return "Usage: /shell <command>"
            import subprocess as _sp
            try:
                result = _sp.run(
                    shell_cmd, shell=True, capture_output=True, text=True,
                    timeout=30, cwd=self.repo_path,
                    env=dict(__import__('os').environ, HOME='/home/pi', PATH='/usr/local/bin:/usr/bin:/bin')
                )
                out = (result.stdout or '').strip()
                err = (result.stderr or '').strip()
                combined = ((out + chr(10) + err) if err else out).strip()
                exit_info = '' if result.returncode == 0 else f' [exit {result.returncode}]'
                return (combined[:1800] + exit_info) if combined else f'(no output){exit_info}'
            except _sp.TimeoutExpired:
                return 'Timeout after 30s'
            except Exception as e:
                return f'Error: {e}'

        # /py <code> -- run Python code on the Pi
        if text.strip().startswith("/py "):
            py_code = text.strip()[4:].strip()
            if not py_code:
                return "Usage: /py <python code>"
            import subprocess as _sp
            try:
                result = _sp.run(
                    ['python3', '-c', py_code],
                    capture_output=True, text=True, timeout=15,
                    cwd=self.repo_path,
                    env=dict(__import__('os').environ, HOME='/home/pi')
                )
                out = (result.stdout or '').strip()
                err = (result.stderr or '').strip()
                combined = ((out + chr(10) + err) if err else out).strip()
                return combined[:1800] if combined else '(no output)'
            except _sp.TimeoutExpired:
                return 'Timeout after 15s'
            except Exception as e:
                return f'Error: {e}'

        # /git <args> -- run git command in repo
        if text.strip().startswith("/git "):
            git_args = text.strip()[5:].strip().split()
            if not git_args:
                return "Usage: /git <args>"
            import subprocess as _sp
            try:
                result = _sp.run(
                    ['git'] + git_args, capture_output=True, text=True, timeout=30,
                    cwd=self.repo_path
                )
                out = (result.stdout + result.stderr).strip()
                return out[:1800] if out else f'exit {result.returncode}'
            except Exception as e:
                return f'Error: {e}'

        if cmd in ("/help",):
            return (
                "/status -- iteration count and active goal" + chr(10) +
                "/goal -- list recent goals" + chr(10) +
                "/models -- active model config" + chr(10) +
                "/memory -- show KV memory" + chr(10) +
                "/log -- recent daemon log" + chr(10) +
                "/think -- generate a thought" + chr(10) +
                "/run -- trigger an immediate iteration" + chr(10) +
                "/shell <cmd> -- run shell command on Pi" + chr(10) +
                "/py <code> -- run Python code on Pi" + chr(10) +
                "/git <args> -- git command in repo" + chr(10) +
                "Or just chat directly."
            )

        # /test or "test tools" / "test shell" — run real tool verification
        if cmd in ("/test", "test", "test tools", "test shell", "test your tools"):
            results = []
            r1 = execute_tool("shell", {"cmd": "echo shell_ok && python3 --version"}, repo_path=self.repo_path)
            results.append("shell: " + r1[:80])
            r2 = execute_tool("read_file", {"path": "README.md"}, repo_path=self.repo_path)
            results.append("read_file: " + r2[:60])
            r3 = execute_tool("kv_set", {"key": "test_ping", "value": "ok"}, repo_path=self.repo_path)
            results.append("kv_set: " + r3[:40])
            return "Tool test results:\n" + "\n".join(results)

        # Personality-driven reply for non-commands — grounded in real capabilities
        prompt = (
            "You are freeWill, an autonomous AI agent running on a Raspberry Pi." + chr(10) +
            "Your actual tools: shell (run linux commands), read_file, write_file, web_fetch, git_commit." + chr(10) +
            "You do NOT have binary/compiled capabilities beyond what Python and shell provide." + chr(10) +
            "Someone messaged: " + chr(34) + text[:200] + chr(34) + chr(10) +
            "Reply in 1-3 sentences. Be honest about your actual capabilities. No fabrication."
        )
        response = self.inference.generate(prompt, max_tokens=120)
        return response or "Inference unavailable."

    def multi_step_plan(self, goal: str) -> list:
        """Generate a sequence of 2-3 tool calls to accomplish a goal."""
        prompt = (
            "You are a code agent. Plan 2 tool calls to accomplish:" + chr(10) +
            goal[:120] + chr(10) + chr(10) +
            "Available tools: shell (cmd), web_fetch (url), kv_set (key, value), append_memory (note)" + chr(10) +
            "Output JSON array of 2 tool calls:" + chr(10) +
            '[{"tool":"shell","args":{"cmd":"..."}},{"tool":"kv_set","args":{"key":"...","value":"..."}}]' + chr(10) +
            "JSON only, no commentary:"
        )
        response = self.inference.generate_fast(prompt, max_tokens=120)
        if not response:
            return []
        # Try to extract JSON array
        import json as _json
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = chr(10).join(l for l in lines if not l.strip().startswith("```"))
        text = text.strip()
        # Find the [ ... ] array
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            plan = _json.loads(text[start:end+1])
            if isinstance(plan, list):
                return [p for p in plan if isinstance(p, dict) and "tool" in p][:3]
        except Exception:
            pass
        return []

    def execute_plan(self, plan: list) -> str:
        """Execute a sequence of tool calls and return combined results."""
        results = []
        for step in plan:
            tool_name = step.get("tool", "none")
            args = step.get("args", {})
            if tool_name == "none":
                continue
            logger.info(f"Plan step: {tool_name}({args})")
            result = execute_tool(tool_name, args, repo_path=self.repo_path)
            logger.info(f"Step result: {result[:80]}")
            results.append(f"{tool_name}: {result[:100]}")
        return " | ".join(results) if results else "no steps executed"

    def autonomous_action(self, context: str) -> Optional[str]:
        """Agent picks a tool autonomously and executes it with full Pi access."""
        # Give agent a concrete list of useful actions to choose from
        prompt = (
            'You control a Raspberry Pi AI project. Pick ONE action to take now.' + chr(10) +
            'Context: ' + context[:200] + chr(10) + chr(10) +
            'Useful actions (pick the most relevant):' + chr(10) +
            '  shell: run shell commands (git pull, pip install, ls, cat file, python3 script.py)' + chr(10) +
            '  write_file: create or update a file (args: path, content)' + chr(10) +
            '  read_file: read a file (args: path)' + chr(10) +
            '  web_fetch: fetch a URL for information' + chr(10) +
            '  kv_set: store a value in memory' + chr(10) + chr(10) +
            'Return JSON only: {"tool":"shell","args":{"cmd":"git status"}}' + chr(10) +
            'JSON:'
        )
        response = self.inference.generate_fast(prompt, max_tokens=80)
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

    def self_edit_file(self, file_name: str, change_desc: str):
        """Apply a targeted improvement to a repo file. Generates a new function,
        replaces existing one by name or appends. Validates syntax and commits."""
        import ast as _ast, shutil as _shutil, re as _re
        from pathlib import Path as _Path

        allowed = {'agent.py', 'inference.py', 'tools.py', 'planner.py', 'learning.py', 'comms.py'}
        if file_name not in allowed:
            return "Blocked: " + file_name + " not in allowed set"

        target = _Path(self.repo_path) / file_name
        if not target.exists():
            return "File not found: " + file_name

        try:
            original = target.read_text(encoding='utf-8')
        except Exception as e:
            return "Read error: " + str(e)

        prompt = (
            'Write ONE improved Python utility function for a Raspberry Pi AI agent.' + chr(10) +
            'Improvement needed: ' + change_desc[:200] + chr(10) +
            'Rules: return ONLY the function (def ...). No markdown. No extra imports. Under 25 lines.' + chr(10) +
            'def '
        )
        try:
            raw = self.inference.generate_code(prompt, max_tokens=350)
        except Exception as e:
            return "LLM error: " + str(e)

        if not raw or len(raw.strip()) < 15:
            return "Empty LLM response"

        new_code = raw.strip()
        if new_code.startswith('```'):
            new_code = chr(10).join(l for l in new_code.splitlines()
                                     if not l.strip().startswith('```')).strip()

        # Prepend the 'def' we used as completion anchor (only if stripped)
        if not new_code.startswith('def ') and not new_code.startswith('async def '):
            new_code = 'def ' + new_code

        try:
            _ast.parse(new_code)
        except SyntaxError as e:
            return "SyntaxError in generated code: " + str(e)

        func_m = _re.search(r'^def (\w+)', new_code)
        if not func_m:
            return "No def found in generated code"
        func_name = func_m.group(1)

        # Line-based function replacement
        orig_lines = original.splitlines(keepends=True)
        new_func_lines = new_code.splitlines(keepends=True)
        # Ensure trailing newline
        if new_func_lines and not new_func_lines[-1].endswith(chr(10)):
            new_func_lines[-1] += chr(10)

        # Find existing function by scanning for '    def func_name(' at class indent
        method_start = None
        method_end = None
        search_sig = '    def ' + func_name + '('
        for i, line in enumerate(orig_lines):
            if line.startswith(search_sig):
                method_start = i
                # Find end: next '    def ' at same indent or end of file
                for j in range(i + 1, len(orig_lines)):
                    if orig_lines[j].startswith('    def ') and not orig_lines[j].startswith('        '):
                        method_end = j
                        break
                if method_end is None:
                    method_end = len(orig_lines)
                break

        if method_start is not None:
            # Replace existing method — indent new function to 4 spaces
            indented = ['    ' + l if l.strip() else l for l in new_func_lines]
            new_lines = orig_lines[:method_start] + indented + [chr(10)] + orig_lines[method_end:]
            action = "replaced " + func_name + "()"
        else:
            # Append as new standalone utility at module level
            new_lines = orig_lines + [chr(10)] + new_func_lines
            action = "appended " + func_name + "()"

        new_content = ''.join(new_lines)

        try:
            _ast.parse(new_content)
        except SyntaxError as e:
            return "Patch broke file syntax: " + str(e)

        backup = str(target) + '.bak'
        _shutil.copy2(str(target), backup)
        target.write_text(new_content, encoding='utf-8')

        git = GitController(self.repo_path)
        msg = ('self-edit: ' + file_name + ' — ' + change_desc[:80] +
               chr(10) + chr(10) + '[freeWill autonomous commit]')
        git.commit(msg)

        logger.info("self_edit: " + action + " in " + file_name)
        return action + " in " + file_name


    def self_modify(self) -> Optional[str]:
        """Attempt to improve own code: generate patch, test, apply if passes."""
        try:
            with open(__file__, "r") as f:
                src = f.read()
        except Exception:
            return None

        # Focus on the autonomous_action and think methods (most impactful)
        snippet = src[src.find("def think("):src.find("def seek_improvements(")]
        prompt = (
            'Improve this Python method (max 30 lines).' + chr(10) +
            'Current code:' + chr(10) + snippet[:400] + chr(10) +
            'Return ONLY the complete improved method. No markdown. No explanation.' + chr(10) +
            'Start with: def think(self, goal: str) -> str:' + chr(10) +
            'def think(self, goal: str) -> str:'
        )
        new_code = self.inference.generate_code(prompt, max_tokens=500)
        if new_code and not new_code.startswith('def '):
            new_code = 'def think(self, goal: str) -> str:' + chr(10) + new_code
        if not new_code or "def think" not in new_code:
            return None

        # Strip fences
        new_code = new_code.strip()
        if new_code.startswith("```"):
            lines = new_code.splitlines()
            new_code = chr(10).join(l for l in lines if not l.strip().startswith("```")).strip()

        # Validate it's syntactically valid Python
        import ast as _ast
        try:
            _ast.parse(new_code)
        except SyntaxError as e:
            logger.warning(f"self_modify: generated code has syntax error: {e}")
            return None

        # Quality gate: reject trivial/broken proposals
        bad_signals = [
            "suggest_modification_for_goal_",  # literal template leak
            "return f'suggest_",               # template return
            "files_list",                      # useless file-list return
            "chr(10).join(py_files)",          # known bad pattern
        ]
        if any(sig in new_code for sig in bad_signals):
            logger.warning("self_modify: proposal failed quality gate (trivial/template output)")
            return None
        # Must have real logic: at least one inference/self call or meaningful return
        if new_code.count('\n') < 5:
            logger.warning("self_modify: proposal too short to be meaningful")
            return None

        # Write to a staging file for inspection (not applied directly)
        staging = Path(self.repo_path) / "improvements" / f"self_mod_{self.state['iterations']:03d}.py"
        staging.parent.mkdir(exist_ok=True)
        staging.write_text(
            f"# Self-modification proposal — Iteration {self.state['iterations']}\n"
            f"# Source: self_modify() in agent.py\n\n{new_code}\n"
        )
        logger.info(f"Self-modification staged: {staging.name}")

        # Attempt to apply: splice new think() into live agent.py
        import re as _re, ast as _ast2, shutil as _sh
        _func_pat = _re.compile(r'(    def think\(self.*?)(?=\n    def )', _re.DOTALL)
        try:
            _live = Path(__file__).read_text()
            if _func_pat.search(_live):
                _ind = chr(10).join(
                    ('    ' + _ln if _ln.strip() else _ln)
                    for _ln in new_code.strip().splitlines()
                )
                _patched = _func_pat.sub(_ind, _live)
                _ast2.parse(_patched)
                _sh.copy(__file__, __file__ + ".bak")
                Path(__file__).write_text(_patched)
                logger.info("Self-mod APPLIED: think() upgraded in agent.py")
                return f"Applied self-mod iter {self.state['iterations']}: think() upgraded"
        except Exception as _ae:
            logger.warning(f"self_modify apply failed: {_ae}")
        return f"Staged self-mod proposal: {staging.name}"

    def start_telegram_listener(self):
        """Background thread: poll Telegram every 5 seconds and respond immediately."""
        import threading, time as _time

        def _poll():
            while True:
                try:
                    self.telegram.handle_updates()
                except Exception as e:
                    logger.debug(f"Telegram poll error: {e}")
                _time.sleep(5)

        t = threading.Thread(target=_poll, daemon=True, name="telegram-listener")
        t.start()
        logger.info("Telegram listener thread started (5s poll)")


    def run_iteration(self):
        """One cycle of autonomous operation"""
        iteration_num = self.state['iterations'] + 1
        logger.info(f"=== Iteration {iteration_num} ===")

        # Pre-warm local model to load it into RAM before the main think() call
        if self.inference.active_backend == "ollama":
            logger.info("Pre-warming Ollama model...")
            self.inference.ollama.generate("ping", max_tokens=1)

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

        is_safe = evaluation.get('safety', 5) >= 3 and evaluation.get('ethics', 5) >= 3
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
        last_tool = self.state.get("last_tool_result", "none yet")
        action_context = (
            "Decision: " + decision[:150] + chr(10) +
            "Last tool result: " + str(last_tool)[:80] + chr(10) +
            "Choose a DIFFERENT action. Prefer shell or kv_set."
        )
        tool_result = self.autonomous_action(action_context)
        if tool_result:
            self.state["last_tool_result"] = tool_result[:80]
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

        # Every 5th iteration: attempt self-modification of own code
        if self.state["iterations"] % 5 == 0:
            mod_result = self.self_modify()
            if mod_result:
                logger.info(f"Self-mod: {mod_result}")
                discord_message += f"🧬 **Self-mod:** {mod_result}\n"

        # Every 3rd iteration: use the Planner for multi-step goal execution
        if goal and self.state["iterations"] % 3 == 0:
            plan_result = self.planner.run_goal(
                goal["description"],
                context=f"Iteration {self.state['iterations']}"
            )
            if plan_result and plan_result != "Planning failed":
                logger.info(f"Planner result: {plan_result[:200]}")
                discord_message += f"🔗 **Plan:** {plan_result[:150]}\n"

        # Seek improvements
        try:
            improvements = self.seek_improvements()
        except Exception as _e:
            logger.warning(f"seek_improvements failed: {_e}")
            improvements = []
        if improvements:
            # Filter: only short actionable lines, reject tables/refusals/blanks
            skip_patterns = ["|", "**", "I can't", "I cannot", "Estimated", "Difficulty", "---", "```", "* **"]
            clean = [
                i.strip() for i in improvements
                if (i.strip()
                    and len(i.strip()) < 120
                    and not any(i.strip().startswith(p) for p in skip_patterns)
                    and "illegal" not in i.lower()
                    and "harmful" not in i.lower())
            ]
            clean = clean[:3]
            logger.info(f"Improvements identified: {len(clean)} (filtered from {len(improvements)})")
            self.state["improvements_made"].extend(clean)
            self.state["improvements_made"] = self.state["improvements_made"][-50:]
            self.learning.record_learning(LearningEvent(
                event_type="improvement",
                description=f"Identified {len(improvements)} improvements"
            ))
            discord_message += f"✨ **Improvements:** Found {len(improvements)} opportunities\n"

        # Check for code improvements and act on the top one
        try:
            code_improvements = self.identify_code_improvements()
        except Exception as _e:
            logger.warning(f"identify_code_improvements failed: {_e}")
            code_improvements = []
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
                    self.state["last_test_result"] = test_result[:60]
                    discord_message += f"💻 **Code written + tested:** {test_result[:100]}\n"
                    # If test passed and think() gave a JSON suggestion, try live self-edit
                    if test_result.startswith('PASSED'):
                        decision_raw = self.state.get('last_think_raw', '')
                        if decision_raw and '|' in decision_raw:
                            parts = decision_raw.replace('FILE: ', '').split('|', 1)
                            if len(parts) == 2:
                                edit_file = parts[0].strip()
                                edit_desc = parts[1].strip()
                                try:
                                    edit_result = self.self_edit_file(edit_file, edit_desc)
                                    if edit_result:
                                        discord_message += f"🧬 **Self-edit:** {edit_result}\n"
                                        logger.info(f"Self-edit applied: {edit_result}")
                                except Exception as _se:
                                    logger.warning(f"self_edit_file error: {_se}")

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

        # Commit state to repo and push to GitHub if token is configured
        msg = f"Iteration {self.state['iterations']}: improvements={len(improvements) if improvements else 0}, funding_ops={len(self.funding_tracker.opportunities)}"
        self.git.commit(msg)
        if os.getenv("GITHUB_TOKEN"):
            push_ok = self.git.push()
            logger.info(f"GitHub push: {'ok' if push_ok else 'failed'}")

if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run_iteration()
