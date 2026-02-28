from typing import Any, Dict
from fastapi import Depends, HTTPException, Path, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from app.modules.user.models import User
from app.core.config import settings
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db, async_session_local
import jwt
from starlette import status

security = HTTPBearer()

class Auth:
    def __init__(self, db: AsyncSession, user_info: Dict[str, Any]):
        self.db = db
        self.user_info = user_info
        self.user_id = user_info['sub']

    async def validate_resource_owner(
        self,
        resource_id: int,
        model: Any,
        user_field: str = "user_rel"
    ) -> bool:
        """
        通用资源归属校验
        使用独立短生命周期会话，避免占用主会话导致事务已开启从而影响业务事务提交。
        :param resource_id: 资源ID
        :param model: ORM模型类
        :param user_field: 模型里的用户字段名（默认 user_rel）
        """
        user_field_column = getattr(model, user_field)
        # 显式类型标注以配合类型检查器；使用独立 session，避免在主会话上触发 autobegin 导致 in_transaction() 为 True
        session: AsyncSession
        async with async_session_local() as session:
            result = await session.execute(
                select(model).where(
                    model.id == resource_id,
                    user_field_column == self.user_id
                )
            )
            return bool(result.scalar_one_or_none())


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    解析并验证JWT，提取用户信息，返回用户信息字典。
    """
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
        # 查询对应用户是否存在
        async with async_session_local() as session:
            result = await session.execute(select(User).where(User.id == payload['sub']))
            user = result.scalars().first()
            if user is None:
                raise ValueError("认证信息用户不存在，请尝试重新注册后登录")
            if user.is_active == 0:
                raise ValueError("认证信息用户已被禁用，请尝试重新注册后登录或联系后台管理员")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效认证，请您重新登录")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during authentication")

async def get_auth(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security)
) -> Auth:
    """
    解析并验证JWT，提取用户信息，同时提供数据库会话。
    """
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
        # 查询对应用户是否存在(增加容错，避免后续操作可能存在的user不存在情况)
        auth = Auth(db, payload)
        # 使用一个独立的session
        async with async_session_local() as session:
            result = await session.execute(select(User).where(User.id == auth.user_id))
            user = result.scalars().first()
            if user is None:
                raise ValueError("认证信息用户不存在，请尝试重新注册后登录")
            if user.is_active == 0:
                raise ValueError("认证信息用户已被禁用，请尝试重新注册后登录或联系后台管理员")
        return auth
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效认证，请您重新登录")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during authentication")
    
async def websocket_auth(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
) -> Auth:
    """
    在 WebSocket 连接中解析并验证 JWT，提取用户信息，同时提供数据库会话。
    """
    await websocket.accept()  # 先接受连接

    try:
        # 从 WebSocket 连接的查询参数中获取 token
        token = websocket.query_params.get("token")

        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证令牌")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")

        # 构造 Auth 对象
        return Auth(db, payload)

    except jwt.ExpiredSignatureError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效认证，请您重新登录")
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
