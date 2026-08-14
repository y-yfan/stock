from __future__ import annotations

import logging

import pandas as pd

from .cache import SQLiteCache
from .config import Config
from .sources import AkShareSource, DataSource
from .sources.akshare_source import (
    SPOT_SOURCES,
    HISTORY_SOURCES,
    MINUTES_SOURCES,
    FUND_FLOW_SOURCES,
    INFO_SOURCES,
    MARKET_FUND_FLOW_SOURCES,
    SECTOR_FUND_FLOW_RANK_SOURCES,
    INDIVIDUAL_FUND_FLOW_RANK_SOURCES,
    BOARD_INDUSTRY_LIST_SOURCES,
    BOARD_CONCEPT_LIST_SOURCES,
    BOARD_INDUSTRY_CONS_SOURCES,
    BOARD_CONCEPT_CONS_SOURCES,
    BOARD_INDUSTRY_HIST_SOURCES,
    BOARD_CONCEPT_HIST_SOURCES,
    HSGT_HIST_SOURCES,
    HSGT_HOLD_STOCK_SOURCES,
    LHB_DETAIL_SOURCES,
    ZT_POOL_SOURCES,
    STOCK_NEWS_SOURCES,
    FINANCIAL_INDICATOR_SOURCES,
    BALANCE_SHEET_SOURCES,
    PROFIT_SHEET_SOURCES,
    CASH_FLOW_SHEET_SOURCES,
    DIVIDEND_SOURCES,
    RESTRICTED_RELEASE_SOURCES,
    HOT_RANK_SOURCES,
)

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self, config: Config | None = None, source: DataSource | None = None):
        self.config = config or Config()
        self.source: DataSource = source or AkShareSource(
            rate_limit=self.config.rate_limit_seconds,
            max_retries=self.config.max_retries,
        )
        self.cache = SQLiteCache(self.config)

    def _try_sources(self, sources: dict[str, str], fetch_fn, source: str | None):
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
        if not force_refresh:
            cached, cached_src = self.cache.read(cache_ns, cache_params)
            if cached is not None:
                src_desc = sources.get(cached_src, cached_src)
                return cached, src_desc

        df, used = self._try_sources(sources, fetch_fn, source)
        src_key = used.split("(")[0]
        self.cache.write(cache_ns, cache_params, df, source=src_key)
        return df, used

    # --- 行情 ---

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

    # --- 资金 ---

    def fund_flow(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_fund_flow(symbol, source=src)

        return self._fetch_with_cache("fund_flow", {"symbol": symbol}, FUND_FLOW_SOURCES, fetch, source, force_refresh)

    def market_fund_flow(self, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_market_fund_flow(source=src)

        return self._fetch_with_cache("market_fund_flow", {}, MARKET_FUND_FLOW_SOURCES, fetch, source, force_refresh)

    def sector_fund_flow_rank(self, indicator: str = "今日", sector_type: str = "行业资金流", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_sector_fund_flow_rank(indicator, sector_type, source=src)

        params = {"indicator": indicator, "sector_type": sector_type}
        return self._fetch_with_cache("sector_fund_flow_rank", params, SECTOR_FUND_FLOW_RANK_SOURCES, fetch, source, force_refresh)

    def individual_fund_flow_rank(self, indicator: str = "5日", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_individual_fund_flow_rank(indicator, source=src)

        return self._fetch_with_cache("individual_fund_flow_rank", {"indicator": indicator}, INDIVIDUAL_FUND_FLOW_RANK_SOURCES, fetch, source, force_refresh)

    # --- 板块 ---

    def board_industry_list(self, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_board_industry_list(source=src)

        return self._fetch_with_cache("board_industry_list", {}, BOARD_INDUSTRY_LIST_SOURCES, fetch, source, force_refresh)

    def board_concept_list(self, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_board_concept_list(source=src)

        return self._fetch_with_cache("board_concept_list", {}, BOARD_CONCEPT_LIST_SOURCES, fetch, source, force_refresh)

    def board_industry_cons(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_board_industry_cons(symbol, source=src)

        return self._fetch_with_cache("board_industry_cons", {"symbol": symbol}, BOARD_INDUSTRY_CONS_SOURCES, fetch, source, force_refresh)

    def board_concept_cons(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_board_concept_cons(symbol, source=src)

        return self._fetch_with_cache("board_concept_cons", {"symbol": symbol}, BOARD_CONCEPT_CONS_SOURCES, fetch, source, force_refresh)

    def board_industry_hist(self, symbol: str, start_date: str, end_date: str, period: str = "日k", adjust: str = "", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_board_industry_hist(symbol, start_date, end_date, period, adjust, source=src)

        params = {"symbol": symbol, "start": start_date, "end": end_date, "period": period, "adjust": adjust}
        return self._fetch_with_cache("board_industry_hist", params, BOARD_INDUSTRY_HIST_SOURCES, fetch, source, force_refresh)

    def board_concept_hist(self, symbol: str, start_date: str, end_date: str, period: str = "daily", adjust: str = "", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_board_concept_hist(symbol, start_date, end_date, period, adjust, source=src)

        params = {"symbol": symbol, "start": start_date, "end": end_date, "period": period, "adjust": adjust}
        return self._fetch_with_cache("board_concept_hist", params, BOARD_CONCEPT_HIST_SOURCES, fetch, source, force_refresh)

    # --- 沪深港通 ---

    def hsgt_hist(self, symbol: str = "沪股通", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_hsgt_hist(symbol, source=src)

        return self._fetch_with_cache("hsgt_hist", {"symbol": symbol}, HSGT_HIST_SOURCES, fetch, source, force_refresh)

    def hsgt_hold_stock(self, market: str = "北向", indicator: str = "5日排行", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_hsgt_hold_stock(market, indicator, source=src)

        params = {"market": market, "indicator": indicator}
        return self._fetch_with_cache("hsgt_hold_stock", params, HSGT_HOLD_STOCK_SOURCES, fetch, source, force_refresh)

    # --- 龙虎榜 ---

    def lhb_detail(self, start_date: str, end_date: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_lhb_detail(start_date, end_date, source=src)

        params = {"start": start_date, "end": end_date}
        return self._fetch_with_cache("lhb_detail", params, LHB_DETAIL_SOURCES, fetch, source, force_refresh)

    # --- 涨停板 ---

    def zt_pool(self, date: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_zt_pool(date, source=src)

        return self._fetch_with_cache("zt_pool", {"date": date}, ZT_POOL_SOURCES, fetch, source, force_refresh)

    # --- 新闻 ---

    def stock_news(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_stock_news(symbol, source=src)

        return self._fetch_with_cache("stock_news", {"symbol": symbol}, STOCK_NEWS_SOURCES, fetch, source, force_refresh)

    # --- 财务 ---

    def financial_indicator(self, symbol: str, indicator: str = "按报告期", force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_financial_indicator(symbol, indicator, source=src)

        params = {"symbol": symbol, "indicator": indicator}
        return self._fetch_with_cache("financial_indicator", params, FINANCIAL_INDICATOR_SOURCES, fetch, source, force_refresh)

    def balance_sheet(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_balance_sheet(symbol, source=src)

        return self._fetch_with_cache("balance_sheet", {"symbol": symbol}, BALANCE_SHEET_SOURCES, fetch, source, force_refresh)

    def profit_sheet(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_profit_sheet(symbol, source=src)

        return self._fetch_with_cache("profit_sheet", {"symbol": symbol}, PROFIT_SHEET_SOURCES, fetch, source, force_refresh)

    def cash_flow_sheet(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_cash_flow_sheet(symbol, source=src)

        return self._fetch_with_cache("cash_flow_sheet", {"symbol": symbol}, CASH_FLOW_SHEET_SOURCES, fetch, source, force_refresh)

    # --- 分红/解禁 ---

    def dividend(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_dividend(symbol, source=src)

        return self._fetch_with_cache("dividend", {"symbol": symbol}, DIVIDEND_SOURCES, fetch, source, force_refresh)

    def restricted_release(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_restricted_release(symbol, source=src)

        return self._fetch_with_cache("restricted_release", {"symbol": symbol}, RESTRICTED_RELEASE_SOURCES, fetch, source, force_refresh)

    # --- 人气 ---

    def hot_rank(self, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_hot_rank(source=src)

        return self._fetch_with_cache("hot_rank", {}, HOT_RANK_SOURCES, fetch, source, force_refresh)

    # --- 个股信息 ---

    def stock_info(self, symbol: str, force_refresh: bool = False, source: str | None = None) -> tuple[pd.DataFrame, str]:
        def fetch(src: str) -> pd.DataFrame:
            return self.source.get_stock_info(symbol, source=src)

        return self._fetch_with_cache("stock_info", {"symbol": symbol}, INFO_SOURCES, fetch, source, force_refresh)
