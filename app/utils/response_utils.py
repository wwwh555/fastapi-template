"""
响应工具类
"""
from typing import Any, Type
from pydantic import BaseModel
from app.utils.response import ResponseUtils as BaseResponseUtils, ResponseCode, ResponseMsg, ApiResponse


class ResponseUtils:
    """响应工具类"""

    @staticmethod
    def success(
        code: ResponseCode = ResponseCode.SUCCESS,
        msg: str = ResponseMsg.SUCCESS,
        data: Any = None
    ) -> ApiResponse:
        """通用成功响应方法"""
        return BaseResponseUtils.success(code=code, msg=msg, data=data)

    @staticmethod
    def error(
        code: ResponseCode = ResponseCode.SERVER_ERROR,
        msg: str = ResponseMsg.SERVER_ERROR,
        data: Any = None
    ) -> ApiResponse:
        """通用异常响应方法"""
        return BaseResponseUtils.error(code=code, msg=msg, data=data)

    @staticmethod
    def unauthorized() -> ApiResponse:
        """未授权访问响应"""
        return BaseResponseUtils.unauthorized()

    @staticmethod
    def get_response_type(data_type: Type[BaseModel]) -> Type[ApiResponse]:
        """获取API响应类型"""
        return ApiResponse[data_type]
