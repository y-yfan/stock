from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Config


class ParquetCache:
    def __init__(self, config: Config):
        self.config = config
        self.root = config.ensure_cache_dir()

    def _key(self, namespace: str, params: dict[str, Any]) -> str:
        raw = "|".join(f"{k}={v}" for k, v in sorted(params.items()))
        h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
        return f"{namespace}_{h}"

    def _path(self, namespace: str, params: dict[str, Any]) -> Path:
        return self.root / f"{self._key(namespace, params)}.parquet"

    def exists(self, namespace: str, params: dict[str, Any]) -> bool:
        return self._path(namespace, params).exists()

    def read(self, namespace: str, params: dict[str, Any]) -> pd.DataFrame | None:
        p = self._path(namespace, params)
        if not p.exists():
            return None
        return pd.read_parquet(p)

    def write(self, namespace: str, params: dict[str, Any], df: pd.DataFrame) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        p = self._path(namespace, params)
        df.to_parquet(p, index=False)

    def get_or_set(
        self,
        namespace: str,
        params: dict[str, Any],
        fetcher,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        if not force_refresh:
            cached = self.read(namespace, params)
            if cached is not None:
                return cached
        df = fetcher()
        if df is not None and not df.empty:
            self.write(namespace, params, df)
        return df
