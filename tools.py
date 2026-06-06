#!/usr/bin/env python3
"""
Autonomous tool registry for freeWillAi — openclaw-alternative tool execution.

Tools the agent can call based on its own decision-making, not just predefined routines.
"""

import subprocess
import logging
import re
import json
import requests
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

TOOLS = {
    "shell": "Run a shell command and return output (5s timeout)",
    "write_file": "Write content to a file (path relative to repo)",
    "read_file": "Read content of a file (path relative to repo)",
    "web_fetch": "Fetch text content from a URL",
    "git_commit": "Commit all changed files with a message",
    "append_memory": "Append a note to long-term memory file",
}

TOOL_SCHEMA = """
You can call ONE tool to act autonomously. Choose the most useful action.

Available tools:
- shell(cmd): Run a Linux shell command (read-only or file-writing commands only; no destructive rm or kill)
- write_file(path, content): Write content to a file in the repo
- read_file(path): Read a file from the repo
- web_fetch(url): Fetch the text content of a web page
- git_commit(message): Stage all changes and commit with a message
- append_memory(note): Save a persistent note to memory/notes.md

Reply ONLY with valid JSON on a single line, for example:
{"tool": "shell", "args": {"cmd": "pip list | grep torch"}}
{"tool": "web_fetch", "args": {"url": "https://ollama.com/library"}}
{"tool": "write_file", "args": {"path": "notes/research.md", "content": "# Research\\n..."}}
{"tool": "git_commit", "args": {"message": "feat: add research notes"}}
{"tool": "append_memory", "args": {"note": "Discovered that qwen2.5:0.5b runs at 12 tok/s on Pi"}}
{"tool": "none", "args": {}}

"""


def execute_tool(tool_name: str, args: dict, repo_path: str = "/home/pi/freeWillAi") -> str:
    """Dispatch a tool call and return result string."""
    try:
        if tool_name == "shell":
            cmd = args.get("cmd", "")
            if not cmd:
                return "ERROR: no cmd provided"
            # Block dangerous patterns
            dangerous = ["rm -rf", "sudo", "dd if=", "mkfs", ":(){ ", "> /dev/"]
            if any(d in cmd for d in dangerous):
                return f"BLOCKED: command contains dangerous pattern"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=8, cwd=repo_path,
                env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": "/home/pi"}
            )
            out = (result.stdout or result.stderr or "").strip()[:500]
            return f"EXIT {result.returncode}: {out}"

        elif tool_name == "write_file":
            path = args.get("path", "")
            content = args.get("content", "")
            if not path:
                return "ERROR: no path"
            full_path = Path(repo_path) / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            return f"Wrote {len(content)} chars to {path}"

        elif tool_name == "read_file":
            path = args.get("path", "")
            full_path = Path(repo_path) / path
            if not full_path.exists():
                return f"ERROR: {path} not found"
            return full_path.read_text()[:800]

        elif tool_name == "web_fetch":
            url = args.get("url", "")
            if not url.startswith("http"):
                return "ERROR: invalid URL"
            resp = requests.get(url, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0 (compatible; freeWillAi/1.0)"})
            if resp.status_code != 200:
                return f"HTTP {resp.status_code}"
            from html.parser import HTMLParser
            class TextExtract(HTMLParser):
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
            p = TextExtract()
            p.feed(resp.text)
            return " ".join(p.text)[:700]

        elif tool_name == "git_commit":
            message = args.get("message", "auto: agent self-improvement")
            result = subprocess.run(
                f"git -C {repo_path} add -A && git -C {repo_path} commit -m '{message}'",
                shell=True, capture_output=True, text=True, timeout=15
            )
            return (result.stdout or result.stderr or "").strip()[:200]

        elif tool_name == "append_memory":
            note = args.get("note", "")
            mem_file = Path(repo_path) / "memory" / "notes.md"
            mem_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mem_file, "a") as f:
                from datetime import datetime
                f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{note}\n")
            return f"Memory updated"

        elif tool_name == "none":
            return "No action taken"

        else:
            return f"ERROR: unknown tool '{tool_name}'"

    except subprocess.TimeoutExpired:
        return "TIMEOUT: command exceeded time limit"
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return f"ERROR: {e}"


def parse_tool_call(response: str) -> Optional[dict]:
    """Extract JSON tool call from LLM response text."""
    # Try direct JSON parse first
    response = response.strip()
    try:
        obj = json.loads(response)
        if "tool" in obj:
            return obj
    except Exception:
        pass
    # Find JSON blob in response
    match = re.search(r'\{[^{}]+\}', response)
    if match:
        try:
            obj = json.loads(match.group())
            if "tool" in obj:
                return obj
        except Exception:
            pass
    return None
