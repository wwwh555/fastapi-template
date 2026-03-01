import json
import os
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.modules.llm_node.models import LLMNodeModel
from app.database.redis_service import RedisService
from app.utils.logger import Logger


def _replace_env_vars(value: str) -> str:
    """
    替换字符串中的环境变量占位符（如 ${MOONSHOT_API_KEY}）
    支持从 os.getenv 和 core.config.settings 读取
    """
    if not isinstance(value, str):
        return value

    # 处理 ${VAR_NAME} 格式的环境变量
    if '${' in value and '}' in value:
        start = value.find('${')
        end = value.find('}', start)
        if start != -1 and end != -1:
            env_var = value[start + 2:end]
            # 首先尝试从 os.getenv 读取
            env_value = os.getenv(env_var)

            # 如果 os.getenv 为空，尝试从 settings 读取
            if env_value is None:
                # 延迟导入避免循环依赖
                from app.core.config import settings
                env_value = getattr(settings, env_var, None)

            # 如果仍然为空，返回空字符串
            if env_value is None:
                env_value = ''

            return value[:start] + env_value + value[end + 1:]

    return value


def _load_config_from_file(config_path: str = None) -> dict:
    """
    从配置文件加载LLM节点配置
    """
    if config_path is None:
        # 默认配置文件路径
        config_path = Path(__file__).parent / 'config' / 'llm_nodes.json'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 替换环境变量
        for provider in config.get('providers', []):
            provider['api_key'] = _replace_env_vars(provider['api_key'])
            provider['api_base'] = _replace_env_vars(provider['api_base'])

        Logger.info(f"从配置文件加载LLM节点配置成功: {config_path}")
        return config
    except FileNotFoundError:
        Logger.error(f"LLM节点配置文件不存在: {config_path}")
        raise
    except json.JSONDecodeError as e:
        Logger.error(f"LLM节点配置文件JSON格式错误: {e}")
        raise


def init_llm_models_from_config(config_path: str = None):
    """
    从配置文件初始化LLM模型（同步版本，用于配置文件模式）
    """
    try:
        config = _load_config_from_file(config_path)

        # 构建provider字典，方便查找
        providers_dict = {p['tag']: p for p in config.get('providers', [])}

        # 遍历所有节点
        for node in config.get('nodes', []):
            provider_tag = node.get('provider_tag')
            provider = providers_dict.get(provider_tag)

            if not provider:
                Logger.error(f"节点 {node['name']} 的provider {provider_tag} 不存在，跳过")
                continue

            # 构造模型参数
            model_params = {
                'model_name': node['model_name'],
                'parameter': json.dumps(node['parameter']),
                'provider_tag': provider_tag,
                'api_key': provider['api_key'],
                'api_base': provider['api_base'],
                'is_stream': int(node.get('is_stream', True)),
            }

            RedisService.save_model(node['name'], model_params)
            Logger.debug(f"成功加载LLM节点: {node['name']} ({node['model_name']})")

        Logger.info(f"从配置文件初始化LLM models实例成功，共加载 {len(config.get('nodes', []))} 个节点")
    except Exception as e:
        Logger.error(f"从配置文件初始化LLM models实例时出错: {e}")
        raise


async def init_llm_node_models():
    """
    初始化加载所有结点node使用的模型model
    """
    from app.database.database import async_session_local
    db = async_session_local()  # 获取会话
    try:
        # 查询数据库所有node和对应provider，然后创建model
        stmt = select(LLMNodeModel).options(selectinload(LLMNodeModel.provider))  # 预加载provider
        result = await db.execute(stmt)
        nodes = result.scalars().all()

        for node in nodes:
            # 将node模型配置存入redis中，与celery共享
            # 构造模型参数
            parameter = node.parameter
            model_params = {
                # 模型名称
                'model_name': node.model_name,
                # 模型参数
                'parameter': json.dumps(parameter),  # 将参数序列化为JSON字符串后存入
                # provider配置
                'provider_tag': node.provider.tag,
                'api_key': node.provider.api_key,
                'api_base': node.provider.api_base,
                'is_stream': int(node.is_stream),  # bool需值转为int值再存到redis中
            }
            RedisService.save_model(node.name, model_params)   # 将模型保存到redis中
        Logger.info("初始化LLM nodes配置到redis中成功")
    except Exception as e:
        Logger.error(f"初始化LLM nodes配置到redis中成功: {e}")
    finally:
        await db.close()  # 确保数据库会话关闭


async def init_llm_models_from_json():
    """
    初始化加载所有结点node使用的模型model（从外部配置的json文件加载）
    仅支持配置文件模式，不使用数据库
    """
    config_path = Path(__file__).parent / 'config' / 'llm_nodes.json'

    if not config_path.exists():
        error_msg = f"LLM节点配置文件不存在: {config_path}。请创建配置文件或从数据库恢复。"
        Logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    Logger.info("使用配置文件模式加载LLM节点配置")
    try:
        init_llm_models_from_config(str(config_path))
    except Exception as e:
        error_msg = f"从配置文件加载LLM节点配置失败: {e}。系统无法启动，请检查配置文件。"
        Logger.error(error_msg)
        raise
