from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.llm_node.models import LLMProviderModel


class LLMProviderDao:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_llm_provider_by_id(self, id: int):
        """通过id查询对应llm_provider"""
        # 1.构造查询
        stmt = select(LLMProviderModel).where(LLMProviderModel.id == id)
        # 3.执行
        result = await self.db.execute(stmt)
        # 4.响应(一条记录或者None)
        return result.scalar_one_or_none()

    async def get_llm_provider_list(self):
        """获取所有llm_provider列表"""
        # 1.构造查询
        stmt = select(LLMProviderModel)
        # 2.执行
        result = await self.db.execute(stmt)
        # 3.响应
        return result.scalars().all()