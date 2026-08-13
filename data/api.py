from __future__ import annotations

import logging

import pandas as pd

from .cache import ParquetCache
from .config import Config
from .sources import AkShareSource, DataSource
from .sources.akshare_source import (
    SPOT_SOURCES,
    HISTORY_SOURCES,
    MINUTES_SOURCES,
    FUND_FLOW_SOURCES,
    INFO_SOURCES,
)

logger = logging.getLogger(__name__)


class DataAPI:
    def __init__(self, config: Config | None = None, source: DataSource | None = None):
        self.config = config or Config()
        self.source: DataSource = source or AkShareSource(
            rate_limit=self.config.rate_limit_seconds,
            max_retries=self.config.max_retries,
        )
        self.cache = ParquetCache(self.config)

    def _try_sources(self, sources: dict[str, str], fetch_fn, source: str | None):
        """尝试指定数据源,或遍历所有源直到成功。返回 (DataFrame, 实际使用的源描述)。"""
        if source:
            if source not in sources:
                raise ValueError(f"不支持的数据源 '{source}', 可选: {list(sources.keys())}")
            df = fetch_fn(source)
            return df, sources[source]

        last_err = None
        for src_key, src_desc in sources.items():
            try:
                df = fetch_fn(src_key)
                if df is not None and not df.empty:
                    return df, src_desc
            except Exception as e:
                last_err = e
                logger.warning(f"数据源 {src_desc} 失败: {e}")
                continue

        raise RuntimeError(f"所有数据源均失败, 最后错误: {last_err}")

    def _fetch_with_cache(self, cache_ns: str, cache_params: dict, sources: dict, fetch_fn, source: str | None, force_refresh: bool) -> tuple[pd.DataFrame, str]:
        """统一缓存+多源逻辑: 先查缓存,没有则拉取并缓存。返回 (DataFrame, 源描述)。"""
        if not force_refresh:
            cached = self.cache.read(cache_ns, cache_params)
            if cached is not None:
                # 缓存命中,从 cache_params 推断 source 描述
                src_key = cache_params.get("source", "")
                src_desc = sources.get(src_key, src_key)
                return cached, src_desc

        df, used = self._try_sources(sources, fetch_fn, source)
        src_key = used.split("(")[0]
        cache_params = {**cache_params, "source": src_key}
        self.cache.write(cache_ns, cache_params, df)
        return df, used

    def spot(self, symbol: str | None = None, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_spot(source=src)

        df, used = self._fetch_with_cache("spot", {"symbol": "all"}, SPOT_SOURCES, fetch, source, force_refresh)
        if symbol:
            code = symbol.lstrip("shsz.")
            col = "code" if "code" in df.columns else "代码"
            df = df[df[col].astype(str).str.contains(code)].reset_index(drop=True)
        return df, used

    def history(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: str = "qfq",
        force_refresh: bool = False,
        source: str | None = None,
    ) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_history(symbol, period, start_date, end_date, adjust, source=src)

        params = {"symbol": symbol, "period": period, "start": start_date or "", "end": end_date or "", "adjust": adjust}
        return self._fetch_with_cache("history", params, HISTORY_SOURCES, fetch, source, force_refresh)

    def minutes(
        self,
        symbol: str,
        period: str = "1",
        adjust: str = "qfq",
        force_refresh: bool = False,
        source: str | None = None,
    ) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_minutes(symbol, period, adjust, source=src)

        params = {"symbol": symbol, "period": period, "adjust": adjust}
        return self._fetch_with_cache("minutes", params, MINUTES_SOURCES, fetch, source, force_refresh)

    def fund_flow(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_fund_flow(symbol, source=src)

        return self._fetch_with_cache("fund_flow", {"symbol": symbol}, FUND_FLOW_SOURCES, fetch, source, force_refresh)

    def stock_info(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_stock_info(symbol, source=src)

        return self._fetch_with_cache("stock_info", {"symbol": symbol}, INFO_SOURCES, fetch, source, force_refresh)
