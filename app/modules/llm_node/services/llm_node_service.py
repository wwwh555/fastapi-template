import time
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from app.decorators.transaction import transactional
from app.enums import Propagation
from app.modules.llm_node.daos.llm_node_dao import LLMNodeDao
from app.modules.llm_node.schemas.llm_node_schemas import LLMNodeResponse, LLMNodeTestRequest, LLMNodeTestResponse
from app.database.redis_service import RedisService
from app.utils.logger import Logger
from app.utils.object_convert_utils import ObjectConvertUtils


class LLMNodeService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_node_dao = LLMNodeDao(db)

    @transactional(propagation=Propagation.REQUIRED)
    async def get_llm_node_list(self):
        # 1.获取所有models
        models = await self.llm_node_dao.get_llm_node_list()
        # 2.models转schemas
        schemas = [ObjectConvertUtils.model_to_schema(model, LLMNodeResponse) for model in models]
        return schemas

    @transactional(propagation=Propagation.REQUIRED)
    async def get_llm_nodes_by_provider_id(self, provider_id: int):
        """
        通过provider_id获取所有llm_node

        Args:
            provider_id: 提供商ID

        Returns:
            LLMNodeResponse列表
        """
        # 1.获取指定provider的nodes
        models = await self.llm_node_dao.get_llm_nodes_by_provider_id(provider_id=provider_id)
        # 2.models转schemas
        schemas = [ObjectConvertUtils.model_to_schema(model, LLMNodeResponse) for model in models]
        return schemas

    @transactional(propagation=Propagation.REQUIRED)
    async def update_llm_node(self, update_data: dict):
        node_id = update_data.get('id')
        update_data.pop('id')
        # 1.查询node
        node_model = await self.llm_node_dao.get_llm_node_by_id_or_name(id=node_id)
        if node_model is None:
            raise ValueError(f"更新的node不存在(id={id})")

        # 2.更新
        node_update = await self.llm_node_dao.update_llm_node_by_id(id=node_id, update_data=update_data)

        # 3.更新redis中对应model配置（通过工厂类重新创建一个）
        await RedisService.update_model(node_model.name, update_data, self.db)

        Logger.info(f"更新node(id={id})成功,Redis全局models配置已同步更新")
        return ObjectConvertUtils.model_to_schema(node_update, LLMNodeResponse)

    async def test_llm_node(self, request: LLMNodeTestRequest) -> LLMNodeTestResponse:
        """测试LLM节点可用性"""
        try:
            node_name = request.node_name
            test_message = request.test_message or "你好，请回复'测试成功'"
            start_time = time.time()

            Logger.info(f"开始测试LLM节点: node_name={node_name}")

            # 1. 从Redis加载模型
            try:
                model = RedisService.load_model(node_name)
                Logger.info(f"成功加载模型: node_name={node_name}")
            except Exception as e:
                Logger.error(f"加载模型失败: node_name={node_name}, error={str(e)}")
                return LLMNodeTestResponse(
                    node_name=node_name,
                    is_available=False,
                    error_message=f"加载模型失败: {str(e)}",
                    response_time_ms=round((time.time() - start_time) * 1000, 2)
                )

            # 2. 获取模型参数信息
            try:
                model_params = RedisService.get_model_params(node_name)
                model_info = {
                    "model_name": model_params.get("model_name"),
                    "provider_tag": model_params.get("provider_tag"),
                    "temperature": model_params.get("parameter", {}).get("temperature"),
                    "max_tokens": model_params.get("parameter", {}).get("max_tokens"),
                    "is_stream": bool(model_params.get("is_stream", 0))
                }
            except Exception as e:
                model_info = {"error": f"获取模型参数失败: {str(e)}"}

            # 3. 创建简单的测试提示模板
            prompt_template = PromptTemplate(
                template="{test_message}",
                input_variables=["test_message"]
            )

            # 4. 直接调用模型进行测试
            try:
                from core.llm_core.llm_service import llm_service
                response = await llm_service.ainvoke(
                    prompt_template=prompt_template,
                    input_variables={"test_message": test_message},
                    model=model,
                    max_retries=1,
                    enable_detailed_logging=True,
                    output_parser=StrOutputParser()  # new一个langchain中的字符串输出解析器
                )

                response_time = round((time.time() - start_time) * 1000, 2)
                Logger.info(f"LLM节点测试成功: node_name={node_name}, response_time={response_time}ms")

                return LLMNodeTestResponse(
                    node_name=node_name,
                    is_available=True,
                    response_content=str(response) if response else None,
                    response_time_ms=response_time,
                    model_info=model_info
                )
            except Exception as e:
                response_time = round((time.time() - start_time) * 1000, 2)
                Logger.error(f"LLM调用失败: node_name={node_name}, error={str(e)}")
                return LLMNodeTestResponse(
                    node_name=node_name,
                    is_available=False,
                    error_message=f"LLM调用失败: {str(e)}",
                    response_time_ms=response_time,
                    model_info=model_info
                )

        except Exception as e:
            Logger.error(f"测试LLM节点失败: {str(e)}")
            raise