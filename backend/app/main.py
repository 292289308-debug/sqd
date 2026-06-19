"""
灵眸量化 (SmartQuant Dashboard) - FastAPI 主入口
版本: v0.1  2026-06-19
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from app.core.config import settings
from app.api.v1 import api_router

# ---------- 日志 ----------
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------- 生命周期 ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子"""
    logger.info("🚀 灵眸量化启动 mode=%s", settings.PAY_MODE)
    # 启动时: 初始化数据库连接池 / 加载缓存 / 启动定时任务
    yield
    # 关闭时: 关闭连接 / 刷新缓存 / 停止任务
    logger.info("👋 灵眸量化关闭")


# ---------- App ----------
app = FastAPI(
    title="灵眸量化 API",
    description="SmartQuant Dashboard - 个人投资者与量化研究员的本地化行情+策略+实盘看板",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS (开发期放行所有,生产期收紧)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 健康检查 ----------
@app.get("/api", tags=["meta"])
async def root():
    return {
        "name": "灵眸量化 (SmartQuant Dashboard)",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "frontend": "/",
    }


# ---------- 路由聚合 ----------
app.include_router(api_router, prefix="/api/v1")

# ---------- 静态前端 (SPA) ----------
# 优先级最低: API 路径都匹配完才到这里
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    logger.info("[OK] 静态前端已挂载: %s", STATIC_DIR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
