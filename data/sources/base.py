from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import pandas as pd

Period = Literal["daily", "weekly", "monthly"]
Adjust = Literal["qfq", "hfq", ""]
MinPeriod = Literal["1", "5", "15", "30", "60"]


class DataSource(ABC):
    name: str = "base"

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

    @abstractmethod
    def get_fund_flow(self, symbol: str) -> pd.DataFrame:
        """资金流向"""

    @abstractmethod
    def get_stock_info(self, symbol: str) -> pd.DataFrame:
        """个股基本信息"""
