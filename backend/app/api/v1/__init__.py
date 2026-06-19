"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, stocks, kline, watchlist, strategy, backtest

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["meta"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(kline.router, prefix="/kline", tags=["kline"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
