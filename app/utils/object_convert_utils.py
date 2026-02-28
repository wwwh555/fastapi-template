from typing import TypeVar, Type
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


class ObjectConvertUtils:

    T = TypeVar('T', bound=BaseModel)
    M = TypeVar('M', bound=DeclarativeBase)

    @staticmethod
    def model_to_schema(model_obj: M, schema_cls: Type[T]) -> T:
        """
        将 SQLAlchemy 模型对象转换为 Pydantic schema 对象

        Args:
            model_obj: SQLAlchemy 模型实例
            schema_cls: Pydantic schema 类

        Returns:
            schema_cls 的实例
        """
        # 获取模型对象的所有属性
        model_dict = {}
        for column in model_obj.__table__.columns:
            model_dict[column.name] = getattr(model_obj, column.name)

        # 创建 schema 实例
        return schema_cls(**model_dict)

    @staticmethod
    def schema_to_model(schema_obj: T, model_cls: Type[M]) -> M:
        """
        将 Pydantic schema 对象转换为 SQLAlchemy 模型对象

        Args:
            schema_obj: Pydantic schema 实例
            model_cls: SQLAlchemy 模型类

        Returns:
            model_cls 的实例
        """
        # 获取 schema 对象的所有字段
        schema_dict = schema_obj.model_dump()

        # 过滤出模型类中存在的字段
        model_fields = {column.name for column in model_cls.__table__.columns}
        filtered_dict = {k: v for k, v in schema_dict.items() if k in model_fields}

        # 创建模型实例
        return model_cls(**filtered_dict)

