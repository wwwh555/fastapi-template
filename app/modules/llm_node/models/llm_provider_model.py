from app.database.base_class import Base
from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey


class LLMProviderModelModel(Base):
    """LLM提供商信息表"""
    __tablename__ = "core_llm_provider_model"
    __table_args__ = {'comment': 'LLM提供商拥有的模型表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(50), nullable=False, comment='模型名称')
    description = Column(String(255), nullable=True, comment='模型描述')
    provider_id = Column(Integer, ForeignKey('core_llm_provider.id'), nullable=False, comment='模型提供商主键id')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')



