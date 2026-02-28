from langchain_deepseek import ChatDeepSeek
from .base import ModelProviderBase


class DeepSeekProvider(ModelProviderBase):
    """DeepSeek模型提供商
    
    负责创建和管理DeepSeek的模型实例
    """
    
    def create_model(self, 
                    model_name: str, 
                    temperature: float, 
                    max_tokens: int,
                    top_p: float,
                    api_key: str, 
                    api_base: str, 
                    streaming: bool, 
                    **kwargs) -> ChatDeepSeek:
        """创建DeepSeek模型实例
        
        Args:
            model_name: 模型名称，如 "deepseek-chat"
            temperature: 温度参数
            max_tokens: 最大token数
            api_key: DeepSeek API密钥
            api_base: DeepSeek API基础URL
            streaming: 是否启用流式输出
            **kwargs: 其他参数
            
        Returns:
            ChatDeepSeek: 返回一个DeepSeek模型实例
        """
        return ChatDeepSeek(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            api_key=api_key,
            api_base=api_base,
            streaming=streaming,
            timeout=kwargs.get('timeout', 1800),  # 默认30分钟超时
            max_retries=kwargs.get('max_retries', 2)
        ) 