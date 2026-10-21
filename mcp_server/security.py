from __future__ import annotations

import os
from pathlib import Path

EXCLUDED = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
DISALLOWED = {".env", ".env.local", "id_rsa", "id_ed25519"}


class SecurityError(ValueError):
    """Raised when an operation violates the repository boundary."""


def allowed_root() -> Path:
    configured = os.environ.get("DEVFLOW_ALLOWED_WORKSPACE_ROOT")
    return Path(configured).expanduser().resolve() if configured else Path.cwd().resolve()


def project_root(project_path: str) -> Path:
    candidate = Path(project_path).expanduser()
    if not candidate.is_absolute():
        candidate = allowed_root() / candidate
    resolved = candidate.resolve()
    root = allowed_root()
    if resolved != root and root not in resolved.parents:
        raise SecurityError("Project is outside the approved workspace")
    if not resolved.exists() or not resolved.is_dir():
        raise SecurityError("Project directory does not exist")
    return resolved


def safe_file(project_path: str, relative_path: str, max_size: int = 200_000) -> Path:
    root = project_root(project_path)
    supplied = Path(relative_path)
    if supplied.is_absolute():
        candidate = supplied.resolve()
    else:
        candidate = (root / supplied).resolve()
    if candidate != root and root not in candidate.parents:
        raise SecurityError("Path is outside the selected project")
    if candidate.name in DISALLOWED or candidate.suffix.lower() in {".pem", ".key"}:
        raise SecurityError("Sensitive files are not permitted")
    if not candidate.exists():
        raise FileNotFoundError(relative_path)
    if not candidate.is_file():
        raise SecurityError("Expected a file path")
    if candidate.stat().st_size > max_size:
        raise SecurityError("File exceeds the configured size limit")
    return candidate


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()
