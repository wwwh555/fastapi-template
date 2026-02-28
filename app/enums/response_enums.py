"""
响应相关枚举
"""
from enum import Enum


class ResponseCode(Enum):
    """响应状态码"""
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500


class ResponseMsg(str, Enum):
    """响应消息"""
    SUCCESS = "操作成功"
    CREATED = "创建成功"
    ACCEPTED = "请求已受理"
    NO_CONTENT = "删除成功"
    BAD_REQUEST = "请求参数错误"
    UNAUTHORIZED = "未授权访问"
    FORBIDDEN = "禁止访问"
    NOT_FOUND = "资源不存在"
    SERVER_ERROR = "服务器内部错误"