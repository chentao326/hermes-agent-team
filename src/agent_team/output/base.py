"""输出渲染器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_team.roles.models import Role


class OutputRenderer(ABC):
    """输出渲染器抽象基类"""

    @abstractmethod
    def render_header(self, requirement: str, mode: str, model: str) -> None:
        """渲染工作流头部信息"""

    @abstractmethod
    def render_role_start(self, role: Role, index: int, total: int) -> None:
        """开始渲染一个角色的输出"""

    @abstractmethod
    def render_role_chunk(self, text: str) -> None:
        """渲染流式文本块"""

    @abstractmethod
    def render_role_end(self, role: Role) -> None:
        """完成一个角色的输出"""

    @abstractmethod
    def render_synthesis(self, text: str) -> None:
        """渲染综合结论"""

    @abstractmethod
    def render_error(self, error: Exception) -> None:
        """渲染错误信息"""

    @abstractmethod
    def get_role_outputs(self) -> dict[str, str]:
        """获取所有角色输出"""

    @abstractmethod
    def finalize(self) -> dict[str, str]:
        """完成渲染，返回所有输出"""
