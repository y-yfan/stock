"""
AkShare 数据层使用示例

注意: AkShare 底层是爬虫,频繁请求会被限流/封 IP。
建议: 接口间加 time.sleep(3),优先使用缓存,避免 force_refresh。
"""

import time
from services import StockService

service = StockService()

# 1. 历史日 K 线(前复权) — 最常用,单次请求,稳定
df = service.history(symbol="000001", start_date="20250101", end_date="20250801")
print("=== 平安银行日 K ===")
print(df.head())
print(f"共 {len(df)} 条\n")

time.sleep(3)

# 2. 分钟 K 线
df = service.minutes(symbol="000001", period="5")
print("=== 平安银行 5 分钟 K ===")
print(df.head())
print(f"共 {len(df)} 条\n")

time.sleep(3)

# 3. 资金流向
df = service.fund_flow(symbol="000001")
print("=== 平安银行资金流向 ===")
print(df.head())

time.sleep(3)

# 4. 个股信息
df = service.stock_info(symbol="000001")
print("=== 平安银行基本信息 ===")
print(df)

time.sleep(5)

# 5. 实时行情(腾讯源,全市场约 16 秒,自动缓存)
# 首次拉取全市场,后续从缓存过滤
df = service.spot(symbol="000001")
print("=== 平安银行实时 ===")
print(df.to_string())

# 缓存命中测试(毫秒级)
t0 = time.time()
df2 = service.spot(symbol="000001")
print(f"\n缓存命中: {time.time()-t0:.4f}s")

# 全市场快照(从缓存读取)
df_all = service.spot()
print(f"全市场股票数: {len(df_all)}")
