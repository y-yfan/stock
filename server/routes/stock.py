from __future__ import annotations

from fastapi import APIRouter, Query

from data import DataAPI
from data.sources.akshare_source import (
    SPOT_SOURCES,
    HISTORY_SOURCES,
    MINUTES_SOURCES,
    FUND_FLOW_SOURCES,
    INFO_SOURCES,
)
from ..schemas import APIResponse

router = APIRouter(prefix="/api/stock", tags=["股票数据"])

api = DataAPI()


def _source_desc(sources: dict[str, str]) -> str:
    opts = ", ".join(f"{k}={v}" for k, v in sources.items())
    return f"数据源: {opts}。不传则自动遍历所有源"


@router.get("/spot", summary="实时行情", description="获取 A 股实时行情,不传 symbol 返回全市场快照")
def get_spot(
    symbol: str | None = Query(None, description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(SPOT_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = api.spot(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/history", summary="历史K线", description="获取股票历史日/周/月K线数据")
def get_history(
    symbol: str = Query(..., description="股票代码,如 000001"),
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    start_date: str | None = Query(None, description="开始日期,如 20250101"),
    end_date: str | None = Query(None, description="结束日期,如 20250801"),
    adjust: str = Query("qfq", description="复权: qfq(前复权)/hfq(后复权)/空字符串(不复权)"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(HISTORY_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = api.history(
            symbol=symbol, period=period, start_date=start_date,
            end_date=end_date, adjust=adjust, force_refresh=force_refresh, source=source,
        )
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/minutes", summary="分钟K线", description="获取股票分钟K线数据")
def get_minutes(
    symbol: str = Query(..., description="股票代码,如 000001"),
    period: str = Query("5", description="分钟周期: 1/5/15/30/60"),
    adjust: str = Query("qfq", description="复权: qfq/hfq/空字符串"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(MINUTES_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = api.minutes(symbol=symbol, period=period, adjust=adjust, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/fund-flow", summary="资金流向", description="获取个股资金流向数据")
def get_fund_flow(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(FUND_FLOW_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = api.fund_flow(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/info", summary="个股信息", description="获取个股基本信息")
def get_stock_info(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(INFO_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = api.stock_info(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))
