# FastAPI 企业级模板仓库

基于 **FastAPI + Pydantic + SQLAlchemy + LangChain + LangGraph** 的企业级 AI/LLM/Agent 应用开发模板，提供完整的分层架构、事务管理、依赖注入和最佳实践。

## 特性

### 核心特性
- **分层架构设计**: API → Service → DAO → Model 清晰分离
- **统一的事务管理**: 基于装饰器的事务管理机制，支持事务传播控制
- **完善的依赖注入**: Service 和 DAO 层自动依赖注入
- **LLM/Agent 集成**: 开箱即用的 LangChain 和 LangGraph 支持
- **数据验证**: Pydantic v2 强类型数据验证
- **异步支持**: 全异步架构，基于 SQLAlchemy 2.0+
- **统一响应格式**: 标准化的 API 响应结构
- **全局异常处理**: 统一的错误处理和异常捕获

### 技术栈
- **后端框架**: FastAPI 0.115+
- **Python版本**: 3.9+
- **数据库**: MySQL 5.7+ with SQLAlchemy 2.0+
- **缓存**: Redis (可选，用于LLM模型参数缓存和业务缓存)
- **LLM集成**: LangChain + LangGraph
- **身份验证**: JWT (Passlib + PyJWT)
- **测试框架**: pytest + pytest-asyncio

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 2. 安装依赖

```bash
# 核心依赖
pip install -r requirements.txt

```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
# 或
cp .env.template .env

# 编辑 .env 文件，配置以下内容：
# - MySQL数据库连接信息（必需）
# - Redis连接信息（可选，但建议配置）
# - LLM API密钥（使用LLM功能时必需）
# - JWT密钥（必需）
```

### 4. 初始化数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 启动应用，会自动创建表结构
uvicorn app.main:app --reload
```

### 5. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload

# 指定端口
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

访问 API 文档: http://localhost:8000/docs

## 项目结构

```
fastapi-template/
├── app/                           # 主应用目录
│   ├── core/                      # 核心配置层
│   │   ├── config.py              # 配置管理（基于pydantic-settings）
│   │   ├── security.py            # 安全工具（JWT、密码哈希）
│   │   ├── exceptions.py          # 自定义异常定义
│   │   └── path_conf.py           # 路径配置
│   │
│   ├── database/                  # 数据库层
│   │   ├── database.py            # 数据库连接和会话管理
│   │   ├── redis_service.py       # Redis服务（连接池、缓存）
│   │   └── db_init_helper.py      # 数据库初始化助手
│   │
│   ├── core/llm_core/             # LLM核心功能
│   │   ├── factory.py             # LLM模型工厂
│   │   ├── init_llm.py            # LLM初始化
│   │   └── llm_service.py         # LLM服务
│   │
│   ├── decorators/                # 装饰器层
│   │   └── transaction.py         # 事务管理装饰器
│   │
│   ├── middlewares/               # 中间件层
│   │   └── error_middleware.py    # 统一错误处理中间件
│   │
│   ├── utils/                     # 工具层
│   │   ├── auth.py                # 认证工具
│   │   ├── logger.py              # 日志工具
│   │   ├── response.py            # 统一响应格式
│   │   ├── response_utils.py      # 响应工具类
│   │   └── object_convert_utils.py # 对象转换工具
│   │
│   ├── schemas/                   # 数据验证层
│   │   └── ...                    # Pydantic模型定义
│   │
│   ├── enums/                     # 枚举定义
│   │
│   ├── modules/                   # 业务模块
│   │   ├── user/                  # 用户模块
│   │   │   ├── api/               # API路由
│   │   │   ├── models/            # ORM模型
│   │   │   ├── schemas/           # 数据验证
│   │   │   ├── daos/              # 数据访问对象
│   │   │   └── services/          # 业务逻辑
│   │   │
│   │   └── llm_node/              # LLM节点管理模块
│   │       ├── api/               # API路由
│   │       ├── models/            # ORM模型
│   │       ├── schemas/           # 数据验证
│   │       ├── daos/              # 数据访问对象
│   │       └── services/          # 业务逻辑
│   │
│   ├── main.py                    # 应用入口
│   └── router.py                  # 路由配置
│
├── docs/                          # 文档目录
│   └── 事务管理规范.md
│
├── static/                        # 静态文件目录
├── tests/                         # 测试目录
├── logs/                          # 日志目录
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量模板
├── .env.template                  # 环境变量模板2
├── requirements.txt               # 核心依赖
├── .gitignore                     # Git忽略配置
└── README.md                      # 项目说明
```

## 架构说明

### 分层架构

项目采用经典的分层架构，每一层都有明确的职责：

```
┌─────────────────────────────────────────────────────────┐
│                        API Layer                        │  ← 处理HTTP请求，参数验证
├─────────────────────────────────────────────────────────┤
│                      Service Layer                      │  ← 业务逻辑，事务管理
├─────────────────────────────────────────────────────────┤
│                       DAO Layer                         │  ← 数据访问，CRUD操作
├─────────────────────────────────────────────────────────┤
│                      Model Layer                        │  ← ORM模型定义
└─────────────────────────────────────────────────────────┘
```

### 核心模块说明

#### 1. 用户模块 (modules/user/)
提供完整的用户管理功能：
- 用户注册
- 用户登录（支持JWT认证）
- 用户注销
- 用户信息更新
- 获取用户信息

#### 2. LLM节点模块 (modules/llm_node/)
LLM模型配置和管理：
- LLM节点配置
- 模型参数管理
- LLM连接测试
- 支持多个LLM提供商（Moonshot、ARK、智谱AI、DeepSeek等）

#### 3. Redis服务
- LLM模型参数缓存
- 业务数据缓存
- **注意**: Redis为可选依赖，即使Redis不可用，项目仍可正常运行

## 开发指南

### 创建新模块

每个模块应遵循以下目录结构：

```
modules/[module_name]/
├── api/              # API层 - 处理HTTP请求，参数验证
├── schemas/          # Schema层 - Pydantic数据验证模型
├── models/           # Model层 - SQLAlchemy ORM模型
├── daos/             # DAO层 - 数据访问对象，CRUD操作
└── services/         # Service层 - 业务逻辑，事务管理
```

### 模块开发示例

#### 1. 定义 Model (models/xxx.py)

```python
from sqlalchemy import Column, Integer, String
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
```

#### 2. 定义 Schema (schemas/xxx.py)

```python
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True
```

#### 3. 定义 DAO (daos/xxx_dao.py)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.user.models.user import User


class UserDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_data: dict) -> User:
        new_user = User(**user_data)
        self.db.add(new_user)
        await self.db.flush()
        return new_user

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()
```

#### 4. 定义 Service (services/xxx_service.py)

```python
from app.decorators.transaction import transactional, Propagation
from app.modules.user.daos.user_dao import UserDAO


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = UserDAO(db)

    @transactional(propagation=Propagation.REQUIRED)
    async def create_user(self, user_data: dict):
        # 业务逻辑处理
        # ...

        # 创建用户
        user = await self.dao.create(user_data)
        return user
```

#### 5. 定义 API (api/xxx.py)

```python
from fastapi import APIRouter, Depends
from app.modules.user.schemas.user import UserCreate, UserResponse
from app.modules.user.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends()
):
    user = await service.create_user(user_data.dict())
    return user
```

#### 6. 注册路由 (router.py)

```python
from app.modules.user.api.user import router as user_router

route.include_router(user_router)
```

### 事务管理

项目提供了基于装饰器的事务管理机制，支持多种事务传播行为：

```python
from app.decorators.transaction import transactional, Propagation


class OrderService:
    @transactional(propagation=Propagation.REQUIRED)
    async def create_order(self, data: dict):
        # 所有数据库操作在一个事务中执行
        order = await self.order_dao.create(data)

        # 如果这里抛出异常，整个事务会回滚
        await self.inventory_dao.decrease_stock(item_id, quantity)

        return order

    @transactional(propagation=Propagation.REQUIRES_NEW)
    async def log_operation(self, log_data: dict):
        # 在新事务中执行，不受外部事务影响
        await self.log_dao.create(log_data)
```

事务传播类型：
- `REQUIRED`: 加入当前事务，如果没有则创建新事务（默认）
- `REQUIRES_NEW`: 总是创建新事务，挂起当前事务
- `SUPPORTS`: 加入当前事务，如果没有则以非事务方式执行
- `NOT_SUPPORTED`: 以非事务方式执行，挂起当前事务
- `NEVER`: 以非事务方式执行，如果有事务则抛出异常
- `MANDATORY`: 加入当前事务，如果没有事务则抛出异常

详细说明请参考：[事务管理规范](docs/事务管理规范.md)

### 配置说明

主要环境变量配置（.env文件）：

```bash
# ========== 数据库配置 ==========
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database

# ========== Redis配置（可选） ==========
REDIS_URL=redis://localhost:6379/0

# ========== JWT配置 ==========
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=43200
REFRESH_TOKEN_EXPIRE_MINUTES=86400

# ========== LLM API密钥（可选） ==========
MOONSHOT_API_KEY=your_moonshot_api_key
ARK_API_KEY=your_ark_api_key
ZHIPUAI_API_KEY=your_zhipuai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# ========== 应用配置 ==========
APP_NAME=FastAPI Template
APP_VERSION=1.0.0
DEBUG=True
```

## API文档

启动服务后，可以通过以下地址访问API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 用户管理
- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `POST /api/v1/users/logout` - 用户注销
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息

#### LLM节点管理
- `POST /api/v1/llm-nodes` - 创建LLM节点
- `GET /api/v1/llm-nodes` - 获取LLM节点列表
- `GET /api/v1/llm-nodes/{node_id}` - 获取LLM节点详情
- `PUT /api/v1/llm-nodes/{node_id}` - 更新LLM节点
- `DELETE /api/v1/llm-nodes/{node_id}` - 删除LLM节点
- `POST /api/v1/llm-nodes/{node_id}/test` - 测试LLM连接

## 测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/modules/user/

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行测试并显示详细输出
pytest -v

# 运行特定测试函数
pytest tests/modules/user/test_user_service.py::test_create_user -v
```

## 依赖说明

### 核心依赖 (requirements.txt)
- FastAPI: Web框架
- SQLAlchemy: ORM
- aiomysql: 异步MySQL驱动
- redis: Redis客户端
- Pydantic: 数据验证
- PyJWT: JWT认证
- passlib: 密码哈希

### LangChain依赖 (requirements_langchain.txt)
- langchain: LangChain核心
- langchain-openai: OpenAI集成
- langchain-community: 社区集成
- langgraph: LangGraph工作流

## 常见问题

### 1. Redis连接失败怎么办？

Redis是可选依赖。如果Redis不可用，项目仍然可以正常运行，只是无法使用缓存功能。如果需要使用缓存：

```bash
# 确保Redis服务已启动
# Windows
redis-server.exe

# Linux/Mac
redis-server
```

### 2. 数据库连接失败？

检查 .env 文件中的数据库配置是否正确，确保MySQL服务已启动。

### 3. LLM调用失败？

- 检查API密钥是否正确配置
- 确保网络可以访问LLM服务
- 部分LLM服务可能需要配置代理

### 4. 如何添加新的LLM提供商？

在 `app/core/llm_core/factory.py` 中添加新的提供商配置，然后在 `.env` 文件中添加对应的API密钥。

## 文档

- [事务管理规范](docs/事务管理规范.md)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
