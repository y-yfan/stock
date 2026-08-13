from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    cache_dir: Path = field(default_factory=lambda: Path.cwd() / "data_cache")
    max_retries: int = 3
    retry_wait: float = 1.0
    retry_max_wait: float = 30.0
    rate_limit_seconds: float = 1.0
    default_source: str = "akshare"

    def ensure_cache_dir(self) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir


default_config = Config()
