"""
安全工具模块

提供JWT令牌编解码、密码哈希、权限验证等安全相关功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from starlette import status
from app.core.config import settings


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码的携带在token中的数据（通常包含 user_id 等信息）
        expires_delta: 过期时间增量--即过期时间

    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # 编码JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的数据，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效认证，请您重新登录")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"身份认证时服务端出现未知异常: {str(e)}")


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT令牌（不验证过期时间）

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的数据，失败返回None
    """
    try:
        # 注意：这里使用了options={"verify_exp": False}来跳过过期时间验证
        # 仅用于调试目的，生产环境应使用 verify_token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效，请您重新登录")
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效认证，请您重新登录")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"身份认证时服务端出现未知异常: {str(e)}")


def get_token_expire_time(minutes: Optional[int] = None) -> datetime:
    """
    获取令牌过期时间

    Args:
        minutes: 过期分钟数，默认使用配置文件中的值

    Returns:
        过期时间对象
    """
    if minutes is None:
        minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    return datetime.utcnow() + timedelta(minutes=minutes)


class TokenPayload(BaseModel):
    """
    JWT令牌载荷模型

    用于验证和解析JWT令牌中的数据
    """
    sub: int = Field(..., description="用户ID")
    exp: int = Field(..., description="过期时间戳")
    iat: int = Field(..., description="签发时间戳")
    extra: Optional[Dict[str, Any]] = Field(None, description="额外数据")


def create_token_payload(user_id: int, extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    创建令牌载荷数据

    Args:
        user_id: 用户ID
        extra_data: 额外的要编码到令牌中的数据

    Returns:
        令牌载荷字典
    """
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow().timestamp()
    }

    if extra_data:
        payload.update(extra_data)

    return payload
