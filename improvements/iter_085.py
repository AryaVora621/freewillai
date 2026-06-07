# Auto-generated improvement — Iteration 85
# Suggestion: Add docstring to explain purpose of code transformation function

def transform_reading(raw_value: float, scale: float = 1.0, offset: float = 0.0) -> float:
    """Convert raw sensor reading to calibrated physical value using linear transformation."""
    if not isinstance(raw_value, (int, float)):
        raise TypeError("raw_value must be numeric")
    if scale == 0:
        raise ValueError("scale cannot be zero")
    calibrated = (raw_value * scale) + offset
    return round(calibrated, 4)
