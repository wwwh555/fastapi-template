"""
用户相关API接口
包括：注册、登录、信息获取、更新、注销等
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token
from app.database.database import get_db
from app.modules.user.schemas.user import (
    LoginForm, LoginResult, RegisterResponse, UserCreate, UserResponse, UserUpdate, UserLoginResponse
)
from app.modules.user.services.login_service import UserLoginService
from app.modules.user.services.user_service import UserService
from app.utils.auth import get_auth, Auth
from app.utils.logger import Logger
from app.utils.response import ResponseUtils, ResponseCode, ApiResponse

router = APIRouter()


# ==================== 无需鉴权的接口 ====================
@router.post("/register", response_model=ApiResponse[RegisterResponse], summary="用户注册")
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口（无需鉴权）

    - **mobile**: 手机号（必填，唯一）
    - **password**: 密码（必填，至少6位）
    - **nickname**: 昵称（可选）
    - **email**: 邮箱（可选）
    - **avatar**: 头像URL（可选）
    """
    try:
        user_service = UserService(db)

        # 获取用户IP地址
        client_host = request.client.host if request.client else "0.0.0.0"
        user_data.join_ip = client_host

        # 注册用户
        new_user = await user_service.create_user(user_data)

        response = RegisterResponse(
            user_id=new_user.id,
            uid=new_user.uid,
            mobile=new_user.mobile
        )
        return ResponseUtils.success(data=response, msg="注册成功")
    except ValueError as e:
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=str(e))
    except Exception as e:
        Logger.error(f"注册失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="注册失败")


@router.post("/login", response_model=ApiResponse[UserLoginResponse], summary="用户登录")
async def login_for_access_token(
    request: Request,
    data: LoginForm,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口（无需鉴权）

    支持多种登录方式：
    - **method=0**: 密码登录
    - **method=1**: 短信验证码登录（预留）
    - **method=2**: 微信小程序登录（预留）
    - **method=3**: 微信公众号登录（预留）
    - **method=4**: 微信开放平台登录（预留）

    返回access_token和refresh_token
    """
    try:
        Logger.info(f"用户登录请求: method={data.method}, mobile={data.mobile}")

        user_login_service = UserLoginService(db)
        # 确定登录方法
        if data.method == "0":
            if not data.mobile:
                return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg="密码登录需要提供手机号")
            result: LoginResult = await user_login_service.password_login(form_data=data)
        elif data.method == "1":
            result: LoginResult = await user_login_service.sms_login(form_data=data)
        elif data.method in ["2", "3", "4"]:
            result: LoginResult = await user_login_service.wechat_login(form_data=data)
        else:
            detail = f"登录方法无效"
            Logger.error(detail)
            return ResponseUtils.error(
                code=ResponseCode.BAD_REQUEST,
                msg=detail
            )

        # 处理登录失败情况
        if not result.status:
            Logger.warning(f"登录失败: {result.msg}")
            return ResponseUtils.error(
                code=ResponseCode.BAD_REQUEST,
                msg=result.msg
            )

        Logger.info(f"登录成功: user_id={result.user.id}")

        # 更新用户最后登录IP和时间
        client_host = request.client.host if request.client else "0.0.0.0"
        await user_login_service.update_login_info(user_id=result.user.id, client_ip=client_host)

        # 生成JWT token
        access_token = create_access_token(
            {"sub": result.user.id, "is_refresh": False}
        )
        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token = create_access_token(
            data={"sub": result.user.id, "is_refresh": True},
            expires_delta=expires
        )

        resp = UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=result.user.id,
            uid=result.user.uid,
            token_type="bearer"
        )

        Logger.info(f"token生成成功: user_id={result.user.id}")
        return ResponseUtils.success(data=resp, msg="登录成功")
    except Exception as e:
        Logger.error(f"登录异常: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="登录失败")


@router.post("/account_cancellation", response_model=ApiResponse, summary="用户账号注销")
async def account_cancellation(auth: Auth = Depends(get_auth)):
    """
    用户账号注销接口（需要鉴权）

    注意：当前接口暂时只返回成功，未实现实际注销逻辑
    """
    # TODO: 实现实际的账号注销逻辑
    return ResponseUtils.success(msg="账号注销成功")


# ==================== 需要鉴权的接口 ====================

@router.get("/info", response_model=ApiResponse[UserResponse], summary="获取用户基本信息")
async def get_user_info(auth: Auth = Depends(get_auth)):
    """
    获取用户基本信息接口（需要鉴权）

    返回当前登录用户的基本信息
    """
    try:
        user_service = UserService(auth.db)
        user_id = auth.user_info['sub']

        if not user_id:
            return ResponseUtils.unauthorized()

        user = await user_service.get_user_by_id(user_id)
        if not user:
            return ResponseUtils.error(
                code=ResponseCode.NOT_FOUND,
                msg=f"用户不存在"
            )

        return ResponseUtils.success(data=user)
    except Exception as e:
        Logger.error(f"获取用户信息失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="获取用户信息失败")


@router.put("/update", response_model=ApiResponse[UserResponse], summary="更新用户基本信息")
async def update_user_properties(
    update_data: UserUpdate,
    auth: Auth = Depends(get_auth)
):
    """
    更新用户基本信息接口（需要鉴权）

    可更新的字段：
    - **nickname**: 昵称
    - **email**: 邮箱
    - **avatar**: 头像URL
    """
    try:
        user_service = UserService(auth.db)
        user_id = auth.user_info['sub']

        if not user_id:
            return ResponseUtils.unauthorized()

        updated_user = await user_service.update_user(user_id, update_data)
        if updated_user:
            return ResponseUtils.success(data=updated_user, msg="更新成功")

        return ResponseUtils.error(
            code=ResponseCode.NOT_FOUND,
            msg="用户不存在"
        )
    except ValueError as e:
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=str(e))
    except Exception as e:
        Logger.error(f"更新用户信息失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="更新用户信息失败")
