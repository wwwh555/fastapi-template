from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from typing import Optional, List
import uuid
import time

from app.modules.user.models.user import User
from app.modules.user.schemas.user import UserCreate, UserUpdate
from app.utils.logger import Logger


class UserDAO:
    """用户数据访问层"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_mobile(self, mobile: str) -> Optional[User]:
        """根据手机号获取用户"""
        stmt = select(User).where(User.mobile == mobile)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        """根据UID获取用户"""
        stmt = select(User).where(User.uid == uid)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 生成唯一uid
        uid = str(uuid.uuid4()).replace('-', '')

        # 检查uid是否已存在
        while await self.get_user_by_uid(uid):
            uid = str(uuid.uuid4()).replace('-', '')

        # 创建用户对象
        user = User(
            uid=uid,
            mobile=user_data.mobile,
            nickname=user_data.nickname or f"用户{user_data.mobile[-4:]}",
            email=user_data.email or '',
            avatar=user_data.avatar or '',
            is_active=True
        )
        # 设置密码
        user.set_password(user_data.password)

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, update_data: UserUpdate) -> Optional[User]:
        """更新用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_data_dict.items():
            if value is not None:
                setattr(user, key, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.flush()
        return True

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """
        获取用户列表

        Args:
            page: 页码
            page_size: 每页数量
            is_active: 是否活跃（可选）

        Returns:
            (用户列表, 总数)
        """
        # 构建查询条件
        conditions = []
        if is_active is not None:
            conditions.append(User.is_active == is_active)

        # 查询总数
        count_stmt = select(func.count(User.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # 查询分页数据
        stmt = select(User)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return list(users), total

    async def authenticate_user(self, mobile: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = await self.get_user_by_mobile(mobile)
        if not user:
            return None
        if user.verify_password(password):
            return user
        return None
