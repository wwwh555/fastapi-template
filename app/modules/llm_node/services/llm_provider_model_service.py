from sqlalchemy.ext.asyncio import AsyncSession
from app.decorators.transaction import transactional
from app.enums import Propagation
from app.modules.llm_node.daos.llm_provider_model_dao import LLMProviderModelDao
from app.modules.llm_node.schemas.llm_provider_model_schemas import LLMModelResponse
from app.utils.object_convert_utils import ObjectConvertUtils


class LLMProviderModelService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_provider_model_dao = LLMProviderModelDao(db)

    @transactional(propagation=Propagation.REQUIRED)
    async def get_models_by_provider_id(self, provider_id: int):
        # 1.获取所有models
        models = await self.llm_provider_model_dao.get_models_by_provider_id(provider_id=provider_id)
        # 2.models转schemas
        schemas = [ObjectConvertUtils.model_to_schema(model, LLMModelResponse) for model in models]
        return schemas
