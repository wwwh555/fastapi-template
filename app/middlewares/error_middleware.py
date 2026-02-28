"""
Error handling middleware for the application
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import Logger
from app.utils.response import ResponseUtils, ResponseCode
from app.core.config import settings
from datetime import datetime
import traceback


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        error_id = f"ERR-{start_time.strftime('%Y%m%d%H%M%S')}"

        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            # 处理业务逻辑错误
            Logger.warning(
                f"Business error {error_id}: {str(e)}\n"
                f"Path: {request.url.path}\n"
                f"Method: {request.method}"
            )
            response_data = ResponseUtils.error(
                code=ResponseCode.BAD_REQUEST,
                msg=str(e),
                data={"error_id": error_id}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=response_data.model_dump()
            )

        except Exception as e:
            # 处理未捕获的异常
            Logger.error(
                f"Unhandled error {error_id}: {str(e)}\n"
                f"Path: {request.url.path}\n"
                f"Method: {request.method}\n"
                f"Traceback: {traceback.format_exc()}"
            )

            # 在生产环境中不返回详细错误信息
            if settings.ENV == "prod":
                error_msg = "服务器内部错误"
                error_detail = None
            else:
                error_msg = str(e)
                error_detail = {
                    "error_id": error_id,
                    "traceback": traceback.format_exc()
                }

            response_data = ResponseUtils.error(
                code=ResponseCode.SERVER_ERROR,
                msg=error_msg,
                data=error_detail
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data.model_dump()
            )
