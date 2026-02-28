"""
统一封装的响应模型模块
所有后端接口响应模型均为ApiResponse类，具体响应数据的字段与值封装到data字段中
"""
from typing import TypeVar, Generic, Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一API响应模型

    使用方法:
        ApiResponse[UserSchema](code=200, msg="success", data=user_data)
        ApiResponse[str](code=400, msg="error", data="详细错误信息")
    """
    code: int = Field(200, description="业务状态码，200表示成功")
    msg: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }

    def model_dump(self, *args, **kwargs):
        """Pydantic v2 兼容方法"""
        return {
            'code': int(self.code) if isinstance(self.code, Enum) else self.code,
            'msg': self.msg,
            'data': self.data
        }

    def __json__(self):
        """自定义JSON序列化方法，供FastAPI使用"""
        return self.model_dump()


class PageResponse(BaseModel, Generic[T]):
    """
    分页响应模型

    使用方法:
        PageResponse[UserSchema](
            total=100,
            page=1,
            size=10,
            items=[user1, user2, ...]
        )
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页大小")
    items: List[T] = Field(default_factory=list, description="数据列表")

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }


class ErrorDetail(BaseModel):
    """
    错误详情模型

    用于返回详细的错误信息
    """
    field: str = Field(..., description="错误字段")
    message: str = Field(..., description="错误消息")
    type: str = Field(..., description="错误类型")


# 响应码枚举
class ResponseCode(Enum):
    """统一响应码"""
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500


# 快捷创建响应的工厂函数
def success_response(data: Any = None, msg: str = "success") -> dict:
    """
    创建成功响应

    Args:
        data: 响应数据
        msg: 响应消息

    Returns:
        响应字典
    """
    return {
        "code": ResponseCode.SUCCESS.value,
        "msg": msg,
        "data": data
    }


def error_response(code: ResponseCode = ResponseCode.SERVER_ERROR, msg: str = "error", data: Any = None) -> dict:
    """
    创建错误响应

    Args:
        code: 错误码
        msg: 错误消息
        data: 错误详情

    Returns:
        响应字典
    """
    response = {
        "code": code.value if isinstance(code, ResponseCode) else code,
        "msg": msg
    }
    if data is not None:
        response["data"] = data
    return response


def page_response(
    total: int,
    page: int,
    size: int,
    items: List[Any]
) -> dict:
    """
    创建分页响应

    Args:
        total: 总记录数
        page: 当前页码
        size: 每页大小
        items: 数据列表

    Returns:
        响应字典
    """
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }
