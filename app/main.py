from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.router import route
from app.database.database import init_db
from app.utils.response import ResponseUtils, ResponseCode

import uvicorn
import sys
import os

# 导入中间件
from app.middlewares import ErrorHandlerMiddleware

# 输出python版本信息
print(f"Python version: {sys.version}")

description_text = """
FastAPI 用户管理系统
"""
app = FastAPI(
    title="FastAPI User Management",
    openapi_url="/openapi.json",
    description=description_text,
    version=settings.API_VERSION,
    contact=settings.CONTACT,
    terms_of_service="https://www.example.com/terms/",
    docs_url=None if settings.ENV == "prod" else "/docs"
)

# 添加错误处理中间件
app.add_middleware(ErrorHandlerMiddleware)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """后台服务启动后的初始化操作"""
    from app.utils.logger import Logger

    if settings.STARTUP_VERBOSE:
        Logger.info("开始初始化应用...")

    # 创建数据表
    await init_db()

    if settings.STARTUP_VERBOSE:
        Logger.info("应用初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    from app.utils.logger import Logger
    Logger.info("应用已关闭")


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")


@app.get("/llm-manager", include_in_schema=False)
async def llm_node_manager():
    """LLM Node 管理页面快捷入口"""
    from fastapi.responses import FileResponse
    import os
    static_file = os.path.join(os.path.dirname(__file__), "static", "llm_node_manager.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return RedirectResponse(url="/i/llm_node_manager.html")


# 将路由器包括到FastAPI主应用中
app.include_router(route)

# 静态文件存放在项目的 "static" 目录下
static_dir = os.path.join(os.path.dirname(__file__), "../static")
if os.path.exists(static_dir):
    app.mount("/i", StaticFiles(directory=static_dir), name="internal-static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    统一处理Pydantic请求验证错误
    """
    from app.utils.logger import Logger

    # 生成错误ID用于日志追踪
    import uuid
    error_id = f"VAL-{uuid.uuid4().hex[:8]}"

    # 提取错误信息
    errors = exc.errors()

    # 构建友好的错误消息
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(item) for item in err['loc'])
        error_messages.append(f"{loc}: {err['msg']}")

    # 记录验证错误日志
    Logger.warning(
        f"请求参数验证失败 [{error_id}]\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Errors: {error_messages}"
    )

    # 构建详细的错误数据
    error_detail = []
    for err in errors:
        error_detail.append({
            "field": " -> ".join(str(item) for item in err['loc']),
            "message": err['msg'],
            "type": err['type']
        })

    # 返回统一的ApiResponse格式
    response_data = ResponseUtils.error(
        code=ResponseCode.BAD_REQUEST,
        msg="请求参数验证失败",
        data={
            "error_id": error_id,
            "errors": error_detail
        }
    )

    return JSONResponse(
        status_code=422,
        content=response_data.model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    统一处理HTTPException
    """
    from app.utils.logger import Logger

    # 记录异常信息
    Logger.warning(f"HTTPException: {exc.status_code} - {exc.detail} - Path: {request.url.path}")

    # 判断detail是否已经是ResponseUtils格式
    if isinstance(exc.detail, dict) and "code" in exc.detail and "msg" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    else:
        # 转换为ResponseUtils格式
        if exc.status_code == 400:
            code = ResponseCode.BAD_REQUEST
        elif exc.status_code == 401:
            code = ResponseCode.UNAUTHORIZED
        elif exc.status_code == 403:
            code = ResponseCode.FORBIDDEN
        elif exc.status_code == 404:
            code = ResponseCode.NOT_FOUND
        elif exc.status_code == 500:
            code = ResponseCode.SERVER_ERROR
        else:
            code = ResponseCode.SERVER_ERROR

        response_data = ResponseUtils.error(
            code=code,
            msg=str(exc.detail)
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=response_data.model_dump()
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.RELOAD)
