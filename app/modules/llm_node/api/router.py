from fastapi import APIRouter
from .llm_node import router as router

llm_node_router = APIRouter(prefix='/llm/node', tags=['后台-LLM结点管理'])

llm_node_router.include_router(router)