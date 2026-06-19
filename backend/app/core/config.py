"""
配置管理 - 从环境变量加载
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "灵眸量化"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://sqd:sqd_dev_pwd@localhost:5432/sqd"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # 安全
    JWT_SECRET: str = "change_me_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Tushare 数据源
    TUSHARE_TOKEN: Optional[str] = None
    TUSHARE_RATE_LIMIT: int = 200  # 每分钟调用次数

    # 数据存储
    DATA_DIR: str = "./data"

    # 实盘交易 (V1.1)
    PAY_MODE: str = "mock"  # mock / hpayer / jsapi

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
