"""工作流引擎基类"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowContext:
    """工作流共享状态"""

    requirement: str
    role_outputs: dict[str, str] = field(default_factory=dict)
    current_role: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """工作流执行结果"""

    requirement: str
    role_outputs: dict[str, str]
    synthesis: str = ""
    total_tokens: int = 0
    elapsed_seconds: float = 0.0
    mode: str = "analysis"
    errors: list[str] = field(default_factory=list)