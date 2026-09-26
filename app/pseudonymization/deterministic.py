import hashlib


def stable_key(value: str, seed: int = 20250925) -> str:
    return hashlib.sha256(f"{seed}:{value.casefold()}".encode()).hexdigest()[:16]
