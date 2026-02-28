from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import datetime


class UserCreate(BaseModel):
    """创建用户请求模型"""
    mobile: str = Field(..., description="手机号")
    password: str = Field(..., description="密码", min_length=6)
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像URL")


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    mobile: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    uid: str
    nickname: str
    mobile: str
    email: Optional[str] = None
    avatar: str
    is_active: bool
    create_time: datetime.datetime
    update_time: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
