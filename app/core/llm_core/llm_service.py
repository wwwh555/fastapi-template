import asyncio
import base64
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Type, Optional, Union
from app.utils.logger import Logger
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.messages import HumanMessage
from pydantic import ValidationError


class LLMServiceError(Exception):
    """LLM服务基础异常类"""
    def __init__(self, message: str, error_type: str = "UNKNOWN", details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = datetime.now()


class LLMInvokeError(LLMServiceError):
    """LLM调用错误"""
    def __init__(self, message: str, attempt: int = None, max_attempts: int = None):
        super().__init__(message, "INVOKE_ERROR", {
            "attempt": attempt,
            "max_attempts": max_attempts
        })


class LLMParsingError(LLMServiceError):
    """LLM输出解析错误"""
    def __init__(self, message: str, raw_output: str = None, schema_info: str = None):
        super().__init__(message, "PARSING_ERROR", {
            "raw_output": raw_output,
            "schema_info": schema_info
        })


class LLMService:
    """通用LLM服务类 - 增强版本，包含详细的错误处理和日志记录"""

    @staticmethod
    def _sanitize_input_for_logging(input_variables: Dict[str, Any], max_length: int = 1000) -> Dict[str, Any]:
        """
        清理输入变量用于日志记录（避免日志过长）

        Args:
            input_variables: 原始输入变量
            max_length: 单个字段的最大长度

        Returns:
            Dict[str, Any]: 清理后的输入变量
        """
        sanitized = {}
        for key, value in input_variables.items():
            if isinstance(value, str):
                if len(value) > max_length:
                    sanitized[key] = value[:max_length] + f"... [截断，总长度: {len(value)}]"
                else:
                    sanitized[key] = value
            elif isinstance(value, (dict, list)):
                str_value = str(value)
                if len(str_value) > max_length:
                    sanitized[key] = str_value[:max_length] + f"... [截断，总长度: {len(str_value)}]"
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def _diagnose_parsing_error(error: Exception, raw_output: str, parser_type: Type) -> Dict[str, Any]:
        """
        诊断解析错误并提供详细信息

        Args:
            error: 解析异常
            raw_output: LLM原始输出
            parser_type: 解析器类型

        Returns:
            Dict[str, Any]: 诊断信息
        """
        diagnosis = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "parser_type": str(parser_type),
            "raw_output_length": len(raw_output) if raw_output else 0,
            "raw_output_preview": raw_output[:500] if raw_output else None,
            "suggestions": []
        }

        # 基于错误类型提供建议
        if isinstance(error, ValidationError):
            diagnosis["validation_errors"] = []
            for validation_error in error.errors():
                diagnosis["validation_errors"].append({
                    "field": ".".join(str(loc) for loc in validation_error.get("loc", [])),
                    "message": validation_error.get("msg", ""),
                    "type": validation_error.get("type", "")
                })
            diagnosis["suggestions"].append("检查LLM输出是否包含所有必需字段")
            diagnosis["suggestions"].append("验证字段类型是否与schema定义匹配")

        if "JSON" in str(error).upper() or "json" in str(error).lower():
            diagnosis["suggestions"].append("检查LLM输出是否为有效的JSON格式")
            diagnosis["suggestions"].append("查看是否存在未闭合的括号或引号")

        # 检查是否返回了schema定义而不是数据
        if raw_output and ("$defs" in raw_output or "properties" in raw_output):
            diagnosis["likely_schema_confusion"] = True
            diagnosis["suggestions"].append("LLM可能返回了schema定义而不是实际数据")
            diagnosis["suggestions"].append("考虑优化提示词，明确要求返回数据而不是schema")

        return diagnosis

    @staticmethod
    def _calculate_backoff_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0) -> float:
        """
        计算指数退避延迟时间

        Args:
            attempt: 当前尝试次数（从0开始）
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）

        Returns:
            float: 延迟时间（秒）
        """
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)

    @staticmethod
    async def ainvoke(
            prompt_template: Any,
            input_variables: Dict[str, Any],
            output_parser: Optional[PydanticOutputParser] = None,
            model: Any = None,
            max_retries: int = 2,
            enable_detailed_logging: bool = True
    ) -> Any:
        """
        通用LLM调用方法 - 增强版本

        Args:
            prompt_template: 提示模板
            input_variables: 输入变量字典
            output_parser: 输出解析器（可选）
            model: 要使用的LLM模型（默认为None）
            max_retries: 最大重试次数
            enable_detailed_logging: 是否启用详细日志记录

        Returns:
            Any: LLM响应结果

        Raises:
            LLMInvokeError: LLM调用失败
            LLMParsingError: 输出解析失败
        """
        # 生成唯一的请求ID用于追踪
        request_id = f"llm_req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            # 记录请求开始
            if enable_detailed_logging:
                sanitized_input = LLMService._sanitize_input_for_logging(input_variables)
                Logger.info(f"[{request_id}] 开始LLM调用 - 输入变量键: {list(input_variables.keys())}")
                Logger.debug(f"[{request_id}] 输入变量详情: {sanitized_input}")
            else:
                Logger.info(f"[{request_id}] 开始LLM调用")

            # 模型初始化
            if model is None:
                try:
                    from core.models import llm_powerful
                    model = llm_powerful
                    Logger.debug(f"[{request_id}] 使用默认模型: llm_powerful")
                except ImportError as e:
                    Logger.error(f"[{request_id}] 无法导入默认模型: {str(e)}")
                    raise LLMInvokeError(f"无法导入默认模型: {str(e)}")

            # 构建chain
            try:
                if output_parser:
                    chain = prompt_template | model | output_parser
                    Logger.debug(f"[{request_id}] 构建链: prompt -> model(模型名称:{model.model_name}) -> {type(output_parser).__name__}")
                else:
                    chain = prompt_template | model | StrOutputParser()
                    Logger.debug(f"[{request_id}] 构建链: prompt -> model(模型名称:{model.model_name}) -> StrOutputParser")
            except Exception as e:
                Logger.error(f"[{request_id}] 构建处理链失败: {str(e)}")
                raise LLMInvokeError(f"构建处理链失败: {str(e)}")

            # 重试循环
            last_error = None
            raw_llm_output = None

            for attempt in range(max_retries + 1):  # +1 因为第一次不算重试
                try:
                    Logger.info(f"[{request_id}] 执行LLM调用 (尝试 {attempt + 1}/{max_retries + 1})")

                    # 执行LLM调用
                    response = await chain.ainvoke(input_variables)

                    # 记录成功
                    Logger.info(f"[{request_id}] LLM调用成功 - 响应类型: {type(response).__name__}")
                    if enable_detailed_logging:
                        if isinstance(response, str):
                            Logger.debug(f"[{request_id}] 响应长度: {len(response)}字符")
                            if len(response) <= 1000:
                                Logger.debug(f"[{request_id}] 响应内容: {response}")
                            else:
                                Logger.debug(f"[{request_id}] 响应预览: {response[:500]}...")
                        else:
                            Logger.debug(f"[{request_id}] 响应对象: {type(response)}")

                    return response

                except ValidationError as e:
                    # Pydantic验证错误 - 通常是解析错误
                    raw_llm_output = getattr(e, 'raw_output', None) or str(e)
                    diagnosis = LLMService._diagnose_parsing_error(e, raw_llm_output, type(output_parser) if output_parser else None)

                    Logger.error(f"[{request_id}] 输出解析失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                    Logger.error(f"[{request_id}] 诊断信息: {json.dumps(diagnosis, ensure_ascii=False, indent=2)}")

                    last_error = LLMParsingError(
                        f"输出解析失败: {str(e)}",
                        raw_output=raw_llm_output,
                        schema_info=str(type(output_parser)) if output_parser else None
                    )

                except Exception as e:
                    # 其他错误（网络、模型等）
                    Logger.error(f"[{request_id}] LLM调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                    Logger.error(f"[{request_id}] 错误堆栈: {traceback.format_exc()}")

                    last_error = LLMInvokeError(
                        f"LLM调用失败: {str(e)}",
                        attempt=attempt + 1,
                        max_attempts=max_retries + 1
                    )

                # 如果不是最后一次尝试，则等待后重试
                if attempt < max_retries:
                    delay = LLMService._calculate_backoff_delay(attempt)
                    Logger.info(f"[{request_id}] 等待 {delay:.2f} 秒后重试...")
                    await asyncio.sleep(delay)

            # 所有重试都失败了
            Logger.error(f"[{request_id}] 所有重试都失败，抛出最后一个错误")
            if last_error:
                raise last_error
            else:
                raise LLMInvokeError("未知错误：所有重试都失败但没有捕获到具体错误")

        except (LLMServiceError, LLMParsingError, LLMInvokeError):
            # 重新抛出我们自定义的错误
            raise
        except Exception as e:
            # 捕获所有其他未预期的错误
            Logger.error(f"[{request_id}] 意外错误: {str(e)}")
            Logger.error(f"[{request_id}] 错误堆栈: {traceback.format_exc()}")
            raise LLMInvokeError(f"意外错误: {str(e)}")

    @staticmethod
    async def ainvoke_multimodal(
            messages: list,
            output_parser: Optional[PydanticOutputParser] = None,
            model: Any = None,
            max_retries: int = 2,
            enable_detailed_logging: bool = True
    ) -> Any:
        """
        多模态LLM调用方法 - 支持图片、语音等多模态输入

        Args:
            messages: LangChain 消息列表（支持 HumanMessage, SystemMessage 等）
                      消息 content 可以包含多模态内容，如图片 URL、base64 等
            output_parser: 输出解析器（可选）
            model: 要使用的LLM模型（默认为None）
            max_retries: 最大重试次数
            enable_detailed_logging: 是否启用详细日志记录

        Returns:
            Any: LLM响应结果

        Raises:
            LLMInvokeError: LLM调用失败
            LLMParsingError: 输出解析失败

        使用示例:
            ```python
            from langchain_core.messages import HumanMessage

            # 图片理解
            messages = [
                HumanMessage(content=[
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
                    {"type": "text", "text": "请分析这张图片"}
                ])
            ]
            result = await llm_service.ainvoke_multimodal(
                messages=messages,
                output_parser=my_parser,
                model=my_vlm_model
            )
            ```
        """
        # 生成唯一的请求ID用于追踪
        request_id = f"llm_multi_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            # 记录请求开始
            if enable_detailed_logging:
                messages_summary = [
                    {
                        "type": type(msg).__name__,
                        "content_type": type(msg.content).__name__ if not isinstance(msg.content, str) else "str",
                        "content_length": len(str(msg.content))
                    }
                    for msg in messages
                ]
                Logger.info(f"[{request_id}] 开始多模态LLM调用 -使用模型:{model.model_name} - 消息数: {len(messages)}, 类型: {messages_summary}")
            else:
                Logger.info(f"[{request_id}] 开始多模态LLM调用 -使用模型:{model.model_name}")

            # 模型初始化
            if model is None:
                try:
                    from core.models import llm_powerful
                    model = llm_powerful
                    Logger.debug(f"[{request_id}] 使用默认模型: llm_powerful")
                except ImportError as e:
                    Logger.error(f"[{request_id}] 无法导入默认模型: {str(e)}")
                    raise LLMInvokeError(f"无法导入默认模型: {str(e)}")

            # 直接调用模型（不使用 prompt_template）
            last_error = None
            raw_llm_output = None

            for attempt in range(max_retries + 1):
                try:
                    Logger.info(f"[{request_id}] 执行多模态LLM调用 (尝试 {attempt + 1}/{max_retries + 1})")

                    # 直接调用模型
                    response = await model.ainvoke(messages)

                    # 如果有 parser，进行解析
                    if output_parser:
                        result = output_parser.parse(response.content)
                        Logger.info(f"[{request_id}] 多模态LLM调用成功 - 已解析为: {type(result).__name__}")
                        return result
                    else:
                        # 没有 parser，返回原始内容
                        Logger.info(f"[{request_id}] 多模态LLM调用成功 - 原始响应类型: {type(response.content).__name__}")
                        return response.content

                except ValidationError as e:
                    # Pydantic验证错误
                    raw_llm_output = getattr(e, 'raw_output', None) or response.content if 'response' in locals() else str(e)
                    diagnosis = LLMService._diagnose_parsing_error(e, raw_llm_output, type(output_parser) if output_parser else None)

                    Logger.error(f"[{request_id}] 输出解析失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                    Logger.error(f"[{request_id}] 诊断信息: {json.dumps(diagnosis, ensure_ascii=False, indent=2)}")

                    last_error = LLMParsingError(
                        f"输出解析失败: {str(e)}",
                        raw_output=raw_llm_output,
                        schema_info=str(type(output_parser)) if output_parser else None
                    )

                except Exception as e:
                    # 其他错误
                    Logger.error(f"[{request_id}] 多模态LLM调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                    Logger.error(f"[{request_id}] 错误堆栈: {traceback.format_exc()}")

                    last_error = LLMInvokeError(
                        f"多模态LLM调用失败: {str(e)}",
                        attempt=attempt + 1,
                        max_attempts=max_retries + 1
                    )

                # 如果不是最后一次尝试，则等待后重试
                if attempt < max_retries:
                    delay = LLMService._calculate_backoff_delay(attempt)
                    Logger.info(f"[{request_id}] 等待 {delay:.2f} 秒后重试...")
                    await asyncio.sleep(delay)

            # 所有重试都失败了
            Logger.error(f"[{request_id}] 所有重试都失败，抛出最后一个错误")
            if last_error:
                raise last_error
            else:
                raise LLMInvokeError("未知错误：所有重试都失败但没有捕获到具体错误")

        except (LLMServiceError, LLMParsingError, LLMInvokeError):
            # 重新抛出我们自定义的错误
            raise
        except Exception as e:
            # 捕获所有其他未预期的错误
            Logger.error(f"[{request_id}] 意外错误: {str(e)}")
            Logger.error(f"[{request_id}] 错误堆栈: {traceback.format_exc()}")
            raise LLMInvokeError(f"意外错误: {str(e)}")

    @staticmethod
    def _build_multimodal_content(
        text: str,
        image_input: Optional[Union[str, bytes]] = None
    ) -> list:
        """
        构建多模态消息内容（仅支持图片）

        注意：音频请使用 ainvoke_audio 方法，它使用专门的 audio.transcriptions API

        Args:
            text: 文本内容
            image_input: 图片输入，支持：
                - 文件路径（str）
                - 图片 URL（str，以 http/https 开头）
                - base64 编码（str）
                - 图片字节流（bytes）

        Returns:
            list: 多模态内容列表，可用于 HumanMessage
        """
        content = [{"type": "text", "text": text}]

        # 处理图片输入
        if image_input:
            if isinstance(image_input, bytes):
                # (1) 字节流 -> base64
                base64_image = base64.b64encode(image_input).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
            elif isinstance(image_input, str):
                if image_input.startswith(('http://', 'https://')):
                    # (2) URL
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": image_input}
                    })
                elif Path(image_input).is_file():
                    # (3) 文件路径 -> 读取并 base64
                    with open(image_input, "rb") as f:
                        base64_image = base64.b64encode(f.read()).decode('utf-8')
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    })
                else:
                    # (4) 假设已经是 base64 编码
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_input}"}
                    })

        return content

    @staticmethod
    async def ainvoke_vision(
            prompt_template: Any = None,
            input_variables: Optional[Dict[str, Any]] = None,
            image_file: Optional[Union[str, bytes]] = None,
            output_parser: Optional[PydanticOutputParser] = None,
            model: Any = None,
            max_retries: int = 2,
            enable_detailed_logging: bool = True
    ) -> Any:
        """
        视觉模型调用方法 - 支持图片理解

        Args:
            prompt_template: 提示模板（可选，如果提供则使用模板格式化）
            input_variables: 输入变量字典（可选）
            image_file: 图片输入，支持：
                - 文件路径（str）
                - 图片 URL（str，以 http/https 开头）
                - base64 编码（str）
                - 图片字节流（bytes）
            output_parser: 输出解析器（可选）
            model: 要使用的视觉模型（默认为None）
            max_retries: 最大重试次数
            enable_detailed_logging: 是否启用详细日志记录

        Returns:
            Any: LLM响应结果

        使用示例:
            ```python
            # 方式1: 使用 prompt_template
            result = await llm_service.ainvoke_vision(
                prompt_template=prompt,
                input_variables={"question": "这是什么?"},
                image_file="/path/to/image.jpg",
                output_parser=parser,
                model=model
            )

            # 方式2: 直接使用文本（不使用模板）
            result = await llm_service.ainvoke_vision(
                image_file="/path/to/image.jpg",
                model=model
            )
            ```
        """
        request_id = f"llm_vision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            # 构建文本内容
            if prompt_template and input_variables is not None:
                # 使用模板格式化
                text = prompt_template.format(**input_variables)
            elif prompt_template and input_variables is None:
                text = prompt_template.format()  # 没有输入的动态变量，直接格式化为字符串即可
            else:
                # 使用默认文本或空文本
                text = prompt_template if isinstance(prompt_template, str) else "请分析这张图片"

            # 构建多模态内容
            content = LLMService._build_multimodal_content(text=text, image_input=image_file)
            messages = [HumanMessage(content=content)]

            # 记录请求
            if enable_detailed_logging:
                Logger.info(f"[{request_id}] 开始视觉模型调用 - 图片类型: {type(image_file).__name__}")
            else:
                Logger.info(f"[{request_id}] 开始视觉模型调用")

            # 调用多模态方法
            return await LLMService.ainvoke_multimodal(
                messages=messages,
                output_parser=output_parser,
                model=model,
                max_retries=max_retries,
                enable_detailed_logging=enable_detailed_logging
            )

        except Exception as e:
            Logger.error(f"[{request_id}] 视觉模型调用失败: {str(e)}")
            raise LLMInvokeError(f"视觉模型调用失败: {str(e)}")

    @staticmethod
    async def ainvoke_audio(
            audio_file: Union[str, bytes],
            model: Any = None,
            language: str = "zh",
            prompt: Optional[str] = None,
            max_retries: int = 2,
            enable_detailed_logging: bool = True
    ) -> str:
        """
        音频模型调用方法 - 支持 ASR（语音识别）

        注意：此方法使用 OpenAI 的 audio.transcriptions API，不是 chat API
        支持的模型：
        - OpenAI Whisper (whisper-1)
        - 智谱 GLM-ASR (需要使用 base_url 指向智谱)

        Args:
            audio_file: 音频输入，支持：
                - 文件路径（str）
                - 音频字节流（bytes）
                - (暂不支持 URL，需要先下载到本地)
            model: OpenAI 兼容的模型实例（需要包含 api_key 和 base_url）
                   示例：OpenAI(api_key="...", base_url="https://open.bigmodel.cn/api/paas/v4/")
            language: 语言代码（默认 "zh" 中文）
            prompt: 可选的提示词，用于改善识别效果
            max_retries: 最大重试次数
            enable_detailed_logging: 是否启用详细日志记录

        Returns:
            str: 识别的文本

        使用示例:
            ```python
            # 使用 OpenAI Whisper
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key="sk-...")
            result = await llm_service.ainvoke_audio(
                audio_file="/path/to/audio.wav",
                model=client
            )

            # 使用智谱 GLM-ASR
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key="your_zhipu_key",
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            )
            result = await llm_service.ainvoke_audio(
                audio_file="/path/to/audio.wav",
                model=client,
                language="zh"
            )
            ```
        """
        request_id = f"llm_audio_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            from openai import AsyncOpenAI

            # 确保 model 是 AsyncOpenAI 实例
            if not isinstance(model, AsyncOpenAI):
                raise ValueError("model 参数必须是 AsyncOpenAI 实例")

            # 处理音频文件输入
            if isinstance(audio_file, str):
                # 文件路径
                if not Path(audio_file).is_file():
                    raise FileNotFoundError(f"音频文件不存在: {audio_file}")
                file_obj = open(audio_file, "rb")
                should_close = True
            elif isinstance(audio_file, bytes):
                # 字节流 - 需要写入临时文件
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_file)
                    tmp_path = tmp.name
                file_obj = open(tmp_path, "rb")
                should_close = True
            else:
                raise TypeError(f"不支持的 audio_file 类型: {type(audio_file)}")

            try:
                # 记录请求
                if enable_detailed_logging:
                    Logger.info(f"[{request_id}] 开始音频模型调用 - 模型: {getattr(model, 'base_url', 'OpenAI')}")
                else:
                    Logger.info(f"[{request_id}] 开始音频模型调用")

                # 使用 OpenAI 的 audio.transcriptions API
                for attempt in range(max_retries + 1):
                    try:
                        Logger.info(f"[{request_id}] 执行音频模型调用 (尝试 {attempt + 1}/{max_retries + 1})")

                        # 调用 API
                        response = await model.audio.transcriptions.create(
                            model="GLM-ASR-Nano-2512" if "bigmodel" in getattr(model, 'base_url', '') else "whisper-1",
                            file=file_obj,
                            language=language,
                            prompt=prompt
                        )

                        text = response.text
                        Logger.info(f"[{request_id}] 音频识别成功 - 文本长度: {len(text)}")
                        return text

                    except Exception as e:
                        Logger.error(f"[{request_id}] 音频识别失败 (尝试 {attempt + 1}): {str(e)}")

                        if attempt < max_retries:
                            delay = LLMService._calculate_backoff_delay(attempt)
                            Logger.info(f"[{request_id}] 等待 {delay:.2f} 秒后重试...")
                            await asyncio.sleep(delay)
                        else:
                            raise LLMInvokeError(
                                f"音频识别失败: {str(e)}",
                                attempt=attempt + 1,
                                max_attempts=max_retries + 1
                            )

            finally:
                # 清理文件句柄
                if should_close:
                    file_obj.close()
                    # 如果是临时文件，删除它
                    if isinstance(audio_file, bytes):
                        try:
                            Path(tmp_path).unlink()
                        except:
                            pass

        except Exception as e:
            Logger.error(f"[{request_id}] 音频模型调用失败: {str(e)}")
            raise LLMInvokeError(f"音频模型调用失败: {str(e)}")


llm_service = LLMService()