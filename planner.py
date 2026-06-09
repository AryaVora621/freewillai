#!/usr/bin/env python3
"""
Planner - multi-step goal execution engine
The "openclaw alternative" core: plans, executes, verifies, loops.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionPlan:
    """A sequence of tool calls with expected outcomes."""
    def __init__(self, goal: str, steps: list):
        self.goal = goal
        self.steps = steps  # list of {"tool": ..., "args": ..., "expected": ...}
        self.results = []
        self.status = "pending"  # pending | running | done | failed


class Planner:
    """
    Multi-step task planner. Given a goal, generates a plan of tool calls,
    executes them in sequence, verifies outcomes, and reports progress.

    This is the core of the openclaw-style agentic loop:
      think -> plan -> act -> verify -> reflect -> repeat
    """
    def __init__(self, inference_engine, repo_path: str = "."):
        self.inference = inference_engine
        self.repo_path = repo_path
        self.plan_history = []  # list of ExecutionPlan
        self.plan_log = Path(repo_path) / "memory" / "plans.jsonl"
        self.plan_log.parent.mkdir(exist_ok=True)

    def _log_plan(self, plan: ExecutionPlan):
        """Append plan execution to persistent log."""
        record = {
            "ts": datetime.now().isoformat(),
            "goal": plan.goal[:100],
            "steps": len(plan.steps),
            "results": plan.results,
            "status": plan.status,
        }
        with open(self.plan_log, "a") as f:
            f.write(json.dumps(record) + chr(10))

    def generate_plan(self, goal: str, context: str = "") -> Optional[ExecutionPlan]:
        """Ask the LLM to generate a 2-4 step tool execution plan."""
        from tools import TOOL_SCHEMA
        prompt = (
            "Generate a plan to accomplish this goal on a Raspberry Pi:" + chr(10) +
            goal[:150] + chr(10) +
            (("Context: " + context[:100] + chr(10)) if context else "") +
            chr(10) +
            "Available tools: shell(cmd), web_fetch(url), kv_set(key,value), " +
            "write_file(path,content - path must be a RELATIVE filename like output.txt), append_memory(note)" + chr(10) + "IMPORTANT: write_file paths must be relative filenames, never absolute paths like /home/*" + chr(10) +
            "Output a JSON array of 2-3 steps:" + chr(10) +
            '[{"tool":"shell","args":{"cmd":"ls"},"expected":"file list"},' +
            '{"tool":"kv_set","args":{"key":"result","value":"done"},"expected":"stored"}]' + chr(10) +
            "JSON only, no explanation:"
        )
        response = self.inference.generate(prompt, max_tokens=200)
        if not response:
            return None

        import json as _j
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = chr(10).join(l for l in lines if not l.strip().startswith("```")).strip()
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return None
        try:
            steps = _j.loads(text[start:end+1])
            if isinstance(steps, list) and steps:
                valid = [s for s in steps if isinstance(s, dict) and "tool" in s]
                if valid:
                    return ExecutionPlan(goal, valid[:4])
        except Exception:
            pass
        return None

    def execute(self, plan: ExecutionPlan) -> str:
        """Run plan steps in sequence, abort on failure."""
        from tools import execute_tool
        plan.status = "running"
        summary_parts = []

        for i, step in enumerate(plan.steps):
            tool = step.get("tool", "none")
            args = step.get("args", {})
            expected = step.get("expected", "")

            logger.info(f"Plan step {i+1}/{len(plan.steps)}: {tool}({args})")
            result = execute_tool(tool, args, repo_path=self.repo_path)
            logger.info(f"Result: {result[:80]}")

            step["result"] = result[:200]
            plan.results.append(f"{tool}: {result[:100]}")
            summary_parts.append(f"Step {i+1} ({tool}): {result[:60]}")

            # Abort on ERROR or BLOCKED
            if result.startswith("ERROR:") or result.startswith("BLOCKED:") or result.startswith("TIMEOUT"):
                plan.status = "failed"
                logger.warning(f"Plan aborted at step {i+1}: {result[:80]}")
                break
        else:
            plan.status = "done"

        self.plan_history.append(plan)
        self._log_plan(plan)
        return chr(10).join(summary_parts)

    def run_goal(self, goal: str, context: str = "") -> str:
        """Full cycle: generate plan, execute, return summary."""
        plan = self.generate_plan(goal, context)
        if not plan:
            logger.warning(f"Could not generate plan for: {goal[:80]}")
            return "Planning failed"
        logger.info(f"Plan generated: {len(plan.steps)} steps for: {goal[:60]}")
        return self.execute(plan)

    def get_history_summary(self, n: int = 5) -> str:
        """Return summary of recent plan executions."""
        recent = self.plan_history[-n:]
        if not recent:
            return "No plan history yet."
        lines = []
        for p in recent:
            lines.append(f"[{p.status}] {p.goal[:60]}: {' | '.join(p.results[:2])}")
        return chr(10).join(lines)
