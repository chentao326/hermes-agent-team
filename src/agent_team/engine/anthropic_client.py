"""Anthropic (Claude) LLM 客户端"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, Callable

import anthropic

from agent_team.engine.base import BaseLLMClient


# Anthropic 格式的工具定义
BASH_TOOL = {
    "name": "bash",
    "description": "执行 Bash 命令并返回输出",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 Bash 命令"},
        },
        "required": ["command"],
    },
}

READ_FILE_TOOL = {
    "name": "read_file",
    "description": "读取文件内容",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "offset": {"type": "integer", "description": "起始行号（0-based）", "default": 0},
            "limit": {"type": "integer", "description": "最大行数", "default": 2000},
        },
        "required": ["path"],
    },
}

WRITE_FILE_TOOL = {
    "name": "write_file",
    "description": "写入文件内容",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "要写入的内容"},
        },
        "required": ["path", "content"],
    },
}

# 权限 → 工具映射
ROLE_TOOLS_ANTHROPIC = {
    "read_only": None,
    "read_bash": [BASH_TOOL],
    "full": [BASH_TOOL, READ_FILE_TOOL, WRITE_FILE_TOOL],
}


def _convert_tools_to_anthropic(tools: list[dict[str, Any]] | None) -> list[dict] | object:
    """将通用工具格式转为 Anthropic 格式。

    通用格式和 Anthropic 格式相同（name/description/input_schema），
    所以直接透传；None 转为 NOT_GIVEN。
    """
    if tools is None:
        return anthropic.NOT_GIVEN
    return tools


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 客户端"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = anthropic.Anthropic(**client_kwargs)
        self._async_client = anthropic.AsyncAnthropic(**client_kwargs)

    @property
    def model_name(self) -> str:
        return self._model

    # ── 同步流式 ──────────────────────────────────────────

    def stream_chat(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, list[dict[str, Any]], int]:
        temp = temperature or self._temperature
        max_tok = max_tokens or self._max_tokens
        anthropic_tools = _convert_tools_to_anthropic(tools)

        full_text = ""
        input_tokens = 0

        with self._client.messages.stream(
            model=self._model,
            max_tokens=max_tok,
            temperature=temp,
            system=system,
            messages=messages,
            tools=anthropic_tools,
        ) as stream:
            current_text = ""
            for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text") and event.delta.text:
                        current_text += event.delta.text
                        if on_chunk:
                            on_chunk(event.delta.text)
                elif event.type == "message_start":
                    if hasattr(event, "message") and hasattr(event.message, "usage"):
                        input_tokens = getattr(event.message.usage, "input_tokens", 0)

            response = stream.get_final_message()
            full_text += current_text

        # 提取工具调用
        tool_calls = self._extract_tool_calls(response)

        return full_text, tool_calls, input_tokens

    # ── 异步流式 ──────────────────────────────────────────

    async def stream_chat_async(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, list[dict[str, Any]], int]:
        temp = temperature or self._temperature
        max_tok = max_tokens or self._max_tokens
        anthropic_tools = _convert_tools_to_anthropic(tools)

        full_text = ""
        input_tokens = 0

        async with self._async_client.messages.stream(
            model=self._model,
            max_tokens=max_tok,
            temperature=temp,
            system=system,
            messages=messages,
            tools=anthropic_tools,
        ) as stream:
            current_text = ""
            async for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text") and event.delta.text:
                        current_text += event.delta.text
                        if on_chunk:
                            on_chunk(event.delta.text)

            response = await stream.get_final_message()
            full_text += current_text
            input_tokens = getattr(response.usage, "input_tokens", 0) if hasattr(response, "usage") else 0

        tool_calls = self._extract_tool_calls(response)
        return full_text, tool_calls, input_tokens

    # ── 工具调用结果格式 ─────────────────────────────────

    def build_tool_result_messages(
        self,
        tool_calls: list[dict[str, Any]],
        tool_results: list[str],
    ) -> list[dict[str, Any]]:
        """Anthropic 格式：assistant content blocks + user tool_result blocks"""
        assistant_content = []
        for tc in tool_calls:
            assistant_content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"],
            })

        tool_result_content = []
        for tc, result in zip(tool_calls, tool_results):
            tool_result_content.append({
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": result,
            })

        return [
            {"role": "assistant", "content": assistant_content},
            {"role": "user", "content": tool_result_content},
        ]

    # ── 内部方法 ──────────────────────────────────────────

    @staticmethod
    def _extract_tool_calls(response) -> list[dict[str, Any]]:
        """从 Anthropic 响应中提取工具调用"""
        calls = []
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "tool_use":
                calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": dict(block.input) if hasattr(block.input, "items") else block.input,
                })
        return calls