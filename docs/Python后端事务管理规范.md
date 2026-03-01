# Python 后端开发事务管理规范

## 1. 概述

本文档定义了 AiCV 项目中 Python 后端开发的数据库事务管理规范。事务管理的正确性直接影响数据一致性和系统的可靠性，所有开发人员必须严格遵守本规范。

### 1.1 核心原则

1. **事务管理统一在 Service 服务层进行**
2. **使用显式事务管理，禁止隐式事务**
3. **DAO** **层专注于数据库操作，不处理事务边界**
4. **API** **层不处理事务，仅负责请求响应**

### 1.2 分层架构与事务边界

```Plaintext
┌─────────────────────────────────────────────────────────────┐
│ API Layer (api/)                                             │
│ - 职责：参数验证、响应格式化、异常处理                        │
│ - 禁止：直接操作事务                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Service Layer (services/)                                   │
│ - 职责：业务逻辑、事务管理、调用 DAO                          │
│ - 事务边界：以 Service 方法为单位                             │
│ - 支持：@transactional 装饰器 或 手动事务管理                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DAO Layer (daos/)                                            │
│ - 职责：数据库 CRUD 操作、flush/refresh                      │
│ - 禁止：处理事务边界（commit/rollback）                       │
│ - 职责：执行增删改后立即 flush/refresh 回显数据               │
└─────────────────────────────────────────────────────────────┘
```

## 2. 事务管理方式

### 2.1 @transactional 装饰器（推荐简单场景）

`@transactional` 装饰器提供了声明式的事务管理，适合大多数简单业务场景。

#### 2.1.1 基本使用

```Python
from utils.transaction import transactional, Propagation

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_dao = UserDAO(db)

    @transactional(propagation=Propagation.REQUIRED)
    async def update_user_profile(self, user_id: int, update_data: dict):
        """更新用户资料 - 单表操作"""
        user = await self.user_dao.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # DAO 层已处理 flush/refresh，此处无需额外操作
        updated_user = await self.user_dao.update_user(user_id, update_data)
        return updated_user
```

#### 2.1.2 事务传播行为

| 传播行为       | 说明                                         | 使用场景                           |
| -------------- | -------------------------------------------- | ---------------------------------- |
| `REQUIRED`     | 默认。如果当前存在事务则加入，否则创建新事务 | **80% 的场景**，简单单表或多表操作 |
| `REQUIRES_NEW` | 总是创建新事务，挂起当前事务（如果有）       | 需要独立提交的场景，如操作日志记录 |
| `NESTED`       | 嵌套事务，使用保存点（Savepoint）            | 复杂业务流程中的部分回滚           |

**示例：REQUIRES_NEW 使用场景**

```Python
@transactional(propagation=Propagation.REQUIRED)
async def process_payment(self, order_id: int):
    """处理支付 - 主事务"""
    # 1. 更新订单状态
    await self.order_dao.update_status(order_id, "PAID")

    # 2. 记录操作日志（使用独立事务，即使主事务回滚也不影响日志）
    await self.log_service.record_operation_log(
        operation="payment",
        order_id=order_id
    )  # log_service 内部使用 REQUIRES_NEW

    # 3. 发送通知
    await self.notification_service.send_payment_success(order_id)
```

#### 2.1.3 装饰器工作原理

```Python
# 伪代码说明装饰器执行流程
@transactional(propagation=Propagation.REQUIRED)
async def business_method(self, ...):
    # 1. 进入方法前检查：db.in_transaction()
    #    - 如果 False：自动执行 async with db.begin()
    #    - 如果 True：使用现有事务
    # 2. 执行业务逻辑
    # 3. 正常退出：自动 commit（由 context manager 处理）
    # 4. 异常退出：自动 rollback（由 context manager 处理）
```

### 2.2 手动事务管理（推荐复杂场景）

对于涉及多表、复杂业务逻辑、需要精细控制事务边界的场景，使用手动事务管理。

#### 2.2.1 基本模式

```Python
class MembershipService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.membership_dao = MembershipDAO(db)
        self.user_balance_log_service = UserBalanceLogService(db)

    async def membership_buy(self, user_id: int, membership_id: int):
        """会员购买 - 多表操作，手动事务管理"""
        # 开启事务
        async with self.db.begin():
            # 1. 查询会员商品（读取操作，不产生写事务）
            membership_model = await self.membership_dao.get_by_id(id=membership_id)
            if membership_model is None:
                raise ValueError("该会员商品不存在")

            # 2. 检查并扣除用户余额（写入操作）
            success = await self.user_balance_log_service.change_balance(
                user_id=user_id,
                type='money',
                amount=membership_model.rmb_price,
                operation='deduct',
                memo=f'购买会员{membership_model.name}'
            )
            if not success:
                raise ValueError("扣除用户余额失败")

            # 3. 开通会员（写入操作）
            await self.open_membership(
                user_id=user_id,
                type=membership_model.type,
                duration=membership_model.duration
            )

            # 事务块退出时自动 commit
            # 如果期间抛出异常，自动 rollback
```

#### 2.2.2 多事务场景

**场景：需要在同一方法中控制多个独立事务**

```Python
async def complex_business_process(self, order_id: int):
    """复杂业务流程 - 多个独立事务"""

    # 事务 1：更新订单状态
    async with self.db.begin():
        await self.order_dao.update_status(order_id, "PROCESSING")
        # 事务 1 自动提交

    # 执行一些不依赖数据库的业务逻辑
    result = await self.calculate_something()

    # 事务 2：写入结果
    async with self.db.begin():
        await self.order_dao.update_result(order_id, result)
        # 事务 2 自动提交

    # 事务 3：记录日志（独立事务）
    async with self.db.begin():
        await self.log_dao.create_log(order_id, "completed")
        # 事务 3 自动提交
```

#### 2.2.3 带异常处理的手动事务

```Python
async def process_with_error_handling(self, user_id: int):
    """带完整异常处理的手动事务"""
    async with self.db.begin():
        try:
            # 业务逻辑
            await self._step1(user_id)
            await self._step2(user_id)
            await self._step3(user_id)

        except ValueError as e:
            # 业务异常，记录并回滚
            Logger.error(f"业务异常: {e}")
            raise  # async with 块会自动 rollback

        except Exception as e:
            # 系统异常，记录并回滚
            Logger.error(f"系统异常: {e}")
            raise  # async with 块会自动 rollback
```

### 2.3 两种方式的选择指南

| 场景特征                     | 推荐方式         | 原因                   |
| ---------------------------- | ---------------- | ---------------------- |
| 单表增删改查                 | `@transactional` | 简洁清晰，事务边界明确 |
| 简单多表操作（串行）         | `@transactional` | 一个事务即可完成       |
| 需要条件判断后开启不同事务   | 手动管理         | 需要精细控制事务边界   |
| 涉及多个独立事务             | 手动管理         | 需要明确每个事务的起止 |
| 复杂业务流程，中间有外部调用 | 手动管理         | 避免长事务占用连接     |
| 需要在事务中调用外部服务     | 手动管理         | 可在事务外处理异常     |

## 3. DAO 层规范

### 3.1 DAO 层职责

1. **执行数据库 CRUD 操作**
2. **负责 flush/refresh 操作**（回显数据）
3. **不处理事务边界**（不调用 commit/rollback）

### 3.2 DAO 层 flush/refresh 规范

**必须在 DAO 层的增、删、改操作后执行 flush 和 refresh：**

```Python
class PaymentOrderDAO:
    async def create(self, payment_order: PaymentOrder) -> PaymentOrder:
        """创建支付订单"""
        self.db.add(payment_order)
        await self.db.flush()      # 回显主键 id
        await self.db.refresh(payment_order)  # 回显其他更新字段
        return payment_order

    async def update_payment_order(self, out_trade_no: str, data: dict):
        """更新支付订单"""
        # 1. 查询订单
        payment_order = await self.get_by_trade_no(out_trade_no)

        # 2. 更新字段
        for key, value in data.items():
            setattr(payment_order, key, value)

        await self.db.flush()      # flush 回显主键 id
        await self.db.refresh(payment_order)  # refresh 回显其他属性
        return payment_order
```

**flush 和 refresh 的区别：**

| 操作        | 作用                                      | 何时使用                              |
| ----------- | ----------------------------------------- | ------------------------------------- |
| `flush()`   | 将 session 中的变更发送到数据库，但不提交 | 需要获取数据库生成的值（如自增 ID）时 |
| `refresh()` | 从数据库重新加载对象实例                  | 需要获取数据库计算/触发器更新的字段时 |

### 3.3 DAO 层禁止操作

```Python
# ❌ 错误示例：DAO 层不应处理事务
class BadExampleDAO:
    async def create_bad(self, obj):
        self.db.add(obj)
        await self.db.commit()  # ❌ 禁止：DAO 层不应 commit
        return obj

# ✅ 正确示例
class GoodExampleDAO:
    async def create_good(self, obj):
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj  # 事务由 Service 层管理
```

## 4. API 层规范

### 4.1 API 层职责

1. **接收请求、参数验证**
2. **调用 Service 层处理业务**
3. **格式化响应、处理 HTTP 异常**

### 4.2 API 层禁止操作

```Python
# ❌ 错误示例：API 层不应处理事务
@router.post("/payment")
async def create_payment(request: PaymentCreateRequest, auth: AuthDependency):
    async with auth.db.begin():  # ❌ 禁止：API 层不应管理事务
        # 业务逻辑...
        pass

# ✅ 正确示例：API 层只调用 Service
@router.post("/payment")
async def create_payment(
    request: PaymentCreateRequest,
    auth: AuthDependency,
    payment_service: PaymentService = Depends(get_payment_service)
):
    # Service 层内部处理事务
    result = await payment_service.create_payment_order(request, auth.user_id)
    return ApiResponse.success(data=result)
```

## 5. 禁止隐式事务管理

### 5.1 什么是隐式事务

隐式事务是指：没有显式开启事务（`begin()` 或 `@transactional`），但通过 select 查询后使 session 进入事务状态，后续进行写操作却没有显式 commit。

### 5.2 隐式事务的问题

```Python
# ❌ 危险的隐式事务
async def dangerous_method(self, user_id: int):
    # 1. select 查询隐式开启事务
    user = await self.user_dao.get_user_by_id(user_id)

    # 2. 执行写操作
    user.balance += 100
    await self.db.flush()  # flush 执行了，但事务未 commit

    # 3. 方法结束，框架自动 rollback！
    # 数据丢失，且没有报错
```

### 5.3 REQUIRED 传播行为与隐式事务

```Python
# ❌ 错误示例：隐式事务 + @transactional(REQUIRED)
async def implicit_transaction_wrong(self, user_id: int):
    # 隐式开启事务
    user = await self.user_dao.get_user_by_id(user_id)
    # session.in_transaction() == True

    # 即使加了装饰器，也不会自动 commit
    # 因为 REQUIRED 会使用现有事务
    @transactional(propagation=Propagation.REQUIRED)
    async def inner_method():
        user.balance += 100
        # 不会自动 commit，因为已经在外层事务中

    await inner_method()
    # 方法结束，事务 rollback，数据丢失
```

### 5.4 正确做法

**所有写操作必须在显式事务中进行：**

```Python
# ✅ 正确：使用 @transactional
@transactional(propagation=Propagation.REQUIRED)
async def correct_method_v1(self, user_id: int):
    user = await self.user_dao.get_user_by_id(user_id)
    user.balance += 100
    # 方法结束自动 commit

# ✅ 正确：使用手动事务
async def correct_method_v2(self, user_id: int):
    async with self.db.begin():
        user = await self.user_dao.get_user_by_id(user_id)
        user.balance += 100
        # 块结束自动 commit
```

## 6. 特殊场景处理

### 6.1 Celery 异步任务

Celery 任务中需要特别注意事务管理，因为每个任务有独立的执行上下文。

```Python
# ✅ 推荐：为每个操作创建独立会话
@celery_app.task
def process_career_plan_report_task(task_id: int, user_id: int, ...):
    async def run_async():
        from database.database import async_session_local

        # 使用独立会话，避免与主线程会话冲突
        async with async_session_local() as db:
            service = CareerPlanService(db)
            return await service._run_career_plan_task(...)

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_async())
```

### 6.2 长事务处理

**避免长事务占用数据库连接：**

```Python
async def long_transaction_handling(self, user_id: int):
    """长事务拆分示例"""

    # 事务 1：更新状态
    async with self.db.begin():
        await self.task_dao.update_status(task_id, "PROCESSING")

    # 执行耗时操作（不在事务中）
    result = await self.expensive_llm_generation()

    # 事务 2：写入结果
    async with self.db.begin():
        await self.task_dao.update_result(task_id, result)
        await self.task_dao.update_status(task_id, "COMPLETED")
```

### 6.3 异常处理与事务回滚

```Python
@transactional(propagation=Propagation.REQUIRED)
async def with_exception_handling(self, user_id: int):
    try:
        # 业务逻辑
        await self._step1(user_id)
        await self._step2(user_id)
    except ValueError as e:
        # 业务异常：记录日志后抛出，事务自动回滚
        Logger.error(f"业务异常: {e}")
        raise  # 抛出异常，触发 rollback
    except Exception as e:
        # 系统异常：记录日志后抛出，事务自动回滚
        Logger.error(f"系统异常: {e}")
        raise  # 抛出异常，触发 rollback
    # 正常执行：自动 commit
```

## 7. 常见错误与最佳实践

### 7.1 常见错误

| 错误类型           | 问题表现                     | 解决方案                                |
| ------------------ | ---------------------------- | --------------------------------------- |
| 隐式事务           | 数据未提交，无报错           | 使用 `@transactional` 或手动 `begin()`  |
| DAO 层 commit      | 事务边界不清晰               | 移除 DAO 层的 commit，在 Service 层管理 |
| API 层事务         | 职责混乱                     | 将事务管理移至 Service 层               |
| 混用两种方式       | 事务边界模糊                 | 选择一种方式，不要混用                  |
| 忘记 flush/refresh | 返回的数据缺少 ID 或计算字段 | DAO 层增删改后立即 flush/refresh        |

### 7.2 最佳实践

1. **优先使用** **`@transactional`** **装饰器**，除非有复杂场景
2. **Service 层方法名体现事务边界**，如 `create_xxx`、`update_xxx`
3. **DAO 层方法保持原子性**，每个方法只做一件事
4. **异常要正确抛出**，不要吞异常，否则事务无法回滚
5. **日志记录事务状态**，便于排查问题

```Python
# ✅ 最佳实践示例
@transactional(propagation=Propagation.REQUIRED)
async def create_order(self, user_id: int, product_id: int):
    """创建订单 - 完整示例"""

    # 1. 参数验证
    if user_id <= 0 or product_id <= 0:
        raise ValueError("参数无效")

    # 2. 业务逻辑
    user = await self.user_dao.get_user_by_id(user_id)
    product = await self.product_dao.get_by_id(product_id)

    if user.balance < product.price:
        raise ValueError("余额不足")

    # 3. 扣款
    user.balance -= product.price

    # 4. 创建订单
    order = Order(user_id=user_id, product_id=product_id, amount=product.price)
    order = await self.order_dao.create(order)  # DAO 内部已 flush/refresh

    # 5. 记录日志
    Logger.info(f"订单创建成功: order_id={order.id}, user_id={user_id}")

    # 6. 返回结果
    return order
    # 方法结束，事务自动 commit
```

## 8. 代码审查检查清单

在代码审查时，检查以下要点：

- Service 层方法是否使用了事务管理（@transactional 或手动 begin()）
- DAO 层是否没有 commit() 或 rollback() 调用
- API 层是否没有事务管理代码
- DAO 层的增删改方法是否在操作后执行了 flush() 和 refresh()
- 是否存在隐式事务（select 后直接写，没有显式事务）
- 事务传播行为是否选择正确（默认 REQUIRED）
- 复杂场景是否使用了手动事务管理
- 异常处理是否正确（异常会触发 rollback）
- Celery 任务是否使用了独立的数据库会话
- 是否有长事务需要拆分

## 9. 参考资料

### 9.1 项目相关文件

- `utils/transaction.py` - 事务装饰器实现
- `database/database.py` - 数据库会话配置
- SQLAlchemy 事务文档：https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-begin-nested

### 9.2 实例参考

- `app/modules/product/services/membership_service.py` - @transactional 使用示例
- `app/modules/career_plan/services/career_plan_service.py` - 手动事务管理示例
- `app/common/pay/services/payment_order_service.py` - 复杂事务场景示例
- `app/modules/product/daos/membership_dao.py` - DAO 层 flush/refresh 示例

## 10. 版本历史

| 版本  | 日期       | 作者      | 变更说明 |
| ----- | ---------- | --------- | -------- |
| 1.0.0 | 2025-01-30 | aicv 团队 | 初始版本 |

*本文档由 AiCV 团队维护，如有疑问请联系技术负责人。*