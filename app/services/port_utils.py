def get_available_port(start: int = 8000, end: int = 8010) -> int:
    """Return the first available port in the given range (inclusive)."""
    import socket
    for p in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError(f"No available port in {start}-{end}")
