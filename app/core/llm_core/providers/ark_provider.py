from langchain_openai import ChatOpenAI
from .base import ModelProviderBase


class ArkProvider(ModelProviderBase):
    """火山引擎模型提供商
    
    负责创建和管理火山引擎的模型实例
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
        """创建火山引擎模型实例
        
        Args:
            model_name: 模型名称，如 "deepseek-v3"或"doubao"
            temperature: 温度参数
            max_tokens: 最大token数
            api_key: 火山引擎 API密钥
            api_base: 火山引擎 API基础URL
            streaming: 是否启用流式输出
            **kwargs: 其他参数
            
        Returns:
            ChatOpenAI: 返回一个使用火山引擎的LangChain模型实例
        """
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            api_key=api_key,
            api_base=api_base,
            streaming=streaming,
            **kwargs
        ) 