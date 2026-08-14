from __future__ import annotations

import random
import time

import akshare as ak
import pandas as pd
import requests

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

# 同花顺资金流时间指标映射
_THS_PERIOD_MAP: dict[str, str] = {
    "今日": "即时",
    "3日": "3日排行",
    "5日": "5日排行",
    "10日": "10日排行",
    "20日": "20日排行",
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
    "sina": "新浪财经(stock_zh_a_minute)",
}

FUND_FLOW_SOURCES = {
    "em": "东方财富(stock_individual_fund_flow)",
    "ths": "同花顺(stock_fund_flow_individual)",
}

INFO_SOURCES = {
    "em": "东方财富(stock_individual_info_em)",
    "tx": "腾讯财经(stock_zh_a_spot_tx)",
}

MARKET_FUND_FLOW_SOURCES = {
    "em": "东方财富(stock_market_fund_flow)",
    "ths": "同花顺(stock_fund_flow_industry+concept)",
}

SECTOR_FUND_FLOW_RANK_SOURCES = {
    "em": "东方财富(stock_sector_fund_flow_rank)",
    "ths": "同花顺(stock_fund_flow_industry/concept)",
}

INDIVIDUAL_FUND_FLOW_RANK_SOURCES = {
    "em": "东方财富(stock_individual_fund_flow_rank)",
    "ths": "同花顺(stock_fund_flow_individual)",
}

BOARD_INDUSTRY_LIST_SOURCES = {
    "em": "东方财富(stock_board_industry_name_em)",
    "ths": "同花顺(stock_board_industry_name_ths)",
}

BOARD_CONCEPT_LIST_SOURCES = {
    "em": "东方财富(stock_board_concept_name_em)",
    "ths": "同花顺(stock_board_concept_name_ths)",
}

BOARD_INDUSTRY_CONS_SOURCES = {
    "em": "东方财富(stock_board_industry_cons_em)",
    "sina": "新浪财经(stock_sector_detail)",
}

BOARD_CONCEPT_CONS_SOURCES = {
    "em": "东方财富(stock_board_concept_cons_em)",
    "sina": "新浪财经(stock_sector_detail)",
}

BOARD_INDUSTRY_HIST_SOURCES = {
    "em": "东方财富(stock_board_industry_hist_em)",
    "ths": "同花顺(stock_board_industry_index_ths)",
}

BOARD_CONCEPT_HIST_SOURCES = {
    "em": "东方财富(stock_board_concept_hist_em)",
    "ths": "同花顺(stock_board_concept_index_ths)",
}

HSGT_HIST_SOURCES = {
    "em": "东方财富(stock_hsgt_hist_em)",
}

HSGT_HOLD_STOCK_SOURCES = {
    "em": "东方财富(stock_hsgt_hold_stock_em)",
}

LHB_DETAIL_SOURCES = {
    "em": "东方财富(stock_lhb_detail_em)",
}

ZT_POOL_SOURCES = {
    "em": "东方财富(stock_zt_pool_em)",
}

STOCK_NEWS_SOURCES = {
    "em": "东方财富(stock_news_em)",
}

FINANCIAL_INDICATOR_SOURCES = {
    "em": "东方财富(stock_financial_analysis_indicator_em)",
}

BALANCE_SHEET_SOURCES = {
    "em": "东方财富(stock_balance_sheet_by_report_em)",
}

PROFIT_SHEET_SOURCES = {
    "em": "东方财富(stock_profit_sheet_by_report_em)",
}

CASH_FLOW_SHEET_SOURCES = {
    "em": "东方财富(stock_cash_flow_sheet_by_report_em)",
}

DIVIDEND_SOURCES = {
    "em": "东方财富(stock_fhps_detail_em)",
}

RESTRICTED_RELEASE_SOURCES = {
    "em": "东方财富(stock_restricted_release_queue_em)",
}

HOT_RANK_SOURCES = {
    "em": "东方财富(stock_hot_rank_em)",
    "xq": "雪球(stock_hot_follow_xq)",
}


class AkShareSource(DataSource):
    name = "akshare"

    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3):
        self._limiter = RateLimiter(rate_limit)
        self._max_retries = max_retries
        self._patch_akshare()

    @staticmethod
    def _patch_akshare():
        """Patch akshare 的 request_with_retry,解决东财限流断连问题。

        原因: akshare 用 requests.Session + HTTPAdapter(pool_connections=1),
        东财服务器对 keep-alive 连接会断开。改用 requests.get + Connection: close。
        """
        def patched_request_with_retry(url, params=None, timeout=15, max_retries=3, base_delay=1.0, random_delay_range=(0.5, 1.5)):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, params=params, timeout=timeout,
                                            headers={"Connection": "close"})
                    response.raise_for_status()
                    return response
                except (requests.RequestException, ValueError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(*random_delay_range)
                        time.sleep(delay)
            raise last_exception

        try:
            from akshare.utils import request as _req_mod
            _req_mod.request_with_retry = patched_request_with_retry
        except ImportError:
            pass

        try:
            from akshare.stock_feature import stock_hist_em as _hist_mod
            _hist_mod.request_with_retry = patched_request_with_retry
        except ImportError:
            pass

        AkShareSource._fix_stock_news_regex()

    @staticmethod
    def _fix_stock_news_regex():
        """修复 akshare 1.18.x 在 Python 3.12+ 下 stock_news_em 的正则转义 bug。

        原因: akshare 用 raw 字符串 r"\\u3000" 作为正则模式,Python 3.12+ 的 re
        引擎拒绝未知转义序列 \\u,报 "invalid escape sequence"。
        """
        import inspect as _inspect

        try:
            from akshare.news import news_stock as _news_mod
            src = _inspect.getsource(_news_mod.stock_news_em)
            src = src.replace(r"\u3000", "\u3000")
            exec(compile(src, "<patched_stock_news_em>", "exec"), _news_mod.__dict__)
            ak.stock_news_em = _news_mod.stock_news_em
        except Exception:
            pass

    def _call(self, func, *args, **kwargs):
        self._limiter.wait()
        retried = with_retry(max_retries=self._max_retries)(func)
        return retried(*args, **kwargs)

    # --- 行情 ---

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
        if symbol.startswith(("0", "3")):
            return "sz", f"sz{symbol}"
        return "sh", f"sh{symbol}"

    @staticmethod
    def _em_prefix_symbol(symbol: str) -> str:
        """东方财富财务接口需要的前缀格式: 000001 -> 000001.SZ, 600519 -> 600519.SH"""
        if symbol.startswith(("0", "3")):
            return f"{symbol}.SZ"
        return f"{symbol}.SH"

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
        if source == "sina":
            _, prefixed = self._prefix_symbol(symbol)
            return self._call(ak.stock_zh_a_minute, symbol=prefixed, period=period, adjust=adjust)
        return self._call(
            ak.stock_zh_a_hist_min_em,
            symbol=symbol,
            period=period,
            adjust=_ADJUST_MAP[adjust],
        )

    # --- 资金 ---

    def get_fund_flow(self, symbol: str, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            df = self._call(ak.stock_fund_flow_individual, symbol="即时")
            code = symbol.lstrip("shsz.")
            return df[df["股票代码"].astype(str).str.zfill(6).str.contains(code)].reset_index(drop=True)
        market = "sz" if symbol.startswith(("0", "3")) else "sh"
        return self._call(ak.stock_individual_fund_flow, stock=symbol, market=market)

    def get_market_fund_flow(self, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            ind = self._call(ak.stock_fund_flow_industry, symbol="即时")
            con = self._call(ak.stock_fund_flow_concept, symbol="即时")
            ind.insert(0, "类型", "行业")
            con.insert(0, "类型", "概念")
            return pd.concat([ind, con], ignore_index=True)
        return self._call(ak.stock_market_fund_flow)

    def get_sector_fund_flow_rank(self, indicator: str, sector_type: str, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            period = _THS_PERIOD_MAP.get(indicator, "即时")
            if "概念" in sector_type:
                return self._call(ak.stock_fund_flow_concept, symbol=period)
            return self._call(ak.stock_fund_flow_industry, symbol=period)
        return self._call(ak.stock_sector_fund_flow_rank, indicator=indicator, sector_type=sector_type)

    def get_individual_fund_flow_rank(self, indicator: str, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            period = _THS_PERIOD_MAP.get(indicator, "即时")
            return self._call(ak.stock_fund_flow_individual, symbol=period)
        return self._call(ak.stock_individual_fund_flow_rank, indicator=indicator)

    # --- 板块 ---

    def get_board_industry_list(self, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            return self._call(ak.stock_board_industry_name_ths)
        return self._call(ak.stock_board_industry_name_em)

    def get_board_concept_list(self, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            return self._call(ak.stock_board_concept_name_ths)
        return self._call(ak.stock_board_concept_name_em)

    def _ths_board_name(self, symbol: str, board_type: str) -> str:
        clean = symbol.replace("板块", "").replace("行业", "").replace("概念", "").strip()
        if board_type == "concept":
            df = self._call(ak.stock_board_concept_name_ths)
        else:
            df = self._call(ak.stock_board_industry_name_ths)
        names = df["name"].astype(str)
        m = df[names.str.contains(clean)]
        if m.empty:
            raise ValueError(f"同花顺板块中未找到 '{symbol}', 可选板块: {names.tolist()[:15]}")
        return m.iloc[0]["name"]

    def _sina_sector_label(self, symbol: str, indicator: str) -> str:
        df = self._call(ak.stock_sector_spot, indicator=indicator)
        clean = symbol.replace("板块", "").replace("行业", "").replace("概念", "").strip()
        names = df["板块"].astype(str)
        m = df[names.str.contains(clean)]
        if m.empty:
            similar = names[names.str.contains(clean[:2], na=False)].tolist()
            hint = f", 相似板块: {similar[:8]}" if similar else ""
            raise ValueError(f"新浪板块中未找到 '{symbol}', 可选板块: {names.tolist()[:10]}{hint}")
        return m.iloc[0]["label"]

    def get_board_industry_cons(self, symbol: str, source: str = "em") -> pd.DataFrame:
        if source == "sina":
            label = self._sina_sector_label(symbol, "新浪行业")
            return self._call(ak.stock_sector_detail, sector=label)
        return self._call(ak.stock_board_industry_cons_em, symbol=symbol)

    def get_board_concept_cons(self, symbol: str, source: str = "em") -> pd.DataFrame:
        if source == "sina":
            label = self._sina_sector_label(symbol, "概念")
            return self._call(ak.stock_sector_detail, sector=label)
        return self._call(ak.stock_board_concept_cons_em, symbol=symbol)

    def get_board_industry_hist(self, symbol: str, start_date: str, end_date: str, period: str, adjust: str, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            name = self._ths_board_name(symbol, "industry")
            return self._call(
                ak.stock_board_industry_index_ths,
                symbol=name, start_date=start_date, end_date=end_date,
            )
        return self._call(
            ak.stock_board_industry_hist_em,
            symbol=symbol, start_date=start_date, end_date=end_date,
            period=period, adjust=adjust,
        )

    def get_board_concept_hist(self, symbol: str, start_date: str, end_date: str, period: str, adjust: str, source: str = "em") -> pd.DataFrame:
        if source == "ths":
            name = self._ths_board_name(symbol, "concept")
            return self._call(
                ak.stock_board_concept_index_ths,
                symbol=name, start_date=start_date, end_date=end_date,
            )
        return self._call(
            ak.stock_board_concept_hist_em,
            symbol=symbol, start_date=start_date, end_date=end_date,
            period=period, adjust=adjust,
        )

    # --- 沪深港通 ---

    def get_hsgt_hist(self, symbol: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_hsgt_hist_em, symbol=symbol)

    def get_hsgt_hold_stock(self, market: str, indicator: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_hsgt_hold_stock_em, market=market, indicator=indicator)

    # --- 龙虎榜 ---

    def get_lhb_detail(self, start_date: str, end_date: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_lhb_detail_em, start_date=start_date, end_date=end_date)

    # --- 涨停板 ---

    def get_zt_pool(self, date: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_zt_pool_em, date=date)

    # --- 新闻 ---

    def get_stock_news(self, symbol: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_news_em, symbol=symbol)

    # --- 财务 ---

    def get_financial_indicator(self, symbol: str, indicator: str, source: str = "em") -> pd.DataFrame:
        prefixed = self._em_prefix_symbol(symbol)
        return self._call(ak.stock_financial_analysis_indicator_em, symbol=prefixed, indicator=indicator)

    def get_balance_sheet(self, symbol: str, source: str = "em") -> pd.DataFrame:
        prefixed = self._em_prefix_symbol(symbol)
        return self._call(ak.stock_balance_sheet_by_report_em, symbol=prefixed)

    def get_profit_sheet(self, symbol: str, source: str = "em") -> pd.DataFrame:
        prefixed = self._em_prefix_symbol(symbol)
        return self._call(ak.stock_profit_sheet_by_report_em, symbol=prefixed)

    def get_cash_flow_sheet(self, symbol: str, source: str = "em") -> pd.DataFrame:
        prefixed = self._em_prefix_symbol(symbol)
        return self._call(ak.stock_cash_flow_sheet_by_report_em, symbol=prefixed)

    # --- 分红/解禁 ---

    def get_dividend(self, symbol: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_fhps_detail_em, symbol=symbol)

    def get_restricted_release(self, symbol: str, source: str = "em") -> pd.DataFrame:
        return self._call(ak.stock_restricted_release_queue_em, symbol=symbol)

    # --- 人气 ---

    def get_hot_rank(self, source: str = "em") -> pd.DataFrame:
        if source == "xq":
            return self._call(ak.stock_hot_follow_xq, symbol="最热门")
        return self._call(ak.stock_hot_rank_em)

    # --- 个股信息 ---

    def get_stock_info(self, symbol: str, source: str = "em") -> pd.DataFrame:
        if source == "tx":
            df = self._call(ak.stock_zh_a_spot_tx)
            return df[df["code"].astype(str).str.contains(symbol.lstrip("shsz."))].reset_index(drop=True)
        return self._call(ak.stock_individual_info_em, symbol=symbol)
