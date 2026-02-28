"""
数据库初始化辅助模块
用于在项目启动前检查并创建数据库（如果不存在）
"""
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.core.config import settings
from app.utils.logger import Logger


def create_database_if_not_exists():
    """
    检查数据库是否存在，如果不存在则创建

    使用同步引擎执行，因为需要在连接数据库之前操作
    """
    # 构建不指定数据库名的连接URL，连接到MySQL服务器
    server_url = (
        f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{str(settings.DB_PORT)}"
    )

    engine = None
    try:
        # 创建连接到MySQL服务器的引擎（不指定数据库）
        engine = create_engine(
            server_url,
            connect_args={
                "connect_timeout": 10,
                "charset": "utf8mb4"
            }
        )

        # 测试连接
        with engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(
                f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                f"WHERE SCHEMA_NAME = '{settings.DB_NAME}'"
            ))
            db_exists = result.fetchone() is not None

            if db_exists:
                Logger.info(f"数据库 '{settings.DB_NAME}' 已存在")
            else:
                # 创建数据库（如果不存在）
                conn.execute(text(
                    f"CREATE DATABASE `{settings.DB_NAME}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                ))
                conn.commit()
                Logger.info(f"数据库 '{settings.DB_NAME}' 创建成功")

    except OperationalError as e:
        error_code = e.orig.args[0] if e.orig else None
        Logger.error(f"连接MySQL服务器失败 (错误代码: {error_code})")
        Logger.error(f"请检查以下配置是否正确:")
        Logger.error(f"  - DB_HOST: {settings.DB_HOST}")
        Logger.error(f"  - DB_PORT: {settings.DB_PORT}")
        Logger.error(f"  - DB_USER: {settings.DB_USER}")
        Logger.error(f"  - 确保MySQL服务已启动")
        raise

    except ProgrammingError as e:
        Logger.error(f"SQL执行错误: {e}")
        raise

    except Exception as e:
        Logger.error(f"创建数据库时发生未知错误: {e}")
        raise

    finally:
        if engine:
            engine.dispose()


async def ensure_database_exists():
    """
    确保数据库存在的异步包装函数
    可在项目启动事件中调用
    """
    try:
        # 在单独的线程中执行同步操作，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_database_if_not_exists)
    except Exception as e:
        Logger.error("数据库初始化检查失败，无法继续启动服务")
        raise
