from __future__ import annotations

import akshare as ak
import pandas as pd

from ..decorators import RateLimiter, with_retry
from .base import Adjust, DataSource, MinPeriod, Period

_PERIOD_MAP: dict[Period, str] = {
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "monthly",
}

_ADJUST_MAP: dict[Adjust, str] = {
    "qfq": "qfq",
    "hfq": "hfq",
    "": "",
}

# 每个接口支持的数据源
SPOT_SOURCES = {
    "tx": "腾讯财经(stock_zh_a_spot_tx)",
    "em": "东方财富(stock_zh_a_spot_em)",
    "sina": "新浪财经(stock_zh_a_spot)",
}

HISTORY_SOURCES = {
    "em": "东方财富(stock_zh_a_hist)",
    "tx": "腾讯财经(stock_zh_a_hist_tx)",
    "sina": "新浪财经(stock_zh_a_daily)",
}

MINUTES_SOURCES = {
    "em": "东方财富(stock_zh_a_hist_min_em)",
}

FUND_FLOW_SOURCES = {
    "em": "东方财富(stock_individual_fund_flow)",
}

INFO_SOURCES = {
    "em": "东方财富(stock_individual_info_em)",
}


class AkShareSource(DataSource):
    name = "akshare"

    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3):
        self._limiter = RateLimiter(rate_limit)
        self._max_retries = max_retries

    def _call(self, func, *args, **kwargs):
        self._limiter.wait()
        retried = with_retry(max_retries=self._max_retries)(func)
        return retried(*args, **kwargs)

    def get_spot(self, symbol: str | None = None, source: str = "tx") -> pd.DataFrame:
        source = source or "tx"
        if source == "em":
            df = self._call(ak.stock_zh_a_spot_em)
            if symbol:
                df = df[df["代码"] == symbol.lstrip("shsz.")].reset_index(drop=True)
        elif source == "sina":
            df = self._call(ak.stock_zh_a_spot)
            if symbol:
                df = df[df["代码"].str.contains(symbol.lstrip("shsz."))].reset_index(drop=True)
        else:
            df = self._call(ak.stock_zh_a_spot_tx)
            if symbol:
                df = df[df["code"].str.contains(symbol.lstrip("shsz."))].reset_index(drop=True)
        return df

    @staticmethod
    def _prefix_symbol(symbol: str) -> tuple[str, str]:
        """根据股票代码返回 (市场前缀, 带前缀代码)。如 000001 -> ('sz', 'sz000001')"""
        if symbol.startswith(("0", "3")):
            return "sz", f"sz{symbol}"
        return "sh", f"sh{symbol}"

    def get_history(
        self,
        symbol: str,
        period: Period = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: Adjust = "qfq",
        source: str = "em",
    ) -> pd.DataFrame:
        source = source or "em"
        if source == "tx":
            _, prefixed = self._prefix_symbol(symbol)
            df = self._call(
                ak.stock_zh_a_hist_tx,
                symbol=prefixed,
                start_date=start_date,
                end_date=end_date,
                adjust=_ADJUST_MAP[adjust],
            )
        elif source == "sina":
            _, prefixed = self._prefix_symbol(symbol)
            df = self._call(
                ak.stock_zh_a_daily,
                symbol=prefixed,
                start_date=start_date,
                end_date=end_date,
                adjust=_ADJUST_MAP[adjust],
            )
        else:
            df = self._call(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period=_PERIOD_MAP[period],
                start_date=start_date,
                end_date=end_date,
                adjust=_ADJUST_MAP[adjust],
            )
        return df

    def get_minutes(
        self,
        symbol: str,
        period: MinPeriod = "1",
        adjust: Adjust = "qfq",
        source: str = "em",
    ) -> pd.DataFrame:
        df = self._call(
            ak.stock_zh_a_hist_min_em,
            symbol=symbol,
            period=period,
            adjust=_ADJUST_MAP[adjust],
        )
        return df

    def get_fund_flow(self, symbol: str, source: str = "em") -> pd.DataFrame:
        market = "sz" if symbol.startswith(("0", "3")) else "sh"
        df = self._call(ak.stock_individual_fund_flow, stock=symbol, market=market)
        return df

    def get_stock_info(self, symbol: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_individual_info_em, symbol=symbol)
