from enum import Enum
from typing import Dict, Any
from app.modules.llm_node.models import LLMProviderModel, LLMNodeModel
from .providers import (
    ModelProviderBase,
    GLMProvider,
    DeepSeekProvider,
    ArkProvider,
    MoonshotProvider
)


class ModelProvider(str, Enum):
    GLM = "glm"
    MOONSHOT = "moonshot"
    DEEPSEEK = "deepseek"
    ARK = "volcengine"


class ModelFactory:
    """模型工厂类
    
    负责创建各种类型的模型实例
    """

    _provider_mapping: Dict[str, ModelProviderBase] = {
        ModelProvider.GLM: GLMProvider(),
        ModelProvider.DEEPSEEK: DeepSeekProvider(),
        ModelProvider.ARK: ArkProvider(),
        ModelProvider.MOONSHOT: MoonshotProvider()
    }

    @classmethod
    def get_provider(cls, provider_type: ModelProvider) -> ModelProviderBase:
        """获取指定类型的提供商实例
        
        Args:
            provider_type: 提供商类型
            
        Returns:
            ModelProviderBase: 提供商实例
            
        Raises:
            ValueError: 当提供商类型不存在时
        """
        if provider_type not in cls._provider_mapping:
            raise ValueError(f"不支持的提供商类型: {provider_type}")
        return cls._provider_mapping[provider_type]

    @classmethod
    def create_llm_by_node(cls,
                           node: LLMNodeModel,
                           provider: LLMProviderModel,
                           **kwargs) -> Any:
        """
        通过node节点创建LLM实例

        Args:
            node: 节点node类型(包含模型名称与模型temperature、max_tokens、top_p、stream参数)
            provider: 模型供应商参数(包括模型api_key和api_base参数)
            **kwargs: 其他参数

        Returns:
            Any: 返回创建的模型实例
        """
        # 获取provider实例
        provider_to_create = cls.get_provider(ModelProvider(provider.tag))
        # 获取节点模型参数
        parameter = node.parameter

        return provider_to_create.create_model(
            model_name=node.model_name,
            temperature=parameter.get('temperature'),
            max_tokens=parameter.get("max_tokens"),
            top_p=parameter.get('top_p'),
            api_key=provider.api_key,
            api_base=provider.api_base,
            streaming=node.is_stream,
            **kwargs
        )

    @classmethod
    def create_llm_by_params(cls,
                           model_params: dict,
                           **kwargs) -> Any:
        """
        通过node结点创建LLM实例

        Args:
            model_params: 模型所有参数
            **kwargs: 其他参数

        Returns:
            Any: 返回创建的模型实例
        """
        # 获取provider实例
        provider_to_create = cls.get_provider(ModelProvider(model_params.get('provider_tag')))
        # 获取结点模型参数
        parameter = model_params.get('parameter')

        # 处理api_base为空的情况
        api_base = model_params.get('api_base')
        if api_base in [None, '', 'None', 'null']:
            api_base = None

        return provider_to_create.create_model(
            model_name=model_params.get('model_name'),
            temperature=parameter.get('temperature'),
            max_tokens=parameter.get("max_tokens"),
            top_p=parameter.get('top_p'),
            api_key=model_params.get('api_key'),
            api_base=api_base,
            streaming=bool(model_params.get('is_stream')),  # redis中存的是1或0，无法直接存bool值
            **kwargs
        )

