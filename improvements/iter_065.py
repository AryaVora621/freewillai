# Auto-generated improvement — Iteration 65
# Suggestion: Use a conditional expression instead of multiple if statements

def The user wants a short Python function for Raspberry Pi that uses a conditional expression (ternary operator) instead of multiple if statements. Max 20 lines, no docstring longer than 1 line, stdlib only. Stop after closing return statement. No extra code.

I need to write a function that demonstrates conditional expression usage. Since it's for Raspberry Pi, maybe something GPIO-related but using stdlib only (no RPi.GPIO). Could simulate reading a sensor or controlling an LED with a mock.

But stdlib only, so no hardware access. Could be a function that returns a status based on input using ternary.

Let's create a function that takes a temperature and returns fan speed using conditional expression.

Max 20 lines including def line. No docstring longer than 1 line. So maybe a one-line docstring.

Function:

def fan_speed(temp):
    """Return fan speed based on temperature."""
    return "high" if temp > 30 else "medium" if temp > 20 else "low"

That's 3 lines. But need to stop after closing return statement. That's fine.

But the user said "Write a short Python function (max 20 lines) for a Raspberry Pi." Could be more realistic: maybe reading a file or something. But stdlib only.

I'll write a function that returns LED state based on button press simulation.
