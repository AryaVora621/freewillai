# Auto-generated improvement — Iteration 52
# Suggestion: Use f-string formatting instead of `str.format()`:

def read_sensor_data(sensor_id: int, temperature: float, humidity: float) -> str:
    timestamp = __import__('datetime').datetime.now().isoformat()
    status = "OK" if 0 <= temperature <= 50 and 0 <= humidity <= 100 else "ERROR"
    return f"sensor_{sensor_id}: temp={temperature:.1f}C hum={humidity:.1f}% status={status} time={timestamp}"
