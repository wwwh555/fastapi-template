from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import text
from app.database.base_class import Base


class User(Base):
    __tablename__ = 'cv_user'
    __table_args__ = {'comment': '用户表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    uid = Column(String(32), nullable=False, unique=True, server_default=text("''"), comment='用户ID')
    nickname = Column(String(50), nullable=False, server_default=text("''"), comment='昵称')
    mobile = Column(String(11), nullable=False, server_default=text("''"), comment='手机')
    email = Column(String(100), nullable=False, server_default=text("''"), comment='邮箱')
    avatar = Column(String(500), nullable=False, server_default=text("''"), comment='头像')
    password = Column(String(255), nullable=False, server_default=text("''"), comment='密码')
    is_active = Column(Boolean, nullable=False, server_default=text("True"), comment='状态:True-活跃；False-注销')

    create_time = Column(DateTime, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    def set_password(self, password: str):
        """设置密码（加密存储）"""
        from app.core.security import hash_password
        self.password = hash_password(password)

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        from app.core.security import verify_password as verify_pwd
        return verify_pwd(password, self.password)
