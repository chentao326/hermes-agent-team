"""角色数据模型"""

from dataclasses import dataclass
from enum import Enum


class PermissionLevel(Enum):
    """角色权限级别"""

    READ_ONLY = "read_only"  # CEO: 无工具
    READ_BASH = "read_bash"  # PM/PJM/Architect/UX/QA/Reviewer: 只读 Bash
    FULL = "full"  # Backend/Frontend: 完整读写


# 权限到 Claude API tools 的映射
PERMISSION_TOOLS: dict[PermissionLevel, list[str]] = {
    PermissionLevel.READ_ONLY: [],
    PermissionLevel.READ_BASH: ["bash"],
    PermissionLevel.FULL: ["bash", "read_file", "write_file"],
}

# 角色 ID 到权限的映射
ROLE_PERMISSIONS: dict[str, PermissionLevel] = {
    "ceo": PermissionLevel.READ_ONLY,
    "pm": PermissionLevel.READ_BASH,
    "pjm": PermissionLevel.READ_BASH,
    "architect": PermissionLevel.READ_BASH,
    "backend": PermissionLevel.FULL,
    "frontend": PermissionLevel.FULL,
    "ux-designer": PermissionLevel.READ_BASH,
    "qa": PermissionLevel.READ_BASH,
    "reviewer": PermissionLevel.READ_BASH,
}

# 角色执行顺序（分析模式默认）
DEFAULT_ROLE_ORDER: list[str] = [
    "ceo",
    "pm",
    "pjm",
    "architect",
    "backend",
    "frontend",
    "ux-designer",
    "qa",
    "reviewer",
]

# 角色中文名
ROLE_NAMES: dict[str, str] = {
    "ceo": "CEO",
    "pm": "产品经理",
    "pjm": "项目经理",
    "architect": "架构师",
    "backend": "后端工程师",
    "frontend": "前端工程师",
    "ux-designer": "UX设计师",
    "qa": "测试工程师",
    "reviewer": "代码审查",
}

# 角色 ID 到定义文件名映射
ROLE_FILE_MAP: dict[str, str] = {
    "ceo": "ceo.md",
    "pm": "pm.md",
    "pjm": "pjm.md",
    "architect": "architect.md",
    "backend": "backend.md",
    "frontend": "frontend.md",
    "ux-designer": "ux-designer.md",
    "qa": "qa.md",
    "reviewer": "reviewer.md",
}


@dataclass(frozen=True)
class Role:
    """角色定义 — frozen=True 保证不可变性，list 字段用 field(default_factory=list)"""

    id: str
    name: str
    personality: str  # Markdown 全文
    permission: PermissionLevel
    capabilities: tuple[str, ...] = ()
    signature_questions: tuple[str, ...] = ()

    @property
    def output_marker(self) -> str:
        return f"## {self.name} 视角"

    @property
    def has_tools(self) -> bool:
        return self.permission != PermissionLevel.READ_ONLY

    @property
    def can_write(self) -> bool:
        return self.permission == PermissionLevel.FULL
