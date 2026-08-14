from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.stock import router as stock_router

app = FastAPI(
    title="金融数据 API",
    description="基于 AkShare 的金融数据查询服务,支持 A 股实时行情、历史K线、分钟数据、资金流向、个股信息等",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock_router)


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok"}
