from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMNodeResponse(BaseModel):
    id: int = Field(..., description="主键ID")
    name: str = Field(..., description='节点名称')
    description: str = Field(..., description='节点描述')
    service_module: str = Field(..., description='所属业务模块(resume/job/user)')
    function_name: str = Field(..., description='所属功能模型名称(resume_import/analyse)')
    model_name: str = Field(..., description='模型名称')
    parameter: dict = Field(..., description='模型参数配置')
    provider_id: int = Field(..., description='模型提供商主键id')
    is_stream: bool = Field(..., description='是否流式输出：False-否，True-是')
    create_time: Optional[datetime] = Field(None, description='创建时间')
    update_time: Optional[datetime] = Field(None, description='更新时间')


class LLMNodeUpdateRequest(BaseModel):
    """LLM Node更新请求schema"""
    id: int = Field(..., description="主键ID")
    description: Optional[str] = Field(None, description='节点描述')
    service_module: Optional[str] = Field(None, description='所属业务模块(resume/job/user)')
    function_name: Optional[str] = Field(None, description='所属功能模型名称(resume_import/analyse)')
    model_name: Optional[str] = Field(None, description='模型名称')
    parameter: Optional[dict] = Field(None, description='模型参数配置')
    provider_id: Optional[int] = Field(None, description='模型提供商主键id')
    is_stream: Optional[bool] = Field(None, description='是否流式输出：False-否，True-是')


# LLM节点测试相关模型
class LLMNodeTestRequest(BaseModel):
    """LLM节点测试请求"""
    node_name: str = Field(..., min_length=1, max_length=100, description="LLM节点名称")
    test_message: Optional[str] = Field("你好，请回复'测试成功'", max_length=500, description="测试消息")


class LLMNodeTestResponse(BaseModel):
    """LLM节点测试响应"""
    node_name: str
    is_available: bool = Field(..., description="节点是否可用")
    response_content: Optional[str] = Field(None, description="LLM响应内容")
    error_message: Optional[str] = Field('无', description="错误信息")
    response_time_ms: Optional[float] = Field(None, description="响应时间（毫秒）")
    model_info: Optional[Dict[str, Any]] = Field(None, description="模型配置信息")