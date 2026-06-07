# Auto-generated improvement — Iteration 43
# Suggestion: 1. **Error Handling and Input Validation**: The current implementation does not handle potential errors that may occur during execution, such as permi

The user wants a Python function that implements error handling and input validation for a Raspberry Pi AI agent. They mention issues like permission problems with git commands and incorrect arguments. The rules are strict: raw Python only, no markdown, no triple backticks, no imports outside stdlib. Start directly with `def ` or `class `. Under 25 lines. Short docstring on first line.

I need to write a function that likely wraps a git command execution with proper error handling and input validation. Since it's for a Raspberry Pi AI agent, maybe it's about running git commands safely.

Constraints: under 25 lines, so concise. Use only stdlib. No external imports. So subprocess, os, sys, etc. are fine.

I'll create a function that runs a git command with validation and error handling.

Let's think: The function should take command arguments, validate them, run git via subprocess, handle permission errors, capture output, raise appropriate exceptions.

Docstring on first line.

I'll write:

def run_git_command(args: list[str], cwd: str | None = None) -> str:
    """Execute git command with validation and error handling."""
    if not args or not isinstance(args,
