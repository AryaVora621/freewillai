# Auto-generated improvement — Iteration 83
# Suggestion: Add `socket.settimeout(5)` for improved timeout handling

def create_socket():
    """Create a socket with 5-second timeout."""
    import socket
    s = socket.socket()
    s.settimeout(5)
    return s
