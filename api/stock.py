from __future__ import annotations

from fastapi import APIRouter, Query

from services import StockService
from services.sources.akshare_source import (
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
from schemas import APIResponse

router = APIRouter(prefix="/api/stock", tags=["股票数据"])

service = StockService()


def _source_desc(sources: dict[str, str]) -> str:
    opts = ", ".join(f"{k}={v}" for k, v in sources.items())
    return f"数据源: {opts}。不传则自动遍历所有源"


# ===================== 行情 =====================


@router.get("/spot", summary="实时行情", description="获取 A 股实时行情,不传 symbol 返回全市场快照")
def get_spot(
    symbol: str | None = Query(None, description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(SPOT_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.spot(symbol=symbol, force_refresh=force_refresh, source=source)
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
        df, used_source = service.history(
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
        df, used_source = service.minutes(symbol=symbol, period=period, adjust=adjust, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 资金 =====================


@router.get("/fund-flow", summary="个股资金流向", description="获取个股资金流向数据")
def get_fund_flow(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(FUND_FLOW_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.fund_flow(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/market-fund-flow", summary="大盘资金流", description="获取大盘整体资金流向数据")
def get_market_fund_flow(
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(MARKET_FUND_FLOW_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.market_fund_flow(force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/sector-fund-flow-rank", summary="板块资金流排名", description="获取行业/概念板块资金流排名")
def get_sector_fund_flow_rank(
    indicator: str = Query("今日", description="时间指标: 今日/3日/5日/10日"),
    sector_type: str = Query("行业资金流", description="板块类型: 行业资金流/概念资金流"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(SECTOR_FUND_FLOW_RANK_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.sector_fund_flow_rank(indicator=indicator, sector_type=sector_type, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/individual-fund-flow-rank", summary="个股资金流排名", description="获取个股资金流排名")
def get_individual_fund_flow_rank(
    indicator: str = Query("5日", description="时间指标: 今日/3日/5日/10日"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(INDIVIDUAL_FUND_FLOW_RANK_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.individual_fund_flow_rank(indicator=indicator, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 板块 =====================


@router.get("/board/industry-list", summary="行业板块列表", description="获取所有行业板块名称")
def get_board_industry_list(
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BOARD_INDUSTRY_LIST_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.board_industry_list(force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/board/concept-list", summary="概念板块列表", description="获取所有概念板块名称")
def get_board_concept_list(
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BOARD_CONCEPT_LIST_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.board_concept_list(force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/board/industry-cons", summary="行业板块成分股", description="获取指定行业板块的成分股列表")
def get_board_industry_cons(
    symbol: str = Query(..., description="行业板块名称,如 小金属"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BOARD_INDUSTRY_CONS_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.board_industry_cons(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/board/concept-cons", summary="概念板块成分股", description="获取指定概念板块的成分股列表")
def get_board_concept_cons(
    symbol: str = Query(..., description="概念板块名称,如 宁德时代概念"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BOARD_CONCEPT_CONS_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.board_concept_cons(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/board/industry-hist", summary="行业板块历史K线", description="获取行业板块历史K线数据")
def get_board_industry_hist(
    symbol: str = Query(..., description="行业板块名称,如 小金属"),
    start_date: str = Query(..., description="开始日期,如 20250101"),
    end_date: str = Query(..., description="结束日期,如 20250801"),
    period: str = Query("日k", description="周期: 日k/周k/月k"),
    adjust: str = Query("", description="复权: qfq/hfq/空字符串"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BOARD_INDUSTRY_HIST_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.board_industry_hist(symbol=symbol, start_date=start_date, end_date=end_date, period=period, adjust=adjust, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/board/concept-hist", summary="概念板块历史K线", description="获取概念板块历史K线数据")
def get_board_concept_hist(
    symbol: str = Query(..., description="概念板块名称,如 宁德时代概念"),
    start_date: str = Query(..., description="开始日期,如 20250101"),
    end_date: str = Query(..., description="结束日期,如 20250801"),
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    adjust: str = Query("", description="复权: qfq/hfq/空字符串"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BOARD_CONCEPT_HIST_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.board_concept_hist(symbol=symbol, start_date=start_date, end_date=end_date, period=period, adjust=adjust, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 沪深港通 =====================


@router.get("/hsgt/hist", summary="沪深港通资金历史", description="获取沪深港通资金流向历史数据")
def get_hsgt_hist(
    symbol: str = Query("沪股通", description="通道: 沪股通/深股通/北向资金"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(HSGT_HIST_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.hsgt_hist(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/hsgt/hold-stock", summary="沪深港通持股", description="获取沪深港通持股明细")
def get_hsgt_hold_stock(
    market: str = Query("北向", description="市场: 北向/沪股通/深股通"),
    indicator: str = Query("5日排行", description="指标: 今日排行/5日排行/10日排行/1月排行/1季排行/1年排行"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(HSGT_HOLD_STOCK_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.hsgt_hold_stock(market=market, indicator=indicator, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 龙虎榜 =====================


@router.get("/lhb/detail", summary="龙虎榜详情", description="获取龙虎榜交易详情")
def get_lhb_detail(
    start_date: str = Query(..., description="开始日期,如 20250101"),
    end_date: str = Query(..., description="结束日期,如 20250110"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(LHB_DETAIL_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.lhb_detail(start_date=start_date, end_date=end_date, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 涨停板 =====================


@router.get("/zt-pool", summary="涨停池", description="获取指定日期的涨停股票池")
def get_zt_pool(
    date: str = Query(..., description="日期,如 20250101"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(ZT_POOL_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.zt_pool(date=date, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 新闻 =====================


@router.get("/news", summary="个股新闻", description="获取个股相关新闻")
def get_stock_news(
    symbol: str = Query(..., description="股票代码,如 603777"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(STOCK_NEWS_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.stock_news(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 财务 =====================


@router.get("/financial/indicator", summary="财务分析指标", description="获取个股财务分析指标")
def get_financial_indicator(
    symbol: str = Query(..., description="股票代码,如 000001"),
    indicator: str = Query("按报告期", description="指标类型: 按报告期/按年度/按单季度"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(FINANCIAL_INDICATOR_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.financial_indicator(symbol=symbol, indicator=indicator, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/financial/balance-sheet", summary="资产负债表", description="获取个股资产负债表")
def get_balance_sheet(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(BALANCE_SHEET_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.balance_sheet(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/financial/profit-sheet", summary="利润表", description="获取个股利润表")
def get_profit_sheet(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(PROFIT_SHEET_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.profit_sheet(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/financial/cash-flow-sheet", summary="现金流量表", description="获取个股现金流量表")
def get_cash_flow_sheet(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(CASH_FLOW_SHEET_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.cash_flow_sheet(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 分红/解禁 =====================


@router.get("/dividend", summary="分红配送", description="获取个股分红配送明细")
def get_dividend(
    symbol: str = Query(..., description="股票代码,如 300073"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(DIVIDEND_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.dividend(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/restricted-release", summary="解禁队列", description="获取个股限售解禁队列")
def get_restricted_release(
    symbol: str = Query(..., description="股票代码,如 600000"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(RESTRICTED_RELEASE_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.restricted_release(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 人气 =====================


@router.get("/hot-rank", summary="人气排名", description="获取个股人气排名")
def get_hot_rank(
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(HOT_RANK_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.hot_rank(force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


# ===================== 个股信息 =====================


@router.get("/info", summary="个股信息", description="获取个股基本信息")
def get_stock_info(
    symbol: str = Query(..., description="股票代码,如 000001"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    source: str | None = Query(None, description=_source_desc(INFO_SOURCES)),
) -> APIResponse:
    try:
        df, used_source = service.stock_info(symbol=symbol, force_refresh=force_refresh, source=source)
        return APIResponse(count=len(df), data=df.to_dict(orient="records"), source=used_source)
    except Exception as e:
        return APIResponse(success=False, message=str(e))
