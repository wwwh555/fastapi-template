from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.llm_node.daos.llm_provider_dao import LLMProviderDao
from app.modules.llm_node.schemas.llm_provider_schemas import LLMProviderResponse
from app.utils.object_convert_utils import ObjectConvertUtils
from app.decorators.transaction import transactional
from app.enums import Propagation


class LLMProviderService:
    """LLM提供商服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_provider_dao = LLMProviderDao(db)

    @transactional(propagation=Propagation.REQUIRED)
    async def get_llm_provider_list(self):
        """
        获取所有LLM提供商列表

        Returns:
            LLMProviderResponse列表
        """
        providers = await self.llm_provider_dao.get_llm_provider_list()
        schemas = [ObjectConvertUtils.model_to_schema(provider, LLMProviderResponse) for provider in providers]
        return schemas
