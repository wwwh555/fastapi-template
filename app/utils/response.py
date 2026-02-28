from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel
from enum import Enum
from app.enums import ResponseCode, ResponseMsg

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    code: ResponseCode
    msg: str
    data: Optional[T] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            ResponseCode: lambda v: int(v.value)
        }

    def dict(self, *args, **kwargs):
        # 直接构建字典，避免调用super().dict()可能导致的递归问题
        d = {
            'code': self.code,
            'msg': self.msg,
            'data': self.data
        }
        
        # 修复code字段为枚举类型导致的序列化问题
        if isinstance(d.get('code'), Enum):
            d['code'] = int(d['code'].value)
        if d.get('data'):
            if isinstance(d['data'], (list, tuple)) and d['data'] and hasattr(d['data'][0], '__dict__'):
                d['data'] = [
                    {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                    for item in d['data']
                ]
            elif hasattr(d['data'], '__dict__'):
                d['data'] = {
                    k: v for k, v in d['data'].__dict__.items() 
                    if not k.startswith('_')
                }
        return d

    def model_dump(self, *args, **kwargs):
        """Pydantic v2 兼容方法"""
        # 直接返回字典，避免递归调用
        return {
            'code': int(self.code.value) if isinstance(self.code, Enum) else self.code,
            'msg': self.msg,
            'data': self.data
        }
    
    def __json__(self):
        """自定义JSON序列化方法，供FastAPI使用"""
        return self.model_dump()


class ResponseUtils:
    @staticmethod
    def success(
            code: ResponseCode = ResponseCode.SUCCESS,
            msg: str = ResponseMsg.SUCCESS,
            data: Any = None
    ) -> ApiResponse:
        """
        通用成功响应方法：
            code 默认   200
            msg  默认   操作成功
            特定code请根据ResponseCode中包含属性传入
            特定msg可根据ResponseMsg中包含属性传入，或自定义字符串传入
        """
        return ApiResponse(
            code=code,
            msg=msg,
            data=data
        )

    @staticmethod
    def error(
            code: ResponseCode = ResponseCode.SERVER_ERROR,
            msg: str = ResponseMsg.SERVER_ERROR,
            data: Any = None
    ) -> ApiResponse:
        """
        通用异常响应方法：
            code默认：  500
            msg 默认：  服务器内部错误
            特定code请根据ResponseCode中包含属性传入
            特定msg可根据ResponseMsg中包含属性传入，或自定义字符串传入
        """
        return ApiResponse(
            code=code,
            msg=msg,
            data=data
        )

    @staticmethod
    def unauthorized() -> ApiResponse:
        """
        频繁使用的未授权访问特定响应格式，无需外部传参
        """
        return ApiResponse(
            code=ResponseCode.UNAUTHORIZED,
            msg=ResponseMsg.UNAUTHORIZED,
            data=None
        )