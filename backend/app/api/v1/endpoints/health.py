"""
健康检查 + 元信息
"""
from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health():
    """基础健康检查"""
    return {
        "status": "ok",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ts": datetime.now().isoformat(),
    }


@router.get("/config")
async def config():
    """暴露前端需要的配置 (脱敏)"""
    return {
        "appName": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "hasTushareToken": bool(settings.TUSHARE_TOKEN),
        "dataDir": settings.DATA_DIR,
    }
