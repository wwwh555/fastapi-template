# app/database/base_class.py
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeMeta
class CustomBase:
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()  # __tablename__ 属性将设置为模型类名的小写版本。

Base = declarative_base(cls=CustomBase)  # 确保所有模型共享相同的数据库会话和元数据

# 之前注解 DeclarativeMeta 导致了一些问题