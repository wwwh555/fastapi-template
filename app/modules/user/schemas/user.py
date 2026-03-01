from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import datetime
import re


class LoginForm(BaseModel):
    """登录请求表单"""
    mobile: Optional[str] = Field(None, description="手机号（密码登录必填）")
    password: str = Field(..., description="密码（8-20位，由字母、数字、下划线组成）")
    code: Optional[str] = Field(None, description="微信登录code")
    method: Optional[str] = Field("0", description="0 for password, 1 for sms, 2 for wechat-mp, 3 for wechat-official, 4 for wechat-open")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码格式：8-20位，由字母、数字、下划线组成"""
        if not (8 <= len(v) <= 20):
            raise ValueError('密码长度必须为8-20位')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('密码只能包含字母、数字和下划线')
        return v


class UserCreate(BaseModel):
    """创建用户请求模型"""
    mobile: str = Field(..., description="手机号", min_length=10, max_length=15)
    password: str = Field(..., description="密码（8-20位，由字母、数字、下划线组成）")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像URL")
    # 注册额外字段
    join_ip: Optional[str] = Field(None, description="加入IP")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码格式：8-20位，由字母、数字、下划线组成"""
        if not (8 <= len(v) <= 20):
            raise ValueError('密码长度必须为8-20位')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('密码只能包含字母、数字和下划线')
        return v


class RegisterResponse(BaseModel):
    """用户注册成功响应"""
    user_id: int
    uid: str
    mobile: str


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


class LoginResult(BaseModel):
    """登录结果模型"""
    status: bool
    user: Optional[UserResponse] = None
    msg: str


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class UserLoginResponse(BaseModel):
    access_token: str = Field(..., description="访问系统的access_token")
    refresh_token: str = Field(..., description="刷新refresh_token")
    user_id: int = Field(..., description="user_id")
    uid: str = Field(..., description="uid")
    token_type: str = Field(..., description="token类型")