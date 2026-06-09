"""LLM 客户端抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类

    所有 provider（Anthropic、OpenAI兼容、自定义）实现此接口。
    工作流引擎只依赖此接口，不感知具体 provider。
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """当前使用的模型名称"""

    @abstractmethod
    def stream_chat(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, list[dict[str, Any]], int]:
        """同步流式调用

        Args:
            system: system prompt
            messages: 对话历史
            tools: 工具定义列表，None 表示不使用工具
            temperature: 采样温度
            max_tokens: 最大输出 tokens
            on_chunk: 流式文本回调

        Returns:
            (输出文本, 工具调用列表, 输入token数)

            工具调用列表格式: [{"id": "xxx", "name": "bash", "input": {...}}]
            如果没有工具调用，返回空列表
        """

    @abstractmethod
    async def stream_chat_async(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, list[dict[str, Any]], int]:
        """异步流式调用，参数和返回值同 stream_chat"""

    def build_tool_result_messages(
        self,
        tool_calls: list[dict[str, Any]],
        tool_results: list[str],
    ) -> list[dict[str, Any]]:
        """将工具调用结果转为 provider 通用的消息格式

        默认返回 OpenAI 兼容格式（tool role），Anthropic 可覆盖。
        """
        messages: list[dict[str, Any]] = []
        # assistant message with tool calls
        assistant_content = []
        for tc in tool_calls:
            assistant_content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"],
            })
        messages.append({"role": "assistant", "content": assistant_content})

        # tool results
        tool_result_content = []
        for tc, result in zip(tool_calls, tool_results):
            tool_result_content.append({
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": result,
            })
        messages.append({"role": "user", "content": tool_result_content})

        return messages