from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import pandas as pd

Period = Literal["daily", "weekly", "monthly"]
Adjust = Literal["qfq", "hfq", ""]
MinPeriod = Literal["1", "5", "15", "30", "60"]


class DataSource(ABC):
    name: str = "base"

    # --- 行情 ---

    @abstractmethod
    def get_spot(self, symbol: str | None = None) -> pd.DataFrame:
        """实时行情。symbol 为 None 时返回全市场快照。"""

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        period: Period = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: Adjust = "qfq",
    ) -> pd.DataFrame:
        """历史 K 线"""

    @abstractmethod
    def get_minutes(
        self,
        symbol: str,
        period: MinPeriod = "1",
        adjust: Adjust = "qfq",
    ) -> pd.DataFrame:
        """分钟 K 线"""

    # --- 资金 ---

    @abstractmethod
    def get_fund_flow(self, symbol: str) -> pd.DataFrame:
        """个股资金流向"""

    @abstractmethod
    def get_market_fund_flow(self) -> pd.DataFrame:
        """大盘资金流"""

    @abstractmethod
    def get_sector_fund_flow_rank(self, indicator: str, sector_type: str) -> pd.DataFrame:
        """板块资金流排名"""

    @abstractmethod
    def get_individual_fund_flow_rank(self, indicator: str) -> pd.DataFrame:
        """个股资金流排名"""

    # --- 板块 ---

    @abstractmethod
    def get_board_industry_list(self) -> pd.DataFrame:
        """行业板块列表"""

    @abstractmethod
    def get_board_concept_list(self) -> pd.DataFrame:
        """概念板块列表"""

    @abstractmethod
    def get_board_industry_cons(self, symbol: str) -> pd.DataFrame:
        """行业板块成分股"""

    @abstractmethod
    def get_board_concept_cons(self, symbol: str) -> pd.DataFrame:
        """概念板块成分股"""

    @abstractmethod
    def get_board_industry_hist(self, symbol: str, start_date: str, end_date: str, period: str, adjust: str) -> pd.DataFrame:
        """行业板块历史K线"""

    @abstractmethod
    def get_board_concept_hist(self, symbol: str, start_date: str, end_date: str, period: str, adjust: str) -> pd.DataFrame:
        """概念板块历史K线"""

    # --- 沪深港通 ---

    @abstractmethod
    def get_hsgt_hist(self, symbol: str) -> pd.DataFrame:
        """沪深港通资金历史"""

    @abstractmethod
    def get_hsgt_hold_stock(self, market: str, indicator: str) -> pd.DataFrame:
        """沪深港通持股"""

    # --- 龙虎榜 ---

    @abstractmethod
    def get_lhb_detail(self, start_date: str, end_date: str) -> pd.DataFrame:
        """龙虎榜详情"""

    # --- 涨停板 ---

    @abstractmethod
    def get_zt_pool(self, date: str) -> pd.DataFrame:
        """涨停池"""

    # --- 新闻 ---

    @abstractmethod
    def get_stock_news(self, symbol: str) -> pd.DataFrame:
        """个股新闻"""

    # --- 财务 ---

    @abstractmethod
    def get_financial_indicator(self, symbol: str, indicator: str) -> pd.DataFrame:
        """财务分析指标"""

    @abstractmethod
    def get_balance_sheet(self, symbol: str) -> pd.DataFrame:
        """资产负债表"""

    @abstractmethod
    def get_profit_sheet(self, symbol: str) -> pd.DataFrame:
        """利润表"""

    @abstractmethod
    def get_cash_flow_sheet(self, symbol: str) -> pd.DataFrame:
        """现金流量表"""

    # --- 分红/解禁 ---

    @abstractmethod
    def get_dividend(self, symbol: str) -> pd.DataFrame:
        """分红配送"""

    @abstractmethod
    def get_restricted_release(self, symbol: str) -> pd.DataFrame:
        """解禁队列"""

    # --- 人气 ---

    @abstractmethod
    def get_hot_rank(self) -> pd.DataFrame:
        """人气排名"""

    # --- 个股信息 ---

    @abstractmethod
    def get_stock_info(self, symbol: str) -> pd.DataFrame:
        """个股基本信息"""
