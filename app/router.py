from fastapi import APIRouter

# 模板仓库模块路由
from app.modules.user.api.router import user_router
from app.modules.llm_node.api.router import llm_node_router

route = APIRouter(prefix='/api/v1')  # 接口版本v1

# 模板仓库启用模块路由
# user模块路由
route.include_router(user_router)

# llm_node模块路由
route.include_router(llm_node_router)