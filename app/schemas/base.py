"""
基础模型
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional


class BaseSchema(BaseModel):
    """基础模型"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        extra='ignore'
    )


class TimestampMixin(BaseSchema):
    """时间戳混入"""
    create_time: Optional[datetime] = Field(default_factory=datetime.now)
    update_time: Optional[datetime] = None
    
    @field_validator('update_time', mode='before')
    @classmethod
    def set_update_time(cls, v):
        return v or datetime.now()
