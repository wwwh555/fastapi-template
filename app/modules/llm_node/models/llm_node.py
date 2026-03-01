from sqlalchemy.orm import relationship
from app.database.base_class import Base
from sqlalchemy import Column, String, Integer, DateTime, func, JSON, Boolean, ForeignKey


class LLMNodeModel(Base):
    """LLM调用的节点信息表"""
    __tablename__ = "core_llm_node"
    __table_args__ = {'comment': 'LLM节点表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(50), nullable=False, unique=True, comment='节点名称')
    description = Column(String(255), nullable=True, comment='节点描述')
    service_module = Column(String(255), nullable=False, default='', comment='所属业务模块(resume/job/user)')
    function_name = Column(String(100), nullable=False, comment='所属功能模型名称(resume_import/analyse)')
    model_name = Column(String(255), nullable=False, comment='模型名称')
    parameter = Column(JSON, nullable=True, comment='模型参数配置')
    provider_id = Column(Integer, ForeignKey('core_llm_provider.id'), nullable=False, comment='模型提供商主键id')
    is_stream = Column(Boolean, nullable=False, default=True, comment='是否流式输出：False-否，True-是')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系定义
    provider = relationship("LLMProviderModel", back_populates="nodes")

