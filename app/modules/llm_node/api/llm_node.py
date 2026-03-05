from typing import List
from fastapi import APIRouter, Depends
from app.modules.llm_node.schemas.llm_provider_model_schemas import LLMProviderModelResponse
from app.modules.llm_node.schemas.llm_provider_schemas import LLMProviderResponse
from app.modules.llm_node.schemas.llm_node_schemas import LLMNodeResponse, LLMNodeUpdateRequest, LLMNodeTestResponse, \
    LLMNodeTestRequest, LLMNodeBatchUpdateRequest, LLMNodeBatchUpdateResponse
from app.modules.llm_node.services.llm_node_service import LLMNodeService
from app.modules.llm_node.services.llm_provider_service import LLMProviderService
from app.database.redis_service import RedisService
from app.utils.auth import Auth, get_auth
from app.utils.logger import Logger
from app.utils.response import ResponseUtils, ResponseCode, ApiResponse

router = APIRouter()


@router.get("/list/{provider_id}", response_model=ApiResponse[List[LLMProviderModelResponse]])
async def get_models_by_provider_id(
    provider_id: int,
    auth: Auth = Depends(get_auth)
):
    """
    查询某provider下的所有models
    """
    try:
        service = LLMProviderService(auth.db)
        result = await service.get_models_by_provider_id(provider_id=provider_id)
        return ResponseUtils.success(data=result, msg=f'获取provider(id={provider_id})所有models成功')
    except ValueError as e:
        msg = f'错误请求 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=msg)
    except Exception as e:
        msg = f'服务端异常 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(msg=msg)


@router.get('/model/{node_name}')
async def get_llm_node_model_by_name(
    node_name: str,
    auth: Auth = Depends(get_auth)
):
    """获取结点对应model(主要用于判断对应内存模型库中模型是否正确更新)"""
    # model = llm_models[node_name]
    # 重构为从redis中直接读取对应配置
    madel_params = RedisService.get_model_params(node_name)
    # 移除敏感配置
    madel_params.pop('api_key')
    madel_params.pop('api_base')
    return ResponseUtils.success(data=madel_params, msg='获取结点模型配置参数成功')


@router.get("/list", response_model=ApiResponse[List[LLMNodeResponse]])
async def get_llm_node_list(
    auth: Auth = Depends(get_auth)
):
    """获取llm所有node list"""

    try:
        service = LLMNodeService(auth.db)
        data = await service.get_llm_node_list()
        return ResponseUtils.success(data=data, msg='获取llm_node list成功')
    except ValueError as e:
        msg = f'错误请求 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST,msg=msg)
    except Exception as e:
        msg = f'服务端异常 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(msg=msg)


@router.put('/update', response_model=ApiResponse[LLMNodeResponse])
async def update_llm_node(
    request: LLMNodeUpdateRequest,
    auth: Auth = Depends(get_auth)
):
    """更新llm node(包括更新数据库node表记录和重新加载全局的llm_models对应node model)"""
    try:
        service = LLMNodeService(auth.db)
        node_schema = await service.update_llm_node(update_data=request.model_dump(exclude_none=True))
        return ResponseUtils.success(data=node_schema, msg=f"更新node(id={str(id)})成功")
    except ValueError as e:
        msg = f'错误请求 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=msg)
    except Exception as e:
        msg = f'服务端异常 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(msg=msg)


@router.put('/batch-update', response_model=ApiResponse[LLMNodeBatchUpdateResponse])
async def batch_update_llm_nodes(
        request: LLMNodeBatchUpdateRequest,
        auth: Auth = Depends(get_auth)
):
    """批量更新llm nodes(包括更新数据库node表记录和重新加载全局的llm_models对应node model)"""
    try:
        service = LLMNodeService(auth.db)

        # 将请求转换为字典列表
        update_data_list = [node.model_dump(exclude_none=True) for node in request.nodes]

        # 调用service层的批量更新方法
        result = await service.batch_update_llm_nodes(update_data=update_data_list)

        # 根据更新结果返回不同的消息
        if result.failed_count == 0:
            msg = f"批量更新成功: 共{result.total}个node全部更新成功"
        elif result.success_count == 0:
            msg = f"批量更新失败: 共{result.total}个node全部更新失败"
        else:
            msg = f"批量更新部分成功: 成功{result.success_count}个, 失败{result.failed_count}个"

        return ResponseUtils.success(data=result, msg=msg)
    except ValueError as e:
        msg = f'错误请求 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=msg)
    except Exception as e:
        msg = f'服务端异常 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(msg=msg)


@router.get("/provider/list", response_model=ApiResponse[List[LLMProviderResponse]])
async def get_llm_provider_list(
    auth: Auth = Depends(get_auth)
):
    """获取所有LLM提供商列表"""
    try:
        service = LLMProviderService(auth.db)
        data = await service.get_llm_provider_list()
        return ResponseUtils.success(data=data, msg='获取llm_provider list成功')
    except ValueError as e:
        msg = f'错误请求 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=msg)
    except Exception as e:
        msg = f'服务端异常 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(msg=msg)


@router.get("/provider/{provider_id}/nodes", response_model=ApiResponse[List[LLMNodeResponse]])
async def get_llm_nodes_by_provider_id(
    provider_id: int,
    auth: Auth = Depends(get_auth)
):
    """
    获取指定provider下的所有llm_node

    Args:
        provider_id: 提供商ID

    Returns:
        该提供商下的所有LLM节点列表
    """
    try:
        service = LLMNodeService(auth.db)
        data = await service.get_llm_nodes_by_provider_id(provider_id=provider_id)
        return ResponseUtils.success(data=data, msg=f'获取provider(id={provider_id})所有nodes成功')
    except ValueError as e:
        msg = f'错误请求 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(code=ResponseCode.BAD_REQUEST, msg=msg)
    except Exception as e:
        msg = f'服务端异常 -- {str(e)}'
        Logger.error(msg)
        return ResponseUtils.error(msg=msg)


@router.post("/test", response_model=ApiResponse[LLMNodeTestResponse])
async def test_llm_node(
    request: LLMNodeTestRequest,
    auth: Auth = Depends(get_auth)
):
    """
    测试LLM节点(node)可用性

    通过传入对应node_name对应LLM调用节点标识，从Redis加载模型配置，直接调用对应LLM进行测试
    """
    try:
        service = LLMNodeService(auth.db)
        result = await service.test_llm_node(request)
        return ResponseUtils.success(data=result)
    except Exception as e:
        return ResponseUtils.error(
            code=ResponseCode.SERVER_ERROR,
            msg=f"测试LLM节点失败: {str(e)}"
        )