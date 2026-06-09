# Auto-generated improvement — Iteration 76
# Suggestion: Use f-string formatting instead of string concatenation (Add).

def format_sensor_reading(pin: int, value: float, unit: str = "V") -> str:
    """Return formatted sensor reading using f-string."""
    timestamp = __import__("time").strftime("%H:%M:%S")
    status = "HIGH" if value > 1.65 else "LOW"
    return f"[{timestamp}] GPIO{pin}: {value:.3f}{unit} ({status})"
