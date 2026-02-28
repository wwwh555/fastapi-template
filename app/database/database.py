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

    # 3.初始化数据库表数据(示例数据、配置项数据）
    await init_db_data()


async def get_db():
    """
    获取数据库会话（异步方式）
    """
    async with async_session_local() as session:
        yield session


async def init_db_data():
    """
    初始化数据库表数据
    """
    from pathlib import Path
    from sqlalchemy import text

    try:
        # 获取SQL脚本文件路径
        current_dir = Path(__file__).parent
        sql_files_path = current_dir / "init"

        # 检查路径是否存在
        if not sql_files_path.exists():
            raise FileNotFoundError(f"路径不存在: {sql_files_path}")

        if not sql_files_path.is_dir():
            raise NotADirectoryError(f"不是有效的目录: {sql_files_path}")

        # 递归查找所有.sql文件
        sql_files = list(sql_files_path.rglob("*.sql"))

        if sql_files is None:
            if settings.STARTUP_VERBOSE:
                Logger.debug(f"SQL初始化脚本为空在: {sql_files_path}，跳过示例数据初始化")
            return

        for sql_file_path in sql_files:

            # 1.读取SQL脚本内容
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            if not sql_content.strip():
                Logger.warning("SQL初始化脚本为空")
                return

            # 2.执行SQL脚本
            Logger.info(f"执行数据表初始脚本: {sql_file_path.name}")
            async with async_session_local() as session:
                try:
                    # 将SQL脚本按分号分割成多个语句，过滤空语句和注释
                    sql_statements = []
                    for stmt in sql_content.split(';'):
                        stmt = stmt.strip()
                        # 跳过空语句和纯注释行(注释行可暂时不用跳过）
                        if stmt:
                            # 移除行内注释（简单处理）
                            lines = []
                            for line in stmt.split('\n'):
                                if '--' in line:
                                    # 检查是否是字符串中的--还是注释
                                    comment_pos = line.find('--')
                                    if comment_pos > 0 and line[comment_pos - 1] not in ["'", '"']:
                                        line = line[:comment_pos].rstrip()
                                if line.strip():
                                    lines.append(line)
                            cleaned_stmt = '\n'.join(lines)
                            if cleaned_stmt.strip():
                                sql_statements.append(cleaned_stmt)

                    if not sql_statements:
                        Logger.warning("SQL脚本中没有有效的SQL语句")
                        return

                    # 逐条执行SQL语句
                    success_count = 0
                    skip_count = 0
                    error_count = 0

                    for sql_stmt in sql_statements:
                        try:
                            await session.execute(text(sql_stmt))
                            await session.commit()
                            success_count += 1
                        except Exception as stmt_error:
                            error_msg = str(stmt_error)
                            # INSERT IGNORE 在重复时会返回警告而不是错误，但某些情况下仍可能抛出异常
                            if "Duplicate entry" in error_msg or "already exists" in error_msg.lower():
                                skip_count += 1
                                await session.rollback()
                            else:
                                error_count += 1
                                Logger.warning(f"执行SQL语句失败: {error_msg}")
                                if settings.STARTUP_VERBOSE:
                                    Logger.debug(f"SQL语句: {sql_stmt[:300]}...")
                                await session.rollback()

                    if success_count > 0:
                        Logger.info(f"数据初始化完成: 成功{success_count}条")
                    if skip_count > 0:
                        Logger.debug(f"跳过已存在的数据: {skip_count}条")
                    if error_count > 0:
                        Logger.warning(f"初始化过程中出现错误: {error_count}条")

                except Exception as e:
                    Logger.error(f"执行SQL脚本时出错: {str(e)}")
                    await session.rollback()
                    if settings.STARTUP_VERBOSE:
                        import traceback
                        Logger.error(traceback.format_exc())

    except FileNotFoundError:
        Logger.warning(f"SQL初始化脚本文件目录不存在: {sql_files_path}")
    except Exception as e:
        Logger.error(f"初始化数据库示例数据失败: {str(e)}")
        if settings.STARTUP_VERBOSE:
            import traceback
            Logger.error(traceback.format_exc())