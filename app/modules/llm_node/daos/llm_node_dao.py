from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.llm_node.models import LLMNodeModel


class LLMNodeDao:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_llm_node_by_id_or_name(self, id: int=None, name:str=None):
        """通过id或者name两个唯一值查询对应llm_node"""
        # 1.校验
        if id is None and name is None:
            raise ValueError("由id或name查询llm_node时两参数不能同时为空")
        # 2.构造查询
        stmt = select(LLMNodeModel).options(selectinload(LLMNodeModel.provider))  # 预加载provider
        if id:
            stmt = stmt.where(LLMNodeModel.id == id)
        else:
            stmt = stmt.where(LLMNodeModel.name == name)
        # 3.执行
        result = await self.db.execute(stmt)
        # 4.响应(一条记录或者None)
        return result.scalar_one_or_none()

    async def get_llm_node_list(self):
        # 1.构造查询
        stmt = select(LLMNodeModel)
        # 2.执行
        result = await self.db.execute(stmt)
        # 3.响应
        return result.scalars().all()

    async def get_llm_nodes_by_provider_id(self, provider_id: int):
        """
        通过provider_id查询对应的所有llm_node

        Args:
            provider_id: 提供商ID

        Returns:
            LLMNodeModel列表
        """
        # 1.构造查询
        stmt = select(LLMNodeModel).where(LLMNodeModel.provider_id == provider_id)
        # 2.执行
        result = await self.db.execute(stmt)
        # 3.响应
        return result.scalars().all()

    async def update_llm_node_by_id(self, id: int, update_data: dict) -> LLMNodeModel:
        # 1.查询
        node = await self.get_llm_node_by_id_or_name(id=id)
        if node is None:
            raise ValueError(f'更新的llm_node不存在(id={id})')
        # 2.遍历update_data更新
        for key,value in update_data.items():
            setattr(node, key, value)  # 设置值
        # 3.刷新
        await self.db.flush()
        await self.db.refresh(node)

        return node