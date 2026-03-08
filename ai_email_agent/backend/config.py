import os
from typing import List


def _split_env_list(value: str, default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


APP_ENV = os.getenv("APP_ENV", "development").lower()

CORS_ORIGINS = _split_env_list(
    os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
    ["http://localhost:3000", "http://127.0.0.1:3000"],
)

# Optional: allow open access when explicitly requested
ALLOW_ALL_ORIGINS = os.getenv("ALLOW_ALL_ORIGINS", "false").lower() in ("1", "true", "yes")
