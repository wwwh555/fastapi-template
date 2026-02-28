from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union


class ModelProviderBase(ABC):
    """模型提供商基础抽象类
    
    所有具体的模型提供商实现都应该继承此类
    """
    
    @abstractmethod
    def create_model(self, 
                    model_name: str, 
                    temperature: float, 
                    max_tokens: int,
                    top_p: float,
                    api_key: str, 
                    api_base: str, 
                    streaming: bool, 
                    **kwargs) -> Any:
        """创建具体的模型实例  FIXME 未实现（被子类的方法重写）
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: 核采样参数
            api_key: API密钥
            api_base: API基础URL
            streaming: 是否启用流式输出
            **kwargs: 其他参数
            
        Returns:
            Any: 返回具体的模型实例
        """
        pass 