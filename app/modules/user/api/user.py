from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.modules.user.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.modules.user.services.user_service import UserService
from app.utils.response import ResponseUtils, ResponseCode, ApiResponse
from app.utils.logger import Logger

router = APIRouter()


@router.post("/", response_model=ApiResponse[UserResponse], summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户

    - **mobile**: 手机号（必填，唯一）
    - **password**: 密码（必填，至少6位）
    - **nickname**: 昵称（可选）
    - **email**: 邮箱（可选）
    - **avatar**: 头像URL（可选）
    """
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        return ResponseUtils.success(data=user, msg="创建用户成功")
    except ValueError as e:
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=str(e))
    except Exception as e:
        Logger.error(f"创建用户失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="创建用户失败")


@router.get("/{user_id}", response_model=ApiResponse[UserResponse], summary="获取用户详情")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    根据用户ID获取用户详情
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        return ResponseUtils.error(code=ResponseCode.NOT_FOUND, msg=f"用户 {user_id} 不存在")
    return ResponseUtils.success(data=user)


@router.put("/{user_id}", response_model=ApiResponse[UserResponse], summary="更新用户")
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息

    - **nickname**: 昵称（可选）
    - **email**: 邮箱（可选）
    - **avatar**: 头像URL（可选）
    - **mobile**: 手机号（可选）
    - **is_active**: 是否活跃（可选）
    """
    try:
        user_service = UserService(db)
        user = await user_service.update_user(user_id, update_data)
        if not user:
            return ResponseUtils.error(code=ResponseCode.NOT_FOUND, msg=f"用户 {user_id} 不存在")
        return ResponseUtils.success(data=user, msg="更新用户成功")
    except Exception as e:
        Logger.error(f"更新用户失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="更新用户失败")


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（物理删除）
    """
    try:
        user_service = UserService(db)
        result = await user_service.delete_user(user_id)
        if not result:
            return ResponseUtils.error(code=ResponseCode.NOT_FOUND, msg=f"用户 {user_id} 不存在")
        return ResponseUtils.success(msg="删除用户成功")
    except Exception as e:
        Logger.error(f"删除用户失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="删除用户失败")


@router.get("/", response_model=ApiResponse[UserListResponse], summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: bool = Query(None, description="是否活跃"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（支持分页）

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    - **is_active**: 是否活跃（可选过滤条件）
    """
    try:
        user_service = UserService(db)
        users, total = await user_service.list_users(page, page_size, is_active)

        return ResponseUtils.success(data={
            "items": users,
            "total": total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        Logger.error(f"获取用户列表失败: {str(e)}")
        return ResponseUtils.error(code=ResponseCode.SERVER_ERROR, msg="获取用户列表失败")
