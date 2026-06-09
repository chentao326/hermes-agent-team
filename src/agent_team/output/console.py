"""Rich 面板 + 流式输出渲染器"""

from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from agent_team.output.base import OutputRenderer
from agent_team.roles.models import Role

# 角色专属颜色
ROLE_COLORS: dict[str, str] = {
    "ceo": "bold red",
    "pm": "bold blue",
    "pjm": "bold yellow",
    "architect": "bold magenta",
    "backend": "bold green",
    "frontend": "bold cyan",
    "ux-designer": "bold white",
    "qa": "bold bright_green",
    "reviewer": "bold bright_red",
}


class ConsoleRenderer(OutputRenderer):
    """Rich 面板 + 流式输出渲染器"""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self._live: Live | None = None
        self._buffer: list[str] = []
        self._current_role: Role | None = None
        self._role_outputs: dict[str, str] = {}
        self._current_index: int = 0
        self._total: int = 0

    def render_header(self, requirement: str, mode: str, model: str) -> None:
        """渲染工作流头部信息"""
        mode_label = "分析模式" if mode == "analysis" else "执行模式"
        header = Text()
        header.append(" Agent Team ", style="bold white on blue")
        header.append(f" {mode_label} ", style="bold white on dark_green")
        header.append(f"\n\n 需求: {requirement[:100]}{'...' if len(requirement) > 100 else ''}")
        header.append(f"\n 模型: {model}")
        self.console.print(Panel(header, border_style="blue"))

    def render_role_start(self, role: Role, index: int, total: int) -> None:
        """开始渲染一个角色的输出"""
        self._current_role = role
        self._current_index = index
        self._total = total
        self._buffer = []

        color = ROLE_COLORS.get(role.id, "bold white")
        self.console.print()
        self.console.print(f"  ▶ [{index}/{total}] {role.name} 视角", style=color)
        self.console.print("  " + "─" * 50, style="dim")

    def render_role_chunk(self, text: str) -> None:
        """渲染流式文本块"""
        self._buffer.append(text)
        # 实时打印（不换行）
        self.console.print(text, end="", highlight=False)

    def render_role_end(self, role: Role) -> None:
        """完成一个角色的输出"""
        full_text = "".join(self._buffer)
        self._role_outputs[role.id] = full_text

        self.console.print()  # 换行
        self.console.print("  " + "─" * 50, style="dim")
        self._current_role = None
        self._buffer = []

    def render_synthesis(self, text: str) -> None:
        """渲染综合结论"""
        self.console.print()
        self.console.print(
            Panel(
                Markdown(text),
                title="[bold]综合结论[/bold]",
                border_style="bright_white",
                padding=(1, 2),
            )
        )

    def render_error(self, error: Exception) -> None:
        """渲染错误信息"""
        self.console.print(f"\n  [bold red]✗ 错误:[/bold red] {error}")

    def render_completion(self, elapsed: float, total_tokens: int = 0) -> None:
        """渲染完成信息"""
        stats = Text()
        stats.append("  ✓ 完成", style="bold green")
        stats.append(f" | 耗时 {elapsed:.1f}s")
        if total_tokens:
            stats.append(f" | tokens: {total_tokens:,}")
        stats.append(f" | {len(self._role_outputs)} 个角色", style="dim")
        self.console.print(stats)

    def get_role_outputs(self) -> dict[str, str]:
        """获取所有角色输出"""
        return dict(self._role_outputs)

    def finalize(self) -> dict[str, str]:
        """完成渲染，返回所有输出"""
        return dict(self._role_outputs)
