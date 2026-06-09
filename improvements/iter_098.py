# Auto-generated improvement — Iteration 98
# Suggestion: Add type hinting for the `is_available` method

def is_available(pin: int) -> bool:
    """Check if GPIO pin is available."""
    try:
        with open(f"/sys/class/gpio/gpio{pin}/direction", "r") as f:
            f.read()
        return True
    except FileNotFoundError:
        return False
