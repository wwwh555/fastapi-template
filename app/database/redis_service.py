import json
import redis
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.llm_node.daos.llm_provider_dao import LLMProviderDao
from app.core.config import settings
from app.core.llm_core.factory import ModelFactory
from app.utils.logger import Logger

try:
    # 初始化连接池
    redis_pool = redis.ConnectionPool(max_connections=20).from_url(settings.REDIS_URL)
    # redis连接
    redis_client = redis.Redis(connection_pool=redis_pool)
    Logger.info(f"📦  Redis数据库连接成功: 服务地址:{settings.REDIS_URL}")
except Exception as e:
    Logger.error(f"❌  Redis数据库连接失败: {str(e)}")

class RedisService:

    @staticmethod
    def save_model(node_name: str, model_params: dict):
        """
        存储模型参数(使用Redis Hash 数据结构)
        """
        try:
            # 兼容老版本Redis (3.x)，不使用mapping参数
            # 使用hmset方法或逐个设置字段
            key = f'llm_models:{node_name}'

            # 方法1：使用hmset (Redis 2.0+支持，但在Redis 4.0+被标记为deprecated)
            # 方法2：逐个使用hset (更兼容，Redis 2.0+支持)

            # 检查Redis版本并选择合适的方法
            redis_version = redis_client.info()['redis_version']
            major_version = int(redis_version.split('.')[0])

            if major_version >= 4:
                # Redis 4.0+ 支持mapping参数
                redis_client.hset(key, mapping=model_params)
            else:
                # Redis 3.x 使用hmset或逐个hset
                if hasattr(redis_client, 'hmset'):
                    # 使用hmset方法 (Redis 2.0-6.x支持)
                    redis_client.hmset(key, model_params)
                else:
                    # 逐个设置字段 (最兼容的方法)
                    for field, value in model_params.items():
                        redis_client.hset(key, field, value)
        except redis.ConnectionError as e:
            error_msg = f"Redis连接失败，无法保存模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 错误详情: 检查Redis服务是否正常运行，确认连接配置正确")
            Logger.error(f"Redis连接错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except redis.TimeoutError as e:
            error_msg = f"Redis操作超时，无法保存模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 错误详情: 网络延迟过高或Redis负载过大")
            Logger.error(f"Redis超时错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except redis.ResponseError as e:
            error_msg = f"Redis响应错误，无法保存模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 错误详情: Redis命令执行失败，可能是权限或内存不足")
            Logger.error(f"Redis响应错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"保存模型参数失败 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 参数详情: {model_params}")
            Logger.error(f"保存模型参数错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)

    @staticmethod
    def get_model_params(node_name: str):
        """
        获取node节点对应model信息
        """
        try:
            data = redis_client.hgetall(f"llm_models:{node_name}")
            
            if not data:
                Logger.warning(f"模型参数不存在: node_name={node_name}")
                return None
                
            # 解码数据
            model_params = {k.decode(): v.decode() for k, v in data.items()}
            
            # 验证必要字段
            required_fields = ['model_name', 'parameter', 'provider_tag', 'api_key', 'api_base', 'is_stream']
            missing_fields = [field for field in required_fields if field not in model_params]
            
            if missing_fields:
                error_msg = f"模型参数不完整，缺少字段: {missing_fields}"
                Logger.error(f"{error_msg} | node_name={node_name} | 现有字段: {list(model_params.keys())}")
                raise Exception(error_msg)
            
            # 反序列化parameter字段
            try:
                model_params['parameter'] = json.loads(model_params['parameter'])
            except json.JSONDecodeError as e:
                error_msg = f"模型参数JSON格式错误: {str(e)}"
                Logger.error(f"{error_msg} | node_name={node_name} | 原始parameter: {model_params.get('parameter', 'N/A')}")
                raise Exception(error_msg)
                
            return model_params
            
        except redis.ConnectionError as e:
            error_msg = f"Redis连接失败，无法获取模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 错误详情: 检查Redis服务是否正常运行")
            Logger.error(f"Redis连接错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except redis.TimeoutError as e:
            error_msg = f"Redis操作超时，无法获取模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 错误详情: 网络延迟过高或Redis负载过大")
            Logger.error(f"Redis超时错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except redis.ResponseError as e:
            error_msg = f"Redis响应错误，无法获取模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | 错误详情: Redis命令执行失败")
            Logger.error(f"Redis响应错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except Exception as e:
            # 如果是我们自己抛出的异常，直接传递
            if "模型参数不完整" in str(e) or "模型参数JSON格式错误" in str(e):
                raise
            error_msg = f"获取模型参数失败 {node_name}: {str(e)}"
            Logger.error(f"{error_msg}")
            Logger.error(f"获取模型参数错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)

    @staticmethod
    def load_model(node_name: str):
        """
        读取模型所有参数并创建模型
        """
        try:
            # 1.读取整个 Hash 转为字典
            model_params = RedisService.get_model_params(node_name)
            
            if model_params is None:
                error_msg = f"模型参数不存在，无法加载模型: {node_name}"
                Logger.error(f"{error_msg}")
                raise Exception(error_msg)

            # 2.创建model
            try:
                model = ModelFactory.create_llm_by_params(model_params=model_params)
                return model
            except Exception as e:
                error_msg = f"模型创建失败: {str(e)}"
                Logger.error(f"{error_msg} | node_name={node_name} | model_name={model_params.get('model_name', 'N/A')} | provider={model_params.get('provider_tag', 'N/A')}")
                Logger.error(f"模型创建错误堆栈: {traceback.format_exc()}")
                raise Exception(f"模型创建失败 {node_name}: {str(e)}")
                
        except Exception as e:
            # 如果异常已经包含node_name，直接抛出
            if node_name in str(e):
                raise
            error_msg = f"模型加载失败 {node_name}: {str(e)}"
            Logger.error(f"{error_msg}")
            Logger.error(f"模型加载错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)

    @staticmethod
    async def update_model(node_name: str, update_data: dict, db: AsyncSession):
        """
        更新redis中对应模型参数
            只需更新Redis中存的4个参数：
                - model_name
                - parameter
                - provider配置
                - streaming
            其余node数据表中其他字段并不需要去更新redis中的
        注意这个方法为异步方法
        """
        k = f'llm_models:{node_name}'
        
        try:
            # 获取更新的所有数据键
            keys = update_data.keys()
            
            if 'model_name' in keys:
                try:
                    # 更新model_name
                    redis_client.hset(k, 'model_name', update_data['model_name'])
                except Exception as e:
                    error_msg = f"更新model_name失败: {str(e)}"
                    Logger.error(f"{error_msg} | node_name={node_name} | new_value={update_data['model_name']}")
                    raise Exception(f"更新model_name失败 {node_name}: {str(e)}")
                    
            if 'parameter' in keys:
                try:
                    # 更新参数，需要序列化为JSON字符串
                    parameter_json = json.dumps(update_data['parameter'])
                    redis_client.hset(k, 'parameter', parameter_json)
                except json.JSONEncodeError as e:
                    error_msg = f"参数JSON序列化失败: {str(e)}"
                    Logger.error(f"{error_msg} | node_name={node_name} | parameter={update_data['parameter']}")
                    raise Exception(f"参数JSON序列化失败 {node_name}: {str(e)}")
                except Exception as e:
                    error_msg = f"更新parameter失败: {str(e)}"
                    Logger.error(f"{error_msg} | node_name={node_name}")
                    raise Exception(f"更新parameter失败 {node_name}: {str(e)}")
                    
            if 'provider_id' in keys:
                try:
                    # 更新提供商配置
                    # 1.创建dao层实例
                    llm_provider_dao = LLMProviderDao(db)
                    # 2.查询对应provider
                    provider = await llm_provider_dao.get_llm_provider_by_id(id=update_data['provider_id'])
                    if provider is None:
                        error_msg = f"Provider不存在，无法更新Redis中model provider: provider_id={update_data['provider_id']}"
                        Logger.error(f"{error_msg} | node_name={node_name}")
                        raise ValueError(error_msg)
                    
                    redis_client.hset(k, 'provider_tag', provider.tag)
                    redis_client.hset(k, 'api_key', provider.api_key)
                    redis_client.hset(k, 'api_base', provider.api_base)
                except ValueError as e:
                    # Provider不存在的错误
                    raise
                except Exception as e:
                    error_msg = f"更新provider失败: {str(e)}"
                    Logger.error(f"{error_msg} | node_name={node_name} | provider_id={update_data.get('provider_id', 'N/A')}")
                    Logger.error(f"更新provider错误堆栈: {traceback.format_exc()}")
                    raise Exception(f"更新provider失败 {node_name}: {str(e)}")
                    
            if 'is_stream' in keys:
                try:
                    # 更新stream是否开启配置
                    redis_client.hset(k, 'is_stream', int(update_data['is_stream']))
                except Exception as e:
                    error_msg = f"更新is_stream失败: {str(e)}"
                    Logger.error(f"{error_msg} | node_name={node_name} | new_value={update_data['is_stream']}")
                    raise Exception(f"更新is_stream失败 {node_name}: {str(e)}")
                    
        except redis.ConnectionError as e:
            error_msg = f"Redis连接失败，无法更新模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | update_data={update_data}")
            Logger.error(f"Redis连接错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except redis.TimeoutError as e:
            error_msg = f"Redis操作超时，无法更新模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | update_data={update_data}")
            Logger.error(f"Redis超时错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except redis.ResponseError as e:
            error_msg = f"Redis响应错误，无法更新模型参数 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | update_data={update_data}")
            Logger.error(f"Redis响应错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
        except Exception as e:
            # 如果是我们自己抛出的异常，直接传递
            if any(msg in str(e) for msg in ["更新model_name失败", "参数JSON序列化失败", "更新parameter失败", 
                                           "Provider不存在", "更新provider失败", "更新is_stream失败"]):
                raise
            error_msg = f"更新模型参数失败 {node_name}: {str(e)}"
            Logger.error(f"{error_msg} | update_data={update_data}")
            Logger.error(f"更新模型参数错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
