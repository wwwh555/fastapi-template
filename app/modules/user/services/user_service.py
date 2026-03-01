from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from app.decorators.transaction import transactional
from app.enums.transaction_enums import Propagation
from app.modules.user.daos.user_dao import UserDAO
from app.modules.user.models.user import User
from app.modules.user.schemas.user import UserCreate, UserUpdate
from app.utils.logger import Logger


class UserService:
    """用户服务层"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = UserDAO(db)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return await self.dao.get_user_by_id(user_id)

    async def get_user_by_mobile(self, mobile: str) -> Optional[User]:
        """根据手机号获取用户"""
        return await self.dao.get_user_by_mobile(mobile)

    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        """根据UID获取用户"""
        return await self.dao.get_user_by_uid(uid)

    @transactional(propagation=Propagation.REQUIRED)
    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查手机号是否已存在
        existing_user = await self.dao.get_user_by_mobile(user_data.mobile)
        if existing_user:
            raise ValueError(f"手机号 {user_data.mobile} 已被注册")

        user = await self.dao.create_user(user_data)
        Logger.info(f"创建用户成功: user_id={user.id}, mobile={user.mobile}")
        return user

    @transactional(propagation=Propagation.REQUIRED)
    async def update_user(self, user_id: int, update_data: UserUpdate) -> Optional[User]:
        """更新用户"""
        user = await self.dao.update_user(user_id, update_data)
        if user:
            Logger.info(f"更新用户成功: user_id={user_id}")
        return user

    @transactional(propagation=Propagation.REQUIRED)
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        result = await self.dao.delete_user(user_id)
        if result:
            Logger.info(f"删除用户成功: user_id={user_id}")
        return result

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """获取用户列表"""
        return await self.dao.list_users(page, page_size, is_active)

    async def authenticate_user(self, mobile: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = await self.dao.authenticate_user(mobile, password)
        if user:
            if not user.is_active:
                raise ValueError("用户已被禁用")
            Logger.info(f"用户登录成功: mobile={mobile}, user_id={user.id}")
        else:
            Logger.warning(f"用户登录失败: mobile={mobile}")
        return user
