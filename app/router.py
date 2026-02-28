from fastapi import APIRouter

# 模板仓库模块路由
from app.modules.user.api.router import v1 as user_router

route = APIRouter(prefix='/api/v1')  # 接口版本v1

# 模板仓库启用模块路由
route.include_router(user_router)
