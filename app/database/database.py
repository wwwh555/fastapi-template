# app/database/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database.base_class import Base
from app.utils.logger import Logger

# 使用 Async 引擎和 MySQL 的异步 URL 格式
async_engine = create_async_engine(
    "mysql+aiomysql://" +
    settings.DB_USER + ":" +
    settings.DB_PASSWORD + "@" +
    settings.DB_HOST + ":" +
    str(settings.DB_PORT) + "/" +
    settings.DB_NAME,
    echo=settings.DB_ECHO,
    echo_pool=settings.DB_ECHO_POOL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    isolation_level="READ_COMMITTED"
)

DATABASE_URL_ASYNC = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{str(settings.DB_PORT)}/{settings.DB_NAME}"

# 创建异步的 sessionmaker
async_session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """
    初始化数据库、数据库表
    """
    # 1.首先检查并创建数据库（如果不存在）
    try:
        from app.database.db_init_helper import ensure_database_exists
        await ensure_database_exists()
    except Exception as e:
        Logger.error(f"数据库检查失败，无法继续初始化: {e}")
        raise

    # 2.导入所有模型类
    from app.modules.user.models.user import User
    from sqlalchemy.orm import configure_mappers

    try:
        configure_mappers()
        if settings.STARTUP_VERBOSE:
            Logger.info("SQLAlchemy映射器配置成功")
    except Exception as e:
        Logger.error(f"配置SQLAlchemy映射器时出错: {e}")

    # 3.建表
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if settings.STARTUP_VERBOSE:
            Logger.info("数据库表创建成功")
    except Exception as e:
        Logger.error(f"创建数据库表时出错: {e}")

    # 4.检查并创建默认用户
    try:
        from sqlalchemy import select
        import uuid

        async with async_session_local() as session:
            result = await session.execute(select(User).limit(1))
            user = result.scalars().first()
            if not user:
                Logger.info("No users found. Creating default user...")
                new_user = User(
                    uid=str(uuid.uuid4()).replace('-', ''),
                    mobile="18888888888",
                    nickname="Default User",
                    is_active=True
                )
                new_user.set_password("default_password")
                session.add(new_user)
                await session.commit()
                Logger.info(f"Default user created with ID: {new_user.id}")
            else:
                Logger.info(f"Existing user found with ID: {user.id}. Skipping default user creation.")
    except Exception as e:
        Logger.error(f"Failed to check/create default user: {e}")


async def get_db():
    """
    获取数据库会话（异步方式）
    """
    async with async_session_local() as session:
        yield session
