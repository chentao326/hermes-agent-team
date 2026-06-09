"""Markdown 文件输出渲染器"""

from __future__ import annotations

from agent_team.output.base import OutputRenderer
from agent_team.roles.models import Role


class MarkdownRenderer(OutputRenderer):
    """Markdown 格式输出渲染器

    生成结构化的 Markdown 报告，适合写入文件或查看。
    """

    def __init__(self) -> None:
        self._role_outputs: dict[str, str] = {}
        self._synthesis: str = ""
        self._requirement: str = ""
        self._mode: str = ""
        self._model: str = ""

    def render_header(self, requirement: str, mode: str, model: str) -> None:
        self._requirement = requirement
        self._mode = mode
        self._model = model

    def render_role_start(self, role: Role, index: int, total: int) -> None:
        pass

    def render_role_chunk(self, text: str) -> None:
        pass

    def render_role_end(self, role: Role) -> None:
        pass

    def add_role_output(self, role_id: str, output: str) -> None:
        """外部API：添加角色输出"""
        self._role_outputs[role_id] = output

    def render_synthesis(self, text: str) -> None:
        self._synthesis = text

    def render_error(self, error: Exception) -> None:
        pass

    def get_role_outputs(self) -> dict[str, str]:
        return dict(self._role_outputs)

    def finalize(self) -> dict[str, str]:
        return dict(self._role_outputs)

    def to_markdown(self, role_names: dict[str, str] | None = None, elapsed: float = 0.0, total_tokens: int = 0) -> str:
        """渲染最终 Markdown 输出"""
        mode_label = "分析模式" if self._mode == "analysis" else "执行模式"
        names = role_names or {}

        lines = [
            f"# Agent Team - {mode_label}报告\n",
            f"## 需求\n{self._requirement}\n",
            f"**模型**: {self._model} | **耗时**: {elapsed:.1f}s | **tokens**: {total_tokens:,}\n",
        ]

        for rid, output in self._role_outputs.items():
            name = names.get(rid, rid)
            lines.append(f"## {name}\n\n{output}\n")

        if self._synthesis:
            lines.append(f"## 综合结论\n\n{self._synthesis}\n")

        return "\n".join(lines)