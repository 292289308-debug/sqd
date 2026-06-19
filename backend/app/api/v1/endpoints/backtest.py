"""
回测任务 - 提交/查询/结果

MVP 阶段: 同步执行 (单次回测),接口会阻塞几秒
V1.0: 改 Celery 异步 + Redis 队列 + 进度推送
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import uuid
import time

router = APIRouter()

# 内存存储 (V1.0 接数据库)
_runs: dict = {}


class BacktestRequest(BaseModel):
    strategy_id: str = Field(..., description="策略模板 ID 或用户策略 ID")
    start_date: date
    end_date: date
    universe: List[str] = Field(default_factory=list, description="股票池 ts_code 列表")
    benchmark: str = "000300.SH"
    initial_cash: float = 1_000_000.0
    commission_rate: float = 0.0003
    slippage: float = 0.001


@router.post("/run")
async def run_backtest(req: BacktestRequest, background_tasks: BackgroundTasks):
    """
    提交回测 (MVP: 同步执行)
    返回: run_id, status
    """
    run_id = f"bt_{uuid.uuid4().hex[:12]}"
    _runs[run_id] = {
        "id": run_id,
        "strategy_id": req.strategy_id,
        "status": "running",
        "request": req.model_dump(),
        "created_at": time.time(),
    }
    # MVP: 同步执行 (实际项目用 Celery 异步)
    result = _do_backtest(req)
    _runs[run_id].update(result)
    _runs[run_id]["status"] = "done"
    _runs[run_id]["finished_at"] = time.time()
    return _runs[run_id]


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in _runs:
        raise HTTPException(404, "回测任务不存在")
    return _runs[run_id]


@router.get("/runs")
async def list_runs(limit: int = 20):
    items = sorted(_runs.values(), key=lambda x: x["created_at"], reverse=True)[:limit]
    return {"count": len(items), "items": items}


def _do_backtest(req: BacktestRequest) -> dict:
    """
    MVP 简化版回测 - 双均线示例
    真实版用 backtrader / 自研事件驱动
    """
    # 延迟导入,避免启动时依赖
    from app.services.backtest_engine import BacktestEngine
    engine = BacktestEngine(
        initial_cash=req.initial_cash,
        commission_rate=req.commission_rate,
        slippage=req.slippage,
    )
    return engine.run_dual_ma(req.start_date, req.end_date, req.universe, req.strategy_id)
