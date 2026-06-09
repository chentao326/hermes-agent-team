"""JSON 结构化输出渲染器"""

from __future__ import annotations

import json
from agent_team.output.base import OutputRenderer
from agent_team.roles.models import Role


class JsonRenderer(OutputRenderer):
    """JSON 结构化输出渲染器

    缓冲所有输出，最终输出一个 JSON 对象。
    适用于管道集成和程序化消费。
    """

    def __init__(self) -> None:
        self._role_outputs: dict[str, str] = {}
        self._synthesis: str = ""
        self._errors: list[str] = []
        self._requirement: str = ""
        self._mode: str = ""
        self._model: str = ""

    def render_header(self, requirement: str, mode: str, model: str) -> None:
        self._requirement = requirement
        self._mode = mode
        self._model = model

    def render_role_start(self, role: Role, index: int, total: int) -> None:
        pass  # JSON 模式不实时输出

    def render_role_chunk(self, text: str) -> None:
        pass  # JSON 模式缓冲到 finalize

    def render_role_end(self, role: Role) -> None:
        # 从 _buffer 收集已完成的内容
        pass  # 由 add_role_output 外部调用

    def add_role_output(self, role_id: str, output: str) -> None:
        """外部API：添加角色输出"""
        self._role_outputs[role_id] = output

    def render_synthesis(self, text: str) -> None:
        self._synthesis = text

    def render_error(self, error: Exception) -> None:
        self._errors.append(str(error))

    def get_role_outputs(self) -> dict[str, str]:
        return dict(self._role_outputs)

    def finalize(self) -> dict[str, str]:
        return dict(self._role_outputs)

    def to_json(self, elapsed: float = 0.0, total_tokens: int = 0) -> str:
        """渲染最终 JSON 输出"""
        data = {
            "requirement": self._requirement,
            "mode": self._mode,
            "model": self._model,
            "roles": dict(self._role_outputs),
            "synthesis": self._synthesis,
            "total_tokens": total_tokens,
            "elapsed_seconds": elapsed,
        }
        if self._errors:
            data["errors"] = self._errors
        return json.dumps(data, ensure_ascii=False, indent=2)