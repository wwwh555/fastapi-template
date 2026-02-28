# FastAPI 企业级模板仓库

基于 **FastAPI + Pydantic + SQLAlchemy + LangChain + LangGraph** 的企业级 AI/LLM/Agent 应用开发模板，提供完整的分层架构、事务管理、依赖注入和最佳实践。

## 特性

### 核心特性
- **分层架构设计**: API → Service → DAO → Model 清晰分离
- **统一的事务管理**: 基于装饰器的事务管理机制
- **完善的依赖注入**: Service 和 DAO 层自动依赖注入
- **LLM/Agent 集成**: 开箱即用的 LangChain 和 LangGraph 支持
- **异步任务处理**: 基于 Celery 的分布式任务队列
- **数据验证**: Pydantic v2 强类型数据验证
- **数据库迁移**: Alembic 自动化数据库版本管理

### 技术栈
- **后端框架**: FastAPI 0.115+
- **Python版本**: 3.9+
- **数据库**: MySQL 5.7+ with SQLAlchemy 2.0+
- **任务队列**: Celery 5.5+ (RabbitMQ + Redis)
- **LLM集成**: LangChain + LangGraph
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

# 开发依赖（可选）
pip install -r requirements.dev.txt
```

### 3. 配置环境变量

```bash
# 运行初始化脚本
python scripts/init_project.py

# 或手动创建
cp .env.template .env
# 编辑 .env 文件，配置数据库和LLM API密钥
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# (可选) 导入初始数据
mysql -u root -p your_database < database/init/init_data.sql
```

### 5. 启动服务

```bash
# 启动 FastAPI 服务
uvicorn main:app --reload

# 启动 Celery Worker（需要先启动 RabbitMQ 和 Redis）
python -m celery -A app.tasks.celery_app worker -l info -P solo
```

访问 API 文档: http://localhost:8000/docs

## 项目结构

```
app/
├── core/                  # 核心配置层
│   ├── config.py         # 配置管理
│   ├── security.py       # 安全工具（JWT、密码哈希）
│   ├── exceptions.py     # 自定义异常
│   └── path_conf.py      # 路径配置
│
├── database/              # 数据库层
│   ├── mysql.py          # MySQL 连接
│   ├── redis.py          # Redis 连接
│   ├── base.py           # SQLAlchemy 基类
│   ├── base_dao.py       # DAO 基类（通用CRUD）
│   ├── base_service.py   # Service 基类
│   └── init/             # 初始化脚本
│
├── llm/                   # LLM层
│   ├── config/           # LLM 配置
│   ├── init_llm.py       # LLM 初始化
│   ├── providers/        # LLM 提供商
│   └── dao_models/       # LLM 配置模型
│
├── decorators/            # 装饰器层
│   ├── transaction.py    # 事务装饰器
│   ├── cache.py          # 缓存装饰器
│   └── ...
│
├── middlewares/           # 中间件层
│   ├── error_handler.py  # 全局异常处理
│   └── ...
│
├── utils/                 # 工具层
│   ├── logger.py         # 日志工具
│   └── response.py       # 响应工具
│
├── schemas/               # 统一数据模型
│   ├── base.py           # 基础模型
│   └── response.py       # 响应模型
│
├── common/                # 通用组件
│   ├── agent/            # Agent 配置
│   ├── prompt_manager/   # 提示词管理
│   └── ...
│
├── modules/               # 业务模块
│   ├── user/             # 用户模块（示例）
│   └── resume/           # 简历模块（示例）
│       └── resume_analysis/  # 简历分析
│
├── tasks/                 # 任务队列层
│   └── celery_app.py     # Celery 配置
│
└── router.py              # 根路由

docs/template/             # 开发文档
scripts/                   # 工具脚本
tests/                     # 测试文件
alembic/                   # 数据库迁移
```

## 开发指南

### 创建新模块

使用提供的脚本快速创建新模块：

```bash
python scripts/create_module.py
```

脚本会交互式地创建标准目录结构和文件模板。

### 模块分层规范

每个模块遵循以下分层结构：

```
modules/[module_name]/
├── api/              # API层 - 处理HTTP请求
├── schemas/          # Schema层 - 数据验证
├── models/           # Model层 - ORM模型
├── daos/             # DAO层 - 数据访问
└── services/         # Service层 - 业务逻辑
```

详细开发指南请参考：[模块开发指南](docs/template/MODULE_DEVELOPMENT_GUIDE.md)

### 使用 BaseDAO 和 BaseService

```python
# DAO层 - 继承BaseDAO获得通用CRUD
class UserDAO(BaseDAO[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

# Service层 - 继承BaseService
class UserService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.dao = UserDAO(db)
```

### 事务管理

```python
from app.decorators.transaction import transactional, Propagation

class OrderService(BaseService):
    @transactional(propagation=Propagation.REQUIRED)
    async def create_order(self, data: dict):
        # 所有操作在一个事务中
        order = await self.order_dao.create(**data)
        await self.inventory_dao.decrease_stock(...)
        return order
```

## 示例模块

### User 模块
基础 CRUD 示例，展示：
- RESTful API 设计
- 数据验证
- 事务管理
- 基类使用

### Resume Analysis 模块
LLM 应用示例，展示：
- LangChain 集成
- Celery 异步任务
- Prompt 版本管理
- Agent 开发

## 测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/user/

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 运行特定测试文件
pytest tests/user/test_user_service.py -v
```

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t fastapi-template .

# 运行容器
docker-compose up -d
```

### 传统部署

```bash
# 生产环境启动
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 配置说明

主要配置项（.env文件）：

- **数据库**: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
- **Redis**: REDIS_URL
- **RabbitMQ**: RABBITMQ_URL
- **LLM**: DEEPSEEK_API_KEY, MOONSHOT_API_KEY, ZHIPUAI_API_KEY
- **安全**: SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

完整配置说明请参考：[.env.template](.env.template)

## 文档

- [模块开发指南](docs/template/MODULE_DEVELOPMENT_GUIDE.md)
- [API设计指南](docs/template/API_DESIGN_GUIDE.md)
- [LLM集成指南](docs/template/LLM_INTEGRATION_GUIDE.md)
- [架构说明](docs/template/ARCHITECTURE.md)

## 常见问题

### 1. Celery Worker 无法启动？
确保 RabbitMQ 和 Redis 已启动：
```bash
# Windows
rabbitmq-server.bat
redis-server.exe

# Linux/Mac
sudo service rabbitmq-server start
redis-server
```

### 2. 数据库连接失败？
检查 .env 文件中的数据库配置是否正确。

### 3. LLM 调用失败？
检查 API Key 是否配置正确，确保网络可以访问 LLM 服务。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
