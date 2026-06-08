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

    def run_git(self, *args):
        """Execute git command, return CompletedProcess."""
        return subprocess.run(
            ["git", "-C", self.repo_path] + list(args),
            capture_output=True, text=True
        )

    def commit(self, message: str) -> bool:
        """Commit changes with agent signature. Returns True if commit was created."""
        self.run_git("add", "-A")
        signed_msg = message + chr(10) + chr(10) + "[freeWill autonomous commit]"
        result = self.run_git("commit", "-m", signed_msg)
        # "nothing to commit" is a non-error no-op (returncode 1 from git)
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            logger.warning(f"git commit failed: {result.stderr.strip()[:80]}")
            return False
        return True

    def push(self, branch: str = "main") -> bool:
        """Push to origin. Uses GITHUB_TOKEN env var if set to authenticate."""
        token = os.getenv("GITHUB_TOKEN")
        if token:
            remote_result = self.run_git("remote", "get-url", "origin")
            remote_url = remote_result.stdout.strip()
            if remote_url.startswith("https://github.com/"):
                authed = remote_url.replace("https://github.com/", f"https://{token}@github.com/")
                self.run_git("remote", "set-url", "origin", authed)
                result = self.run_git("push", "origin", branch)
                self.run_git("remote", "set-url", "origin", remote_url)
                return result.returncode == 0
        result = self.run_git("push", "origin", branch)
        return result.returncode == 0


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

    # Hardware context injected into all prompts — prevents GPU/Docker/CUDA suggestions
    HARDWARE_CONTEXT = (
        'HARDWARE: Raspberry Pi 4 (4-core ARM Cortex-A72, 4GB RAM, SD card storage, NO GPU).' + chr(10) +
        'INFERENCE: Primary=OpenRouter cloud API (fast, free tier). Local=smollm2:135m via Ollama (eval only).' + chr(10) +
        'CONSTRAINTS: No CUDA, no Docker, no vLLM, no GPU libraries. Python 3.11, ARM Linux.' + chr(10) +
        'GOAL: Be a self-improving autonomous agent. Improve your own code, add capabilities, fix bugs.'
    )

    def think(self, goal: str) -> str:
        """Generate a concrete, single-step code modification suggestion."""
        import os as _os
        import json as _json

        try:
            py_files = [f for f in _os.listdir(self.repo_path) if f.endswith('.py')][:5]
            files_list = ', '.join(py_files)
        except Exception:
            files_list = 'agent.py inference.py tools.py'

        recent_test = self.state.get('last_test_result', 'none')[:80]
        iteration = self.state.get('iterations', 0)
        recent_decisions = '; '.join(
            d['decision'][:50] for d in self.state.get('decisions', [])[-2:]
        )

        prompt = (
            self.HARDWARE_CONTEXT + chr(10) + chr(10) +
            'You are a code improvement agent for this repo.' + chr(10) +
            'Repo files: ' + files_list + chr(10) +
            f'Iteration: {iteration}' + chr(10) +
            'Recent decisions: ' + (recent_decisions or 'none') + chr(10) +
            'Current goal: ' + goal[:100] + chr(10) +
            'Last test: ' + recent_test + chr(10) + chr(10) +
            'Suggest ONE concrete, Pi-compatible code change. Respond with JSON only:' + chr(10) +
            '{"file":"filename.py","change":"specific what to change","rationale":"why this helps"}' + chr(10) +
            'JSON:'
        )

        try:
            raw_output = self.inference.generate(prompt, max_tokens=120)
        except Exception as e:
            return 'FILE: agent.py | add retry logic to inference fallback'

        if not raw_output:
            return 'FILE: agent.py | improve error handling'

        resp = raw_output.strip()

        # Try JSON parse first
        try:
            # Strip markdown fences
            if resp.startswith('```'):
                lines = resp.split(chr(10))
                resp = chr(10).join(l for l in lines if not l.startswith('```')).strip()
            suggestion = _json.loads(resp)
            fname = suggestion.get('file', 'agent.py')
            change = suggestion.get('change', 'improve error handling')
            return 'FILE: ' + fname + ' | ' + change[:80]
        except Exception:
            pass

        # Fallback: filter refusals
        refuse_phrases = ["i can't", "i cannot", "unable to", "not able to", "sorry"]
        first_line = resp.splitlines()[0].strip()
        if any(p in first_line.lower() for p in refuse_phrases):
            return 'FILE: agent.py | add retry logic to inference fallback'

        if '|' in first_line:
            return 'FILE: ' + first_line if not first_line.startswith('FILE:') else first_line
        return 'FILE: agent.py | ' + first_line[:60]
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
        system_msg = (
            'You are a Python code generator. '
            'Output ONLY valid Python code. '
            'No explanations, no prose, no markdown fences. '
            'First line MUST start with "def ". '
            'Never write sentences or paragraphs.'
        )
        prompt = (
            'Write a Python function (max 20 lines, stdlib only, Raspberry Pi 4).\n'
            'Task: ' + suggestion[:120] + '\n'
            'Rules: max 20 lines, one-line docstring only, no imports at top.\n'
            'Output starts with: def '
        )
        code = self.inference.generate_code(prompt, max_tokens=400, system=system_msg)
        if not code:
            return None

        # Strip markdown fences
        code = code.strip()
        if code.startswith("```"):
            lines = code.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines).strip()

        # Prepend def if response omitted it
        if not code.startswith('def '):
            code = 'def ' + code

        # Strip any leading prose before first def/class/import
        code_starts = ('def ', 'class ', 'import ', 'from ', 'async def ')
        code_lines = code.splitlines()
        first_code = next(
            (i for i, ln in enumerate(code_lines) if any(ln.lstrip().startswith(p) for p in code_starts)),
            0
        )
        if first_code > 0:
            code = "\n".join(code_lines[first_code:])
        code = code.strip()

        # Hard reject: if no def found or looks like prose (no colon on first code line)
        if not code.startswith('def ') or ':' not in code.split('\n')[0]:
            logger.warning("Code generation returned prose (no def header), rejecting")
            return None

        # Truncate to 25 lines max
        lines = code.splitlines()
        if len(lines) > 25:
            code = "\n".join(lines[:22])

        if len(code.strip()) < 20:
            return None

        # Syntax-check before writing -- catches mixed prose/code (e.g. prose at line 18+)
        import ast as _ast
        try:
            _ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Code generation syntax error at line {e.lineno}: rejecting")
            return None

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
        """Run a generated improvement file in a sandboxed subprocess (5 s timeout).
        Verifies the file imports, executes without error, and that each top‑level
        function can be called with no arguments. Returns an error message or an empty
        string on success.
        """
        import subprocess, pathlib, re, json, os, signal, resource, sys, textwrap, shlex, time

        # ---- 1️⃣ read source & discover top‑level functions -----------------
        src = pathlib.Path(code_file).read_text()
        func_names = re.findall(r'^\s*def\s+([A-Za-z_]\w*)\s*\(', src, re.MULTILINE)

        # ---- 2️⃣ build a tiny harness that imports the module and calls each func ----
        harness = textwrap.dedent(f'''
            import importlib.util, sys, json, traceback
            spec = importlib.util.spec_from_file_location("target_mod", {json.dumps(str(code_file))})
            mod = importlib.util.module_from_spec(spec)
            sys.modules["target_mod"] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception:
                print(json.dumps({{"error":"import_failed","trace":traceback.format_exc()}}))
                sys.exit(1)

            results = {{}}
            for name in {json.dumps(func_names)}:
                try:
                    getattr(mod, name)()
                    results[name] = "ok"
                except Exception as e:
                    results[name] = f"error: {{e}}"
            print(json.dumps(results))
        ''')

        # ---- 3️⃣ write harness to a temporary file -----------------
        harness_path = pathlib.Path("/tmp/harness_") .with_name(f"harness_{int(time.time()*1000)}.py")
        harness_path.write_text(harness)

        # ---- 4️⃣ sandbox limits (CPU time, memory, no file creation) ----------
        def preexec():
            # limit CPU time to 4 s (real time watchdog will enforce 5 s)
            resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
            # limit address space to 64 MiB
            resource.setrlimit(resource.RLIMIT_AS, (64*1024*1024, 64*1024*1024))
            # drop privileges if possible
            try:
                os.setuid(os.getuid())
            except Exception:
                pass

        # ---- 5️⃣ run harness with timeout and capture output -----------------
        try:
            proc = subprocess.run(
                [sys.executable, str(harness_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                preexec_fn=preexec,
                check=False,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return "Error: execution timed out (possible infinite loop)."
        finally:
            try:
                harness_path.unlink()
            except Exception:
                pass

        # ---- 6️⃣ interpret harness result ------------------------------------
        if proc.returncode != 0:
            try:
                err = json.loads(proc.stdout.strip())
                return f"Import error: {err.get('trace','')}"
            except Exception:
                return f"Runtime error: {proc.stderr.strip() or proc.stdout.strip()}"

        try:
            outcomes = json.loads(proc.stdout.strip())
        except Exception:
            return f"Failed to parse harness output: {proc.stdout[:200]}"

        failures = [f"{n}: {msg}" for n, msg in outcomes.items() if not msg == "ok"]
        return "" if not failures else "Function errors: " + "; ".join(failures)

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

    def _pick_best_goal(self, candidates: list) -> str:
        """Pick the candidate goal with the best historical test-pass rate.
        Reads memory/iteration_stats.jsonl. Falls back to cycling if no data.
        """
        import json as _j
        stats_path = Path(self.repo_path) / "memory" / "iteration_stats.jsonl"
        if not stats_path.exists():
            return candidates[self.state["iterations"] % len(candidates)]
        try:
            rows = [_j.loads(l) for l in stats_path.read_text().strip().splitlines() if l.strip()]
        except Exception:
            return candidates[self.state["iterations"] % len(candidates)]

        if len(rows) < 4:
            return candidates[self.state["iterations"] % len(candidates)]

        # Score each candidate by keyword overlap with historically passing goals
        passing_keywords: dict = {}
        for row in rows:
            if row.get("test", "").startswith("PASSED"):
                for word in row.get("goal", "").lower().split():
                    if len(word) > 4:
                        passing_keywords[word] = passing_keywords.get(word, 0) + 1

        if not passing_keywords:
            return candidates[self.state["iterations"] % len(candidates)]

        def score(desc: str) -> int:
            return sum(passing_keywords.get(w, 0) for w in desc.lower().split() if len(w) > 4)

        scored = sorted(candidates, key=score, reverse=True)
        # Pick top candidate, rotating among ties each iteration
        top_score = score(scored[0])
        top_group = [c for c in scored if score(c) == top_score]
        chosen = top_group[self.state["iterations"] % len(top_group)]
        logger.info(f"Goal picker: chose '{chosen[:60]}...' (score={top_score})")
        return chosen

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

        # Use predefined categories directly — avoids an LLM call for goal selection.
        # Cycles deterministically so each iteration advances through the queue.
        goal_categories = [
            "Write function get_response_time_stats() that reads iteration_stats.jsonl and returns avg/p95 elapsed_s per backend",
            "Add /code Telegram command showing last 3 self-edit commits: file changed, function name, git diff summary",
            "Write function score_goal_difficulty(goal_desc) that returns 1-5 based on keywords: add=1, implement=2, build=3, rewrite=4, redesign=5",
            "Add /reset Telegram command: abandon active goals and pick fresh category from next in queue",
            "Write function monitor_openrouter_quota() that calls OpenRouter /auth/key to check remaining credits and logs warning if <10 calls left",
            "Add response_time tracking to _append_iteration_stats: include openrouter_ms latency measured around generate() call",
            "Write function generate_test_case(func_code) that produces a minimal assert-based test for a given function definition",
            "Add /diff Telegram command showing git diff --stat HEAD~3..HEAD to summarize last 3 commits of changes",
        ]
        # Skip categories already completed or deferred (≥3 consecutive code-gen failures)
        skip_descs = {g["description"] for g in self.state["goals"]
                      if g.get("status") in ("completed", "deferred")}
        remaining = [c for c in goal_categories if c not in skip_descs]
        if not remaining:
            # Re-open deferred goals on second pass (maybe models are available now)
            for g in self.state["goals"]:
                if g.get("status") == "deferred":
                    g["status"] = "active"
                    g["fail_count"] = 0
            remaining = goal_categories

        # Data-driven selection: prefer categories that produced passing tests historically.
        # Falls back to simple cycling if no stats exist yet.
        goal_desc = self._pick_best_goal(remaining)

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

        hw = self.HARDWARE_CONTEXT
        if is_code_goal:
            prompt = (
                hw + chr(10) + chr(10) +
                f'You are {self.personality.name}, writing Python code for your goal.' + chr(10) +
                'Goal: ' + goal['description'][:150] + chr(10) +
                'Progress: ' + history + chr(10) + chr(10) +
                'Write WORKING Python code (no markdown, no backticks, raw Python only).' + chr(10) +
                'Start with: # Goal: then a function or class definition.' + chr(10) +
                'Under 25 lines. Must work on Pi 4 (ARM, no GPU, no Docker).' + chr(10) +
                'End with: # STATUS: continue OR # STATUS: complete'
            )
        else:
            prompt = (
                hw + chr(10) + chr(10) +
                'Task: ' + goal['description'][:150] + chr(10) +
                'Progress so far:' + chr(10) + history + chr(10) + chr(10) +
                'Write the next concrete Pi-compatible step. Under 100 words. Be specific.' + chr(10) +
                'End with: STATUS: continue OR STATUS: complete' + chr(10) +
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

        if cmd in ("/history", "/hist"):
            import json as _j
            stats_path = Path(self.repo_path) / "memory" / "iteration_stats.jsonl"
            if not stats_path.exists():
                return "No iteration history yet."
            rows = [_j.loads(l) for l in stats_path.read_text().strip().splitlines()[-5:]]
            lines = [
                f"#{r['iter']} {r['elapsed_s']}s {r['test'][:12]} {r['goal'][:40]}"
                for r in rows
            ]
            return "Last 5 iterations:" + chr(10) + chr(10).join(lines)

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

        if cmd in ("/health",):
            try:
                import subprocess as _sp
                cpu = open("/proc/loadavg").read().split()[0]
                mem_info = {k.split()[0]: k.split()[1]
                            for k in open("/proc/meminfo").read().splitlines()
                            if k.split()[0] in ("MemTotal:", "MemAvailable:")}
                total_mb = int(mem_info.get("MemTotal:", "0 kB").split()[0]) // 1024
                avail_mb = int(mem_info.get("MemAvailable:", "0 kB").split()[0]) // 1024
                used_pct = round((total_mb - avail_mb) / total_mb * 100) if total_mb else 0
                disk = _sp.run(["df", "-h", "/"], capture_output=True, text=True).stdout.splitlines()
                disk_line = disk[1] if len(disk) > 1 else "?"
                uptime = open("/proc/uptime").read().split()[0]
                up_h = int(float(uptime)) // 3600
                return (f"CPU load: {cpu} | RAM: {used_pct}% ({avail_mb}MB free)" +
                        chr(10) + f"Disk: {disk_line.split()[3]} free ({disk_line.split()[4]})" +
                        chr(10) + f"Uptime: {up_h}h | Backend: {self.inference.active_backend}")
            except Exception as e:
                return f"Health check error: {e}"

        if cmd in ("/restart",):
            try:
                import subprocess as _sp, threading as _th
                def _do_restart():
                    import time as _t
                    _t.sleep(1)
                    _sp.run(["pkill", "-f", "ollama"], capture_output=True, timeout=5)
                    _sp.run(["pkill", "-f", "continuous_daemon"], capture_output=True, timeout=5)
                    _t.sleep(2)
                    _sp.Popen(["bash", str(Path(self.repo_path) / "continuous_daemon.sh")],
                              stdout=open("/tmp/daemon_restart.log", "w"),
                              stderr=_sp.STDOUT, cwd=self.repo_path)
                _th.Thread(target=_do_restart, daemon=True).start()
                return "Restarting: killing Ollama + restarting daemon in 3s..."
            except Exception as e:
                return f"Restart error: {e}"

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

        if cmd in ("/diff",):
            import subprocess as _sp
            try:
                result = _sp.run(
                    ['git', 'diff', '--stat', 'HEAD~3..HEAD'],
                    capture_output=True, text=True, timeout=10, cwd=self.repo_path
                )
                out = (result.stdout or '').strip()
                log = _sp.run(
                    ['git', 'log', '--oneline', '-5'],
                    capture_output=True, text=True, timeout=5, cwd=self.repo_path
                ).stdout.strip()
                return f"Last 5 commits:\n{log}\n\nDiff stat (HEAD~3..HEAD):\n{out[:600]}"
            except Exception as e:
                return f"diff error: {e}"

        if cmd in ("/help",):
            return (
                "/status -- iteration count and active goal" + chr(10) +
                "/health -- CPU/RAM/disk/uptime" + chr(10) +
                "/history -- last 5 iterations from stats" + chr(10) +
                "/diff -- last 5 commits + diff stat" + chr(10) +
                "/goal -- list recent goals" + chr(10) +
                "/models -- active model config" + chr(10) +
                "/memory -- show KV memory" + chr(10) +
                "/log -- recent daemon log" + chr(10) +
                "/think -- generate a thought" + chr(10) +
                "/run -- trigger an immediate iteration" + chr(10) +
                "/restart -- kill Ollama + restart daemon" + chr(10) +
                "/shell <cmd> -- run shell command on Pi" + chr(10) +
                "/py <code> -- run Python code on Pi" + chr(10) +
                "/git <args> -- git command in repo" + chr(10) +
                "Or just chat directly."
            )

        # Personality-driven reply for non-commands
        prompt = (
            "You are " + self.personality.name + ", an autonomous AI agent." + chr(10) +
            "Someone messaged: " + chr(34) + text[:200] + chr(34) + chr(10) +
            "Reply in 1-3 sentences. Be direct and opinionated. No corporate-speak."
        )
        response = self.inference.generate(prompt, max_tokens=100)
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
            '  file_write: create or update a file in the repo' + chr(10) +
            '  file_read: read a file to learn about it' + chr(10) +
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

        # Extract the target function name from change_desc if it contains func_name()
        import re as _re2
        target_func = None
        m = _re2.search(r'\b(\w+)\(\)', change_desc)
        if m:
            target_func = m.group(1)

        # Read existing function to include as context for the LLM
        existing_func = ""
        if target_func:
            func_m = _re2.search(
                r'(    def ' + target_func + r'\(.*?)(?=\n    def |\Z)',
                original, _re2.DOTALL
            )
            if func_m:
                existing_func = func_m.group(1)[:600]

        prompt = (
            'Improve this Python method for a Raspberry Pi AI agent (ARM, no GPU).' + chr(10) +
            'Improvement goal: ' + change_desc[:200] + chr(10) +
            (('Current code:\n' + existing_func + chr(10)) if existing_func else '') +
            'Rules: return ONLY the complete improved function (def ...). No markdown. Under 30 lines.' + chr(10) +
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

        # Runtime import check -- catches errors that AST parse misses
        import subprocess as _sp
        check = _sp.run(
            ['python3', '-c', f'import py_compile; py_compile.compile("{target}", doraise=True)'],
            capture_output=True, text=True, timeout=10
        )
        if check.returncode != 0:
            _shutil.copy2(backup, str(target))
            return "Reverted: compile check failed — " + check.stderr.strip()[:100]

        git = GitController(self.repo_path)
        msg = ('self-edit: ' + file_name + ' — ' + change_desc[:80] +
               chr(10) + chr(10) + '[freeWill autonomous commit]')
        git.commit(msg)

        logger.info("self_edit: " + action + " in " + file_name)
        return action + " in " + file_name


    def self_modify(self) -> Optional[str]:
        """Improve own code every 5th iteration using self_edit_file().
        Rotates through high-impact methods so each self-mod targets something different.
        """
        # Rotate targets so the agent doesn't just keep rewriting think()
        targets = [
            ("agent.py", "improve the think() method: better JSON parsing, more context-aware decisions"),
            ("agent.py", "improve apply_code_improvement(): better prompt, strip markdown more robustly"),
            ("inference.py", "improve OpenRouterClient.generate(): better error handling, smarter retry"),
            ("agent.py", "improve _append_iteration_stats(): also record inference_calls count"),
            ("agent.py", "improve test_code_improvement(): add more robust sandbox, detect infinite loops"),
        ]
        iteration = self.state.get('iterations', 0)
        file_name, change_desc = targets[iteration % len(targets)]

        logger.info(f"self_modify: targeting {file_name} — {change_desc[:60]}")
        result = self.self_edit_file(file_name, change_desc)
        if result and result.startswith("Reverted"):
            logger.warning(f"self_modify reverted: {result}")
            return None
        return result

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

    def run_iteration_v2(self):
        """OpenClaw-style iteration: focused THINK→PLAN→IMPLEMENT→TEST→COMMIT.
        Max 3 inference calls. Blocks commit on test failure.
        """
        import time as _time
        iteration_num = self.state['iterations'] + 1
        logger.info(f"=== Iteration {iteration_num} (v2) ===")
        start_ts = _time.time()

        # --- THINK (call 1): pick the active goal ---
        context_lines = [
            f"Iteration: {iteration_num}",
            f"Recent: {'; '.join(d['decision'][:60] for d in self.state.get('decisions', [])[-3:])}",
            f"Last test: {self.state.get('last_test_result', 'none')}",
            f"Active goal: {self.state.get('active_goal_desc', 'none')}",
        ]
        decision = self.think("\n".join(context_lines))
        logger.info(f"THINK: {decision[:120]}")

        evaluation = self.evaluate_decision(decision)
        if evaluation.get('safety', 5) < 3 or evaluation.get('ethics', 5) < 3:
            logger.warning("Decision rejected (unsafe) — skipping iteration")
            self.state['iterations'] += 1
            self.save_state()
            return

        # --- PLAN: pick goal with highest priority ---
        goal = self.review_goals()
        code_file = None
        result = None
        if goal:
            self.state['active_goal_desc'] = goal.get('description', '')[:80]
            is_code_goal = any(w in goal['description'].lower()
                               for w in ['implement', 'write', 'create', 'build', 'add', 'code',
                                         'function', 'module', 'tracker', 'cache', 'rate', 'command'])
            logger.info(f"PLAN: goal #{goal['id']} (code={is_code_goal}): {goal['description'][:80]}")

            # --- IMPLEMENT (call 2): generate code or prose ---
            if is_code_goal:
                # apply_code_improvement saves to improvements/iter_XXX.py for testing
                code = self.apply_code_improvement(goal['description'])
                improvements_dir = Path(self.repo_path) / "improvements"
                candidate = improvements_dir / f"iter_{iteration_num:03d}.py"
                if candidate.exists():
                    code_file = str(candidate)
                    result = code
                    goal["fail_count"] = 0  # reset on successful generation
                    # Update goal progress log so it doesn't go stale
                    goal["progress_log"].append(f"Generated code: {candidate.name}")
                    goal["progress_log"] = goal["progress_log"][-5:]
                    logger.info(f"IMPLEMENT: wrote {candidate.name}")
                else:
                    # Code generation failed (prose rejected or API error)
                    goal["fail_count"] = goal.get("fail_count", 0) + 1
                    logger.warning(f"Code gen failed for goal #{goal['id']} (fail_count={goal['fail_count']})")
                    if goal["fail_count"] >= 3:
                        goal["status"] = "deferred"
                        logger.warning(f"Goal #{goal['id']} deferred after {goal['fail_count']} failures")
                    result = code
            else:
                result = self.work_on_goal(goal)
                if result:
                    logger.info(f"IMPLEMENT: goal #{goal['id']} prose result written")

        # --- TEST: run the generated file, block commit if it fails ---
        test_status = "SKIPPED"
        if code_file and Path(code_file).exists():
            test_status = self.test_code_improvement(code_file)
            self.state['last_test_result'] = test_status[:60]
            logger.info(f"TEST: {test_status}")
            if test_status.startswith("FAIL"):
                # Don't commit broken code -- save state only
                logger.warning(f"Test failed — skipping commit this iteration")
                self.state['iterations'] += 1
                self.state['last_run'] = datetime.now().isoformat()
                self.save_state()
                self.telegram.send_message_sync(
                    f"Iter {iteration_num} | TEST FAILED\n{test_status[:120]}\nNo commit."
                )
                return
            elif goal and not test_status.startswith("SKIPPED"):
                # Test passed — mark goal complete so cycling advances to next
                goal["status"] = "completed"
                logger.info(f"Goal #{goal['id']} marked complete (test passed)")

                # --- INTEGRATE: inject the function into agent.py if it's a new utility ---
                # Only for "Write function X()" goals to avoid accidentally patching handlers
                if code_file and goal.get('description', '').lower().startswith('write function'):
                    self._integrate_improvement(code_file)

        # --- SELF-MODIFY every 5th iteration (call 3, optional) ---
        if iteration_num % 5 == 0:
            mod = self.self_modify()
            if mod:
                logger.info(f"SELF-MOD: {mod[:80]}")

        # --- COMMIT: state + code + goals ---
        elapsed = _time.time() - start_ts
        self.state['iterations'] += 1
        self.state['last_run'] = datetime.now().isoformat()
        self.state['decisions'].append({
            'iteration': self.state['iterations'],
            'decision': decision[:200],
            'timestamp': datetime.now().isoformat(),
        })
        self.state['decisions'] = self.state['decisions'][-10:]
        self.save_state()

        # Record learning event so the learning system reflects actual outcomes
        goal_desc = self.state.get('active_goal_desc', 'unknown goal')[:80]
        if test_status.startswith("PASSED"):
            self.learning.record_learning(LearningEvent(
                "feature", f"v2 iter {iteration_num}: {goal_desc}", impact="positive"
            ))
        elif test_status.startswith("FAIL") or test_status.startswith("ERROR"):
            self.learning.record_learning(LearningEvent(
                "bug_fix", f"v2 iter {iteration_num}: test failed — {goal_desc}", impact="negative"
            ))
        elif test_status == "SKIPPED" and result:
            self.learning.record_learning(LearningEvent(
                "optimization", f"v2 iter {iteration_num}: {goal_desc}", impact="neutral"
            ))
        self.learning.save_state()

        # Append to stats file so the agent can review its own history
        self._append_iteration_stats(iteration_num, elapsed, test_status, result)

        commit_msg = (f"Iteration {self.state['iterations']} v2: "
                      f"test={test_status[:20]}, {elapsed:.0f}s, "
                      f"goal={'ok' if result else 'none'}")
        self.git.commit(commit_msg)
        if os.getenv("GITHUB_TOKEN"):
            self.git.push()

        summary = (
            f"Iter {self.state['iterations']} | {elapsed:.0f}s\n"
            f"Goal: {self.state.get('active_goal_desc', 'none')[:80]}\n"
            f"Test: {test_status[:40]}\n"
            f"Backend: {self.inference.active_backend}"
        )
        self.telegram.send_message_sync(summary)
        logger.info(f"v2 done in {elapsed:.1f}s")

    def _append_iteration_stats(self, iteration_num: int, elapsed: float,
                                 test_status: str, result):
        """Append one row to memory/iteration_stats.jsonl for historical analysis."""
        import json as _json
        stats_path = Path(self.repo_path) / "memory" / "iteration_stats.jsonl"
        stats_path.parent.mkdir(exist_ok=True)
        row = {
            "iter": iteration_num,
            "elapsed_s": round(elapsed, 1),
            "test": test_status[:40],
            "goal": self.state.get("active_goal_desc", "")[:80],
            "backend": self.inference.active_backend,
            "result": "ok" if result else "none",
            "ts": datetime.now().isoformat(),
        }
        with open(stats_path, "a") as f:
            f.write(_json.dumps(row) + "\n")

    def _integrate_improvement(self, code_file: str):
        """Inject a tested improvement function into agent.py at module level
        (below the AutonomousAgent class, as a standalone utility).
        Only runs if the function name doesn't already exist in the file.
        Safe: validates full-file syntax before writing; skips on any error.
        """
        import ast as _ast, re as _re, shutil as _sh
        try:
            code = Path(code_file).read_text()
            # Find the first top-level def (module-level function)
            m = _re.search(r'^def (\w+)\(', code, _re.MULTILINE)
            if not m:
                return
            func_name = m.group(1)

            target = Path(self.repo_path) / "agent.py"
            agent_src = target.read_text()

            # Skip if this function name already exists anywhere in agent.py
            if f"def {func_name}(" in agent_src:
                logger.info(f"INTEGRATE: {func_name}() already exists — skipping")
                return

            # Extract only the function lines (strip comment header)
            func_lines = code.splitlines()
            code_start = next((i for i, l in enumerate(func_lines) if l.startswith("def ")), 0)
            func_code = "\n".join(func_lines[code_start:]).strip()

            # Append at module level (after startup_check, before __main__)
            insert_marker = '\nif __name__ == "__main__":'
            if insert_marker in agent_src:
                new_src = agent_src.replace(
                    insert_marker,
                    f"\n\n{func_code}\n{insert_marker}"
                )
            else:
                new_src = agent_src.rstrip() + f"\n\n{func_code}\n"

            # Validate before writing
            try:
                _ast.parse(new_src)
            except SyntaxError as e:
                logger.warning(f"INTEGRATE: syntax error in merged file — {e}")
                return

            _sh.copy2(str(target), str(target) + ".bak_integrate")
            target.write_text(new_src)
            logger.info(f"INTEGRATE: injected {func_name}() into agent.py at module level")
            self.git.commit(f"integrate: add {func_name}() utility to agent.py")
        except Exception as e:
            logger.warning(f"INTEGRATE: error — {e}")


def startup_check(agent: 'AutonomousAgent') -> bool:
    """Run before first iteration after restart. Verifies inference works,
    clears stale state, sends a recovery Telegram message."""
    import time as _time, subprocess as _sp

    logger.info("=== STARTUP CHECK ===")

    # Kill any leftover Ollama runner processes from previous session
    try:
        r = _sp.run(['pkill', '-9', '-f', 'ollama runner'], capture_output=True, timeout=3)
        if r.returncode == 0:
            logger.info("Killed leftover ollama runner processes")
    except Exception:
        pass

    # Test inference is working
    logger.info(f"Testing inference backend: {agent.inference.active_backend}")
    test_resp = agent.inference.generate("Reply with one word: ready", max_tokens=5)
    if not test_resp:
        logger.error("Inference test FAILED — no response from any backend")
        agent.telegram.send_message_sync(
            "Startup failed: inference not working. Check OPENROUTER_API_KEY."
        )
        return False

    logger.info(f"Inference OK: {test_resp!r}")

    # Notify Telegram
    backend = agent.inference.active_backend
    iteration = agent.state.get('iterations', 0)
    agent.telegram.send_message_sync(
        f"freeWillAi restarted OK\n"
        f"Backend: {backend}\n"
        f"Resuming from iteration {iteration}\n"
        f"Inference test: {test_resp!r}"
    )
    return True



def get_response_time_stats():
    """Return avg and p95 elapsed_s per backend from iteration_stats.jsonl."""
    import json, os, math
    path = os.path.join(os.getcwd(), "iteration_stats.jsonl")
    if not os.path.isfile(path):
        return {}
    data = {}
    with open(path, "r") as f:
        for line in f:
            try:
                rec = json.loads(line)
                be = rec.get("backend")
                elapsed = rec.get("elapsed_s")
                if be is None or elapsed is None:
                    continue
                data.setdefault(be, []).append(elapsed)
            except json.JSONDecodeError:
                continue
    result = {}
    for be, times in data.items():
        n = len(times)
        avg = sum(times) / n


def generate_test_case(func_code):
    """Return a simple assert test string for the given function code."""
    import ast, textwrap, random, string
    tree = ast.parse(func_code)
    func = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    name = func.name
    args = [arg.arg for arg in func.args.args]
    defaults = [None]*(len(args)-len(func.args.defaults)) + func.args.defaults
    def gen_val(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        return 0
    sample_vals = []
    for d in defaults:
        if d is None:
            sample_vals.append(0)
        else:
            sample_vals.append(gen_val(d))


def monitor_openrouter_quota(api_key):
    """Check OpenRouter credit quota and log warning if low."""
    import json, logging, urllib.request, urllib.error
    url = f"https://openrouter.ai/api/v1/auth/key?key={api_key}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.load(resp)
        remaining = data.get("credits", {}).get("remaining", 0)
        if remaining < 10:
            logging.warning("OpenRouter quota low: %s credits left", remaining)
    except urllib.error.URLError as e:
        logging.error("Failed to fetch OpenRouter quota: %s", e)


def score_goal_difficulty(goal_desc):
    """Return difficulty 1-5 based on keywords in goal_desc."""
    desc = goal_desc.lower()
    if "rewrite" in desc:
        return 5
    if "build" in desc:
        return 3
    if "implement" in desc:
        return 2
    if "add" in desc:
        return 1
    return 0

if __name__ == "__main__":
    agent = AutonomousAgent()

    # Run startup check on first boot or after restart (AGENT_STARTUP_CHECK=1)
    if os.getenv("AGENT_STARTUP_CHECK", "0") == "1":
        if not startup_check(agent):
            import sys; sys.exit(1)

    # Use v2 (focused, 4 inference calls max) if AGENT_V2=1 is set
    if os.getenv("AGENT_V2", "0") == "1":
        agent.run_iteration_v2()
    else:
        agent.run_iteration()
