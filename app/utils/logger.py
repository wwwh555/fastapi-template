"""
    general logger with user context support
"""
import logging
import logging.handlers
from contextvars import ContextVar
import os
import warnings
from app.core.config import settings

# 创建上下文变量来存储用户信息
user_id_ctx = ContextVar('user_id', default='unknown')
user_name_ctx = ContextVar('user_name', default='unknown')

# 确保日志目录存在
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

class UserContextFilter(logging.Filter):
    """
    日志过滤器，用于添加用户上下文信息
    """
    def filter(self, record):
        record.user_id = user_id_ctx.get()
        record.user_name = user_name_ctx.get()
        return True

def suppress_warnings():
    """抑制不必要的警告信息"""
    
    # 抑制Pydantic兼容性警告
    warnings.filterwarnings("ignore", 
                          message=".*populate_by_name.*",
                          category=UserWarning)
    warnings.filterwarnings("ignore", 
                          message=".*schema_extra.*", 
                          category=UserWarning)
    warnings.filterwarnings("ignore", 
                          message=".*is not a Python type.*", 
                          category=UserWarning)
    
    # 抑制其他不重要的警告
    warnings.filterwarnings("ignore", category=DeprecationWarning)

def configure_third_party_loggers():
    """配置第三方库的日志级别"""
    
    # SQLAlchemy 日志配置
    logging.getLogger('sqlalchemy.engine').setLevel(
        getattr(logging, settings.SQLALCHEMY_LOG_LEVEL.upper(), logging.WARNING)
    )
    logging.getLogger('sqlalchemy.pool').setLevel(
        getattr(logging, settings.SQLALCHEMY_LOG_LEVEL.upper(), logging.WARNING)
    )
    
    # 第三方库日志配置
    other_loggers = [
        'urllib3', 'requests', 'PIL', 'matplotlib', 'asyncio', 
        'aiohttp', 'httpx', 'httpcore', 'chardet', 'filelock'
    ]
    for logger_name in other_loggers:
        logging.getLogger(logger_name).setLevel(
            getattr(logging, settings.THIRD_PARTY_LOG_LEVEL.upper(), logging.WARNING)
        )

def setup_application_logging():
    """设置应用程序日志配置"""
    
    # 根据环境配置根日志级别
    if settings.ENV == "dev":
        root_level = logging.INFO
    elif settings.ENV == "test":
        root_level = logging.INFO  
    else:  # prod
        root_level = logging.WARNING
    
    # 配置根日志记录器
    logging.basicConfig(
        level=root_level,
        format='[%(asctime)s][%(levelname)s] [%(custom_filename)s:%(custom_lineno)d] [user:%(user_name)s(%(user_id)s)] - %(custom_funcName)s() - %(message)s' if settings.ENV == "dev"
               else '[%(asctime)s][%(name)s][%(levelname)s] [%(custom_filename)s:%(custom_lineno)d] [user:%(user_name)s(%(user_id)s)] - %(custom_funcName)s() - %(message)s',
        datefmt='%H:%M:%S' if settings.ENV == "dev" else '%Y-%m-%d %H:%M:%S'
    )

def initialize_logging():
    """初始化所有日志配置"""

    # 1. 抑制警告
    suppress_warnings()

    # 2. 配置应用日志
    setup_application_logging()

    # 3. 配置第三方库日志
    configure_third_party_loggers()

    # 4. 设置特殊处理
    # 禁用 "no ccache found" 警告
    os.environ.setdefault('PADDLE_DISABLE_WARNING', '1')

    if settings.STARTUP_VERBOSE:
        logging.getLogger("main").info(f"日志配置初始化完成 - 环境: {settings.ENV}")

def setup_third_party_loggers():
    """
    配置第三方库的日志级别 (兼容旧版本)
    """
    # 调用新的配置函数
    configure_third_party_loggers()

class Logger:
    """
    Enhanced logger class with user context support
    """
    __logger = None

    @classmethod
    def __get_logger(cls):
        if cls.__logger is None:
            cls.__logger = logging.getLogger("main")
            cls.__logger.setLevel(level=logging.DEBUG)

            # 添加用户上下文过滤器
            cls.__logger.addFilter(UserContextFilter())
            
            # 添加自定义字段过滤器，确保custom_filename等字段总是存在
            class CustomFieldsFilter(logging.Filter):
                def filter(self, record):
                    if not hasattr(record, "custom_filename"):
                        record.custom_filename = "unknown"
                    if not hasattr(record, "custom_lineno"):
                        record.custom_lineno = 0
                    if not hasattr(record, "custom_funcName"):
                        record.custom_funcName = "unknown"
                    return True
            
            cls.__logger.addFilter(CustomFieldsFilter())

            # 增强日志格式，包含详细的代码位置信息
            formatter = logging.Formatter(
                '[%(asctime)s][%(levelname)s] [%(custom_filename)s:%(custom_lineno)d] [user:%(user_name)s(%(user_id)s)]  - %(custom_funcName)s() - %(message)s',
                datefmt='%H:%M:%S'
            )
            # 控制台输出
            console = logging.StreamHandler()
            console.setFormatter(formatter)

            # 设置控制台日志级别
            console.setLevel(logging.DEBUG)

            cls.__logger.addHandler(console)
            cls.__logger.propagate = False
            if settings.FILE_LOG_ENABLED:
                try:
                    # 创建 logs 目录
                    os.makedirs(LOG_DIR, exist_ok=True)

                    # 检查目录是否有写入权限
                    if not os.access(LOG_DIR, os.W_OK):
                        cls.__logger.warning(f"日志目录 {LOG_DIR} 没有写入权限，将仅使用控制台日志")
                    else:
                        # 设置日志文件路径
                        log_file = os.path.join(LOG_DIR, 'app.log')

                        # 尝试创建文件以检查权限
                        try:
                            # 测试是否可以写入文件
                            test_file = log_file + '.test'
                            with open(test_file, 'w') as f:
                                f.write('test')
                            os.remove(test_file)
                        except (PermissionError, OSError) as e:
                            cls.__logger.warning(f"无法创建日志文件 {log_file}: {e}，将仅使用控制台日志")
                        else:
                            # 配置TimedRotatingFileHandler
                            file_handler = logging.handlers.TimedRotatingFileHandler(
                                filename=log_file,
                                when='midnight',  # 在午夜切割
                                interval=1,       # 每天切割一次
                                backupCount=7,    # 保留7天的日志文件
                                encoding='utf-8'
                            )
                            # 设置日志文件后缀格式为 .YYYY-MM-DD
                            file_handler.suffix = '%Y-%m-%d'
                            file_handler.setLevel(logging.INFO)
                            file_handler.setFormatter(formatter)

                            cls.__logger.addHandler(file_handler)
                            cls.__logger.info(f"文件日志已启用，日志文件: {log_file}")
                except (PermissionError, OSError) as e:
                    # 如果无法创建日志文件，只使用控制台日志，不中断应用启动
                    cls.__logger.warning(f"无法初始化文件日志 ({LOG_DIR}): {e}，将仅使用控制台日志")
                except Exception as e:
                    # 捕获所有其他异常，确保应用能够启动
                    cls.__logger.warning(f"初始化文件日志时出现未知错误: {e}，将仅使用控制台日志")

        return cls.__logger

    @staticmethod
    def set_user_context(user_id: str, user_name: str):
        """
        设置用户上下文信息
        """
        user_id_ctx.set(user_id)
        user_name_ctx.set(user_name)

    @staticmethod
    def clear_user_context():
        """
        清除用户上下文信息
        """
        user_id_ctx.set('unknown')
        user_name_ctx.set('unknown')

    @classmethod
    def error(cls, message):
        """
        log error
        """
        import inspect
        frame = inspect.currentframe().f_back
        # 使用自定义属性名，避免覆盖LogRecord内置属性
        # 获取相对路径
        filename = frame.f_code.co_filename
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 如果文件路径以项目根目录开头，则替换为相对路径
        if filename.startswith(project_root):
            filename = filename[len(project_root) + 1:]  # +1 是为了去掉路径分隔符

        extra = {
            'custom_filename': filename,
            'custom_lineno': frame.f_lineno,
            'custom_funcName': frame.f_code.co_name
        }
        cls.__get_logger().error(message, extra=extra, stacklevel=2)

    @classmethod
    def info(cls, message):
        """
        log information
        """
        import inspect
        frame = inspect.currentframe().f_back
        # 使用自定义属性名，避免覆盖LogRecord内置属性
        # 获取相对路径
        filename = frame.f_code.co_filename
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 如果文件路径以项目根目录开头，则替换为相对路径
        if filename.startswith(project_root):
            filename = filename[len(project_root) + 1:]  # +1 是为了去掉路径分隔符

        extra = {
            'custom_filename': filename,
            'custom_lineno': frame.f_lineno,
            'custom_funcName': frame.f_code.co_name
        }
        cls.__get_logger().info(message, extra=extra, stacklevel=2)

    @classmethod
    def warning(cls, message):
        """
        log warning
        """
        import inspect
        frame = inspect.currentframe().f_back
        # 使用自定义属性名，避免覆盖LogRecord内置属性
        # 获取相对路径
        filename = frame.f_code.co_filename
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 如果文件路径以项目根目录开头，则替换为相对路径
        if filename.startswith(project_root):
            filename = filename[len(project_root) + 1:]  # +1 是为了去掉路径分隔符

        extra = {
            'custom_filename': filename,
            'custom_lineno': frame.f_lineno,
            'custom_funcName': frame.f_code.co_name
        }
        cls.__get_logger().warning(message, extra=extra, stacklevel=2)

    @classmethod
    def debug(cls, message):
        """
        log debug information
        """
        import inspect
        frame = inspect.currentframe().f_back
        # 使用自定义属性名，避免覆盖LogRecord内置属性
        # 获取相对路径
        filename = frame.f_code.co_filename
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 如果文件路径以项目根目录开头，则替换为相对路径
        if filename.startswith(project_root):
            filename = filename[len(project_root) + 1:]  # +1 是为了去掉路径分隔符

        extra = {
            'custom_filename': filename,
            'custom_lineno': frame.f_lineno,
            'custom_funcName': frame.f_code.co_name
        }
        cls.__get_logger().debug(message, extra=extra, stacklevel=2)

    @classmethod
    def exception(cls, message):
        """
        log exception
        """
        import inspect
        frame = inspect.currentframe().f_back
        # 使用自定义属性名，避免覆盖LogRecord内置属性
        # 获取相对路径
        filename = frame.f_code.co_filename
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 如果文件路径以项目根目录开头，则替换为相对路径
        if filename.startswith(project_root):
            filename = filename[len(project_root) + 1:]  # +1 是为了去掉路径分隔符

        extra = {
            'custom_filename': filename,
            'custom_lineno': frame.f_lineno,
            'custom_funcName': frame.f_code.co_name
        }
        cls.__get_logger().exception(message, extra=extra, stacklevel=2)

    @classmethod
    def critical(cls, message):
        """
        log critical message
        """
        import inspect
        frame = inspect.currentframe().f_back
        # 使用自定义属性名，避免覆盖LogRecord内置属性
        # 获取相对路径
        filename = frame.f_code.co_filename
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 如果文件路径以项目根目录开头，则替换为相对路径
        if filename.startswith(project_root):
            filename = filename[len(project_root) + 1:]  # +1 是为了去掉路径分隔符

        extra = {
            'custom_filename': filename,
            'custom_lineno': frame.f_lineno,
            'custom_funcName': frame.f_code.co_name
        }
        cls.__get_logger().critical(message, extra=extra, stacklevel=2)

def get_logger(name: str = "main") -> logging.Logger:
    """获取配置好的日志记录器"""
    return logging.getLogger(name)

# 注意：日志配置在main.py中手动初始化，避免重复初始化