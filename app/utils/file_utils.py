from pathlib import Path


def ensure_dirs(*paths: Path):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def safe_name(path: str) -> str:
    return Path(path).name.replace("..", "_")
