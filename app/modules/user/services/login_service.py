"""
用户登录服务模块
支持多种登录方式：密码登录、短信登录、微信登录等
"""
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password
from app.decorators.transaction import transactional
from app.enums.transaction_enums import Propagation
from app.modules.user.schemas.user import LoginForm, LoginResult, UserUpdate
from app.modules.user.daos.user_dao import UserDAO
from app.utils.logger import Logger


class UserLoginService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_dao = UserDAO(db)

    async def password_login(self, form_data: LoginForm) -> LoginResult:
        """
        密码登录
        """
        Logger.info(f"密码登录请求: mobile={form_data.mobile}")

        # 获取用户
        user = await self.user_dao.get_user_by_mobile(form_data.mobile)

        if user is None:
            Logger.warning(f"用户不存在: mobile={form_data.mobile}")
            return LoginResult(status=False, msg="用户不存在或已被禁用")

        Logger.info(f"找到用户: user_id={user.id}, mobile={user.mobile}")

        # 使用security模块的verify_password验证密码
        if not verify_password(form_data.password, user.password):
            Logger.warning(f"密码错误: mobile={form_data.mobile}")
            return LoginResult(status=False, msg="密码错误")

        # 检查用户状态
        if not user.is_active:
            Logger.warning(f"用户已被禁用: mobile={form_data.mobile}")
            return LoginResult(status=False, msg="用户已被禁用")

        Logger.info(f"密码登录成功: user_id={user.id}")
        return LoginResult(status=True, user=user, msg="登录成功")

    async def sms_login(self, form_data: LoginForm) -> LoginResult:
        """
        短信验证码登录（预留）
        """
        # TODO: 实现短信验证码登录逻辑
        user = await self.user_dao.get_user_by_mobile(form_data.mobile)

        if user is None:
            return LoginResult(status=False, msg="用户不存在")

        # TODO: 验证短信验证码
        # 以下是模拟逻辑，实际逻辑应当访问Redis等存储来验证短信验证码
        # if form_data.password != "1234":  # 假设用户输入的验证码是"1234"
        #     return LoginResult(status=False, msg="验证码错误")

        if not user.is_active:
            return LoginResult(status=False, msg="用户已被禁用")

        return LoginResult(status=True, user=user, msg="登录成功")

    async def wechat_login(self, form_data: LoginForm) -> LoginResult:
        """
        微信登录（预留）
        """
        # TODO: 实现微信登录逻辑
        return LoginResult(status=False, msg="微信登录功能暂未开放")


    @transactional(propagation=Propagation.REQUIRED)
    async def update_login_info(self, user_id: int, client_ip: str) -> bool:
        """
        更新用户登录信息（IP和时间）
        """
        current_time = int(time.time())

        update_data = UserUpdate(
            # 这里可以根据需要添加last_login_ip和last_login_time字段到User模型
        )

        try:
            await self.user_dao.update_user(user_id, update_data)
            return True
        except Exception as e:
            Logger.error(f"更新用户登录信息失败: {str(e)}")
            return False
