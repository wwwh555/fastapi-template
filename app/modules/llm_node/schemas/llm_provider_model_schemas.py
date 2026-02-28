from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LLMProviderModelResponse(BaseModel):
    id: int = Field(..., description="主键ID")
    name: str = Field(..., description='模型名称')
    description: Optional[str] = Field(None, description='模型描述')
    provider_id: int = Field(..., description='模型提供商主键id')
    create_time: datetime = Field(..., description='创建时间')
    update_time: datetime = Field(..., description='更新时间')


