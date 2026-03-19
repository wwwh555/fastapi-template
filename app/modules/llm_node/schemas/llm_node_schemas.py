from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


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


class LLMNodeCreateRequest(BaseModel):
    """LLM Node创建请求schema"""
    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., description='节点名称', min_length=1, max_length=50)
    description: str = Field(..., description='节点描述', min_length=1, max_length=255)
    service_module: str = Field(..., description='所属业务模块(resume/job/user)', min_length=1, max_length=255)
    function_name: str = Field(..., description='所属功能模型名称(resume_import/analyse)', min_length=1, max_length=100)
    model_name: str = Field(..., description='模型名称', min_length=1, max_length=255)
    parameter: dict = Field(default_factory=dict, description='模型参数配置')
    provider_id: int = Field(..., description='模型提供商主键id')
    is_stream: bool = Field(default=True, description='是否流式输出：False-否，True-是')


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


class LLMNodeBatchUpdateItem(BaseModel):
    """批量更新中单个node的更新请求"""
    id: int = Field(..., description="主键ID")
    description: Optional[str] = Field(None, description='节点描述')
    service_module: Optional[str] = Field(None, description='所属业务模块(resume/job/user)')
    function_name: Optional[str] = Field(None, description='所属功能模型名称(resume_import/analyse)')
    model_name: Optional[str] = Field(None, description='模型名称')
    parameter: Optional[dict] = Field(None, description='模型参数配置')
    provider_id: Optional[int] = Field(None, description='模型提供商主键id')
    is_stream: Optional[bool] = Field(None, description='是否流式输出：False-否，True-是')


class LLMNodeBatchUpdateRequest(BaseModel):
    """LLM Node批量更新请求schema"""
    nodes: List[LLMNodeBatchUpdateItem] = Field(..., description="待更新的node列表")


class LLMNodeBatchUpdateResult(BaseModel):
    """批量更新单个node的结果"""
    id: int = Field(..., description="主键ID")
    success: bool = Field(..., description="是否更新成功")
    message: str = Field(..., description="结果消息")
    data: Optional[LLMNodeResponse] = Field(None, description="更新后的node数据，成功时返回")


class LLMNodeBatchUpdateResponse(BaseModel):
    """批量更新响应"""
    total: int = Field(..., description="总数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[LLMNodeBatchUpdateResult] = Field(..., description="每个node的更新结果")