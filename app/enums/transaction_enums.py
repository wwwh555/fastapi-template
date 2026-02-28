"""
事务类型枚举
"""
from enum import Enum


class Propagation(Enum):
    """
    事务的传播行为，一共有7种
    REQUIRED、SUPPORTS、MANDATORY、REQUIRES_NEW、NOT_SUPPORTED、NEVER、NESTED。
    REQUIRED传播行为在80%场景下够用
    感觉还是得在具体的业务场景下讨论使用哪种事务传播行为
    """
    REQUIRED = "REQUIRED"  # 默认，使用现有事务
    REQUIRES_NEW = "REQUIRES_NEW"  # 总是创建新事务
    NESTED = 'NESTED'
