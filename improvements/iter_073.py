# Auto-generated improvement — Iteration 73
# Suggestion: Add docstrings and parameter types for variables that are used in the original code snippet, following PEP 257 (Python's official style guide).

def The user wants a Python function for a Raspberry Pi, max 20 lines, with docstrings and parameter types following PEP 257. Strict rules: max 20 lines total, no docstring longer than 1 line, stdlib only. Stop after the closing return statement. No extra code.

The user provided "def" as the start. I need to write a function definition with docstring and type hints. Since it's for Raspberry Pi, maybe something like reading a sensor or controlling GPIO. But must use stdlib only, so no RPi.GPIO or other libraries. However, the user said "for a Raspberry Pi" but stdlib only. Could be a function that does something generic, like reading a file or simulating a sensor. But the task: "Add docstrings and parameter types for variables that are used in the original code snippet". There's no original code snippet provided. The user just gave "def". Possibly they want me to create a function from scratch? The instruction: "Write a short Python function (max 20 lines) for a Raspberry Pi. Task: Add docstrings and parameter types for variables that are used in the original code snippet, following PEP 257". There's no original code snippet. Maybe they expect me to write a function that could be used on Raspberry Pi, with docstrings and type hints. Since no original snippet, I'll create a simple function that reads a temperature from a file (like /sys/class/thermal/thermal_zone0/temp) which is common on Raspberry Pi. That uses stdlib only.

I need to keep it under 20 lines total. Include function definition, docstring (one line), type hints, and return statement. No extra code after return.

Let's craft:

def read_cpu_temperature() -> float:
    """Read CPU temperature in Celsius from thermal zone."""
    with open("/sys/class/thermal/thermal_zone0
