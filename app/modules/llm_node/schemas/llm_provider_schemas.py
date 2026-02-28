from datetime import datetime
from pydantic import BaseModel, Field


class LLMProviderResponse(BaseModel):
    """LLM提供商响应Schema"""
    id: int = Field(..., description="主键ID")
    name: str = Field(..., description='LLM提供商名称')
    tag: str = Field(..., description='LLM提供商标识(用于使用不同的provider创建LLM)')
    create_time: datetime = Field(..., description='创建时间')
    update_time: datetime = Field(..., description='更新时间')