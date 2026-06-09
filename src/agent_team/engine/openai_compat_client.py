"""OpenAI 兼容 LLM 客户端

支持所有 OpenAI API 兼容的 provider：
- OpenAI (GPT-4o, GPT-4.1, etc.)
- DeepSeek
- 月之暗面 (Moonshot)
- 智谱 (GLM)
- OpenRouter
- vLLM / Ollama 等本地部署
- 任何兼容 OpenAI chat/completions API 的服务
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI, OpenAI

from agent_team.engine.base import BaseLLMClient

# OpenAI 格式的函数工具定义
BASH_FUNCTION = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "执行 Bash 命令并返回输出",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的 Bash 命令"},
            },
            "required": ["command"],
        },
    },
}

READ_FILE_FUNCTION = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "读取文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "offset": {"type": "integer", "description": "起始行号（0-based）", "default": 0},
                "limit": {"type": "integer", "description": "最大行数", "default": 2000},
            },
            "required": ["path"],
        },
    },
}

WRITE_FILE_FUNCTION = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "写入文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的内容"},
            },
            "required": ["path", "content"],
        },
    },
}

# 权限 → 工具映射（OpenAI 函数调用格式）
ROLE_TOOLS_OPENAI = {
    "read_only": None,
    "read_bash": [BASH_FUNCTION],
    "full": [BASH_FUNCTION, READ_FILE_FUNCTION, WRITE_FILE_FUNCTION],
}


class OpenAICompatClient(BaseLLMClient):
    """OpenAI 兼容 LLM 客户端

    适用于：OpenAI、DeepSeek、Moonshot、OpenRouter、vLLM、Ollama 等
    任何兼容 OpenAI chat/completions API 的服务。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        organization: str | None = None,
    ):
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if organization:
            client_kwargs["organization"] = organization

        self._client = OpenAI(**client_kwargs)
        self._async_client = AsyncOpenAI(**client_kwargs)

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

        # 构建消息列表（OpenAI 格式：system 单独传）
        api_messages = [{"role": "system", "content": system}] + messages

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": api_messages,
            "max_tokens": max_tok,
            "temperature": temp,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        full_text = ""
        input_tokens = 0
        tool_calls_accum: dict[int, dict[str, Any]] = {}

        stream = self._client.chat.completions.create(**kwargs)

        for chunk in stream:
            # 提取 usage
            if hasattr(chunk, "usage") and chunk.usage:
                input_tokens = getattr(chunk.usage, "prompt_tokens", 0) or input_tokens

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 文本
            if delta.content:
                full_text += delta.content
                if on_chunk:
                    on_chunk(delta.content)

            # 工具调用（流式增量）
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_accum:
                        tool_calls_accum[idx] = {
                            "id": tc_delta.id or "",
                            "name": tc_delta.function.name if tc_delta.function and tc_delta.function.name else "",
                            "arguments": "",
                        }
                    if tc_delta.id:
                        tool_calls_accum[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_accum[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_accum[idx]["arguments"] += tc_delta.function.arguments

        # 解析工具调用
        tool_calls = []
        if tool_calls_accum:
            import json
            for idx in sorted(tool_calls_accum):
                tc = tool_calls_accum[idx]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": args,
                })

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

        api_messages = [{"role": "system", "content": system}] + messages

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": api_messages,
            "max_tokens": max_tok,
            "temperature": temp,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        full_text = ""
        input_tokens = 0
        tool_calls_accum: dict[int, dict[str, Any]] = {}

        stream = await self._async_client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if hasattr(chunk, "usage") and chunk.usage:
                input_tokens = getattr(chunk.usage, "prompt_tokens", 0) or input_tokens

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                full_text += delta.content
                if on_chunk:
                    on_chunk(delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_accum:
                        tool_calls_accum[idx] = {
                            "id": tc_delta.id or "",
                            "name": tc_delta.function.name if tc_delta.function and tc_delta.function.name else "",
                            "arguments": "",
                        }
                    if tc_delta.id:
                        tool_calls_accum[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_accum[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_accum[idx]["arguments"] += tc_delta.function.arguments

        tool_calls = []
        if tool_calls_accum:
            import json
            for idx in sorted(tool_calls_accum):
                tc = tool_calls_accum[idx]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": args,
                })

        return full_text, tool_calls, input_tokens

    # ── 工具调用结果格式 ─────────────────────────────────

    def build_tool_result_messages(
        self,
        tool_calls: list[dict[str, Any]],
        tool_results: list[str],
    ) -> list[dict[str, Any]]:
        """OpenAI 格式：assistant tool_calls + 各个 tool role 消息"""
        # assistant 消息带 tool_calls
        assistant_tool_calls = []
        for tc in tool_calls:
            assistant_tool_calls.append({
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": __import__("json").dumps(tc["input"]),
                },
            })

        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": assistant_tool_calls,
            }
        ]

        # 每个 tool result 一条 message
        for tc, result in zip(tool_calls, tool_results, strict=False):
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        return messages