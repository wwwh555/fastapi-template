"""
集中了 FastAPI 应用程序所需的各种设置，从环境变量或".env"文件加载
"""
import os
from pydantic_settings import BaseSettings
from app.core.path_conf import BasePath
from typing import Optional, Dict


class Settings(BaseSettings):
    API_VERSION: str = "1.0.0"
    CONTACT: Dict[str, str] = {
        "name": "FastAPI User Management",
        "url": "https://www.example.com/",
        "email": "admin@example.com",
    }
    ENV: str = "dev"
    if ENV == "dev":
        RELOAD: bool = True
        LOG_LEVEL: str = "debug"
    else:
        RELOAD: bool = False
        LOG_LEVEL: str = "info"

    ALLOWED_HOSTS: list = ["*"]

    # 数据库配置
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DEBUG: bool = True
    FILE_LOG_ENABLED: bool = False

    # redis连接地址
    REDIS_URL: Optional[str] = 'redis://redis:6379/0'

    # 日志配置选项
    DB_ECHO: bool = DEBUG  # 在DEBUG模式下输出SQLAlchemy详细SQL日志
    DB_ECHO_POOL: bool = False  # 是否输出连接池日志

    # 启动时信息输出控制
    STARTUP_VERBOSE: bool = False  # 是否显示详细的启动信息

    # JWT配置
    SECRET_KEY: str = 'your-secret-key-change-in-production'
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 * 30  # 30天

    # 中间件配置
    MIDDLEWARE_CONFIG: Dict[str, bool] = {
        "ERROR_HANDLER": True,
        "CORS": True,
    }

    class Config:
        env_file = f'{BasePath}/.env'
        extra = "ignore"


settings = Settings()
