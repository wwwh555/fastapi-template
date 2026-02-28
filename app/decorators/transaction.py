from functools import wraps
from typing import Tuple, Any, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.enums.transaction_enums import Propagation
from app.utils.logger import Logger


def get_db_session(args: Tuple[Any, ...], kwargs: dict) -> Optional[AsyncSession]:
    """获取数据库会话，按优先级：
    1. self.db
    2. args中的AsyncSession实例
    3. auth.db
    4. kwargs中的db参数
    """
    # 检查实例的 db 属性
    if args and hasattr(args[0], 'db'):
        return args[0].db

    # 循环检查args中的AsyncSession实例
    for arg in args:
        if isinstance(arg, AsyncSession):
            return arg

    # 检查 auth 对象的 db
    auth = kwargs.get('auth')
    if auth and hasattr(auth, 'db'):
        return auth.db

    # 检查 kwargs 中的 db
    db = kwargs.get('db')
    if db and isinstance(db, AsyncSession):
        return db

    return None


def transactional(propagation: Propagation = Propagation.REQUIRED):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取数据库会话
            db = get_db_session(args, kwargs)

            Logger.info(f"[Transactional] 开始，事务状态: {db.in_transaction()}")

            if not db:
                raise HTTPException(
                    status_code=500,
                    detail="Database session not found in either service instance or auth object"
                )

            if propagation == Propagation.REQUIRED:
                if db.in_transaction():
                    Logger.info("[Transactional] 使用现有事务")
                    result = await func(*args, **kwargs)
                    Logger.info("[Transactional] 现有事务执行完成")
                    return result
                else:
                    Logger.info("[Transactional] 开启新事务")
                    async with db.begin():
                        Logger.info("[Transactional] 进入事务块")
                        try:
                            result = await func(*args, **kwargs)
                            Logger.info(f"[Transactional] 业务方法执行完成，准备提交")
                            return result
                        except Exception as e:
                            Logger.error(f"[Transactional] 业务方法异常: {e}")
                            raise
                        finally:
                            Logger.info(f"[Transactional] 事务块结束，连接状态: {db.is_active}")

            elif propagation == Propagation.REQUIRES_NEW:
                async with db.begin():
                    return await func(*args, **kwargs)

            elif propagation == Propagation.NESTED:
                if not db.in_transaction():
                    async with db.begin():
                        return await func(*args, **kwargs)
                else:
                    # 在现有事务中创建保存点
                    async with db.begin_nested():
                        return await func(*args, **kwargs)

            raise ValueError(f"Unsupported propagation type: {propagation}")

        return wrapper

    return decorator