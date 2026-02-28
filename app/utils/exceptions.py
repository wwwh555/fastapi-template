# utils/exceptions.py
from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    """
    错误码枚举类
    """
    # 通用错误码
    RESOURCE_NOT_FOUND = ("1001", "请求的资源未找到")
    PERMISSION_DENIED = ("1002", "权限不足")
    INVALID_PARAMETER = ("1003", "参数无效")
    INTERNAL_ERROR = ("1004", "服务器内部错误")

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


class BusinessException(Exception):
    """
    业务异常类
    """
    
    def __init__(
        self, 
        error_code: ErrorCode, 
        message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """
        初始化业务异常
        
        Args:
            error_code: 错误码枚举
            message: 自定义错误信息（可选）
            details: 详细错误信息（可选）
        """
        self.error_code = error_code
        self.message = message or error_code.message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code.code}] {self.message}"
    
    def to_dict(self):
        """
        将异常转换为字典格式，便于序列化
        
        Returns:
            dict: 异常信息字典
        """
        return {
            "code": self.error_code.code,
            "message": self.message,
            "details": self.details
        }