from sqlalchemy.orm import relationship
from app.database.base_class import Base
from sqlalchemy import Column, String, Integer, DateTime, func


class LLMProviderModel(Base):
    """LLM提供商信息表"""
    __tablename__ = "core_llm_provider"
    __table_args__ = {'comment': 'LLM提供商信息表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(50), nullable=False, comment='LLM提供商名称')
    tag = Column(String(50), nullable=False, comment='LLM提供商标识(用于使用不同的provider创建LLM)')
    api_key = Column(String(255), nullable=False, comment='提供商对应API密钥')
    api_base = Column(String(255), nullable=False, comment='提供商对应API基础URL')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系定义
    nodes = relationship("LLMNodeModel", back_populates="provider")


