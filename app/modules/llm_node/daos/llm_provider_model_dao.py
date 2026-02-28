from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.llm_node.models import LLMProviderModelModel


class LLMProviderModelDao:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_models_by_provider_id(self, provider_id: int):
        """通过provider_id查询对应所有models"""
        # 1.构造查询
        stmt = select(LLMProviderModelModel).where(LLMProviderModelModel.provider_id == provider_id)
        # 3.执行
        result = await self.db.execute(stmt)
        # 4.响应
        return result.scalars().all()