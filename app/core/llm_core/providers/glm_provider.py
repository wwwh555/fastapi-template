from langchain_openai import ChatOpenAI
from zhipuai import ZhipuAI
from .base import ModelProviderBase


class GLMProvider(ModelProviderBase):
    """智谱AI模型提供商

    负责创建和管理智谱AI的模型实例
    """

    def create_model(self,
                    model_name: str,
                    temperature: float,
                    max_tokens: int,
                    top_p: float,
                    api_key: str,
                    api_base: str,
                    streaming: bool,
                    **kwargs) -> ChatOpenAI:
        """创建智谱AI模型实例

        Args:
            model_name: 模型名称，如 "glm-4-flashx"
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: 核采样参数
            api_key: 智谱AI API密钥
            api_base: 智谱AI API基础URL
            streaming: 是否启用流式输出
            **kwargs: 其他参数

        Returns:
            ChatOpenAI: 返回一个封装了智谱AI的LangChain模型实例
        """
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            api_key=api_key,
            base_url=api_base,
            streaming=streaming,
            **kwargs
        )

    def create_native_client(self, api_key: str) -> ZhipuAI:
        """创建智谱AI原生客户端

        Args:
            api_key: 智谱AI API密钥

        Returns:
            ZhipuAI: 返回智谱AI原生客户端实例
        """
        return ZhipuAI(api_key=api_key)
