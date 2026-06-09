# Auto-generated improvement — Iteration 95
# Suggestion: Use a more Pythonic way of checking if an item exists in a collection using the `in` operator

def check_sensor_reading(readings, threshold):
    """Check if any sensor reading exceeds threshold."""
    return any(r > threshold for r in readings)

def is_pin_active(active_pins, pin):
    """Check if GPIO pin is in active set."""
    return pin in active_pins

def get_device_status(devices, device_id):
    """Return status if device exists, else None."""
    return devices.get(device_id) if device_id in devices else None
