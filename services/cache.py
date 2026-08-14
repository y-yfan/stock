from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Config

# 各 namespace 的默认 TTL(秒)
DEFAULT_TTL: dict[str, int] = {
    "spot": 60,                        # 实时行情: 1 分钟
    "hot_rank": 300,                   # 人气排名: 5 分钟
    "market_fund_flow": 300,           # 大盘资金流: 5 分钟
    "sector_fund_flow_rank": 300,      # 板块资金流排名: 5 分钟
    "individual_fund_flow_rank": 300,  # 个股资金流排名: 5 分钟
    "board_industry_list": 3600,       # 行业板块列表: 1 小时
    "board_concept_list": 3600,        # 概念板块列表: 1 小时
    "board_industry_cons": 1800,       # 行业板块成分: 30 分钟
    "board_concept_cons": 1800,        # 概念板块成分: 30 分钟
    "fund_flow": 300,                  # 个股资金流: 5 分钟
    "hsgt_hist": 1800,                 # 沪深港通历史: 30 分钟
    "hsgt_hold_stock": 1800,           # 沪深港通持股: 30 分钟
    "zt_pool": 300,                    # 涨停池: 5 分钟
    "lhb_detail": 1800,                # 龙虎榜: 30 分钟
    "stock_news": 600,                 # 新闻: 10 分钟
    "stock_info": 86400,               # 个股信息: 1 天
    "history": 86400,                  # 历史K线: 1 天
    "minutes": 60,                     # 分钟K线: 1 分钟
    "financial_indicator": 86400,      # 财务指标: 1 天
    "balance_sheet": 86400,            # 资产负债表: 1 天
    "profit_sheet": 86400,             # 利润表: 1 天
    "cash_flow_sheet": 86400,          # 现金流量表: 1 天
    "dividend": 86400,                 # 分红: 1 天
    "restricted_release": 86400,       # 解禁: 1 天
    "board_industry_hist": 86400,      # 行业板块历史: 1 天
    "board_concept_hist": 86400,       # 概念板块历史: 1 天
}
FALLBACK_TTL = 300  # 未配置的 namespace 默认 5 分钟


class SQLiteCache:
    def __init__(self, config: Config):
        self.config = config
        config.ensure_cache_dir()
        self.db_path = config.cache_dir / "stock_cache.db"
        self._init_db()

    def _init_db(self):
        with self._conn() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key   TEXT PRIMARY KEY,
                    ns    TEXT NOT NULL,
                    data  TEXT NOT NULL,
                    src   TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL,
                    expire_at   REAL
                )
            """)
            cols = {r[1] for r in con.execute("PRAGMA table_info(cache)")}
            if "src" not in cols:
                con.execute("ALTER TABLE cache ADD COLUMN src TEXT NOT NULL DEFAULT ''")
            con.execute("CREATE INDEX IF NOT EXISTS idx_ns ON cache(ns)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_expire ON cache(expire_at)")

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path), timeout=10)

    @staticmethod
    def _key(namespace: str, params: dict[str, Any]) -> str:
        raw = "|".join(f"{k}={v}" for k, v in sorted(params.items()))
        h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
        return f"{namespace}_{h}"

    def _ttl_for(self, namespace: str) -> int:
        return DEFAULT_TTL.get(namespace, FALLBACK_TTL)

    def read(self, namespace: str, params: dict[str, Any]) -> tuple[pd.DataFrame | None, str]:
        key = self._key(namespace, params)
        with self._conn() as con:
            row = con.execute(
                "SELECT data, src, expire_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None, ""
            data_json, src, expire_at = row
            if expire_at is not None and time.time() > expire_at:
                con.execute("DELETE FROM cache WHERE key = ?", (key,))
                return None, ""
            return pd.read_json(StringIO(data_json), orient="records"), src

    def write(self, namespace: str, params: dict[str, Any], df: pd.DataFrame, source: str = "") -> None:
        key = self._key(namespace, params)
        data_json = df.to_json(orient="records", force_ascii=False)
        ttl = self._ttl_for(namespace)
        now = time.time()
        expire_at = now + ttl
        with self._conn() as con:
            con.execute(
                """INSERT OR REPLACE INTO cache (key, ns, data, src, created_at, expire_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (key, namespace, data_json, source, now, expire_at),
            )

    def get_or_set(
        self,
        namespace: str,
        params: dict[str, Any],
        fetcher,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        if not force_refresh:
            cached, _ = self.read(namespace, params)
            if cached is not None:
                return cached
        df = fetcher()
        if df is not None and not df.empty:
            self.write(namespace, params, df)
        return df

    def cleanup(self) -> int:
        """删除所有过期缓存,返回删除行数。"""
        with self._conn() as con:
            cur = con.execute("DELETE FROM cache WHERE expire_at IS NOT NULL AND expire_at < ?", (time.time(),))
            return cur.rowcount
