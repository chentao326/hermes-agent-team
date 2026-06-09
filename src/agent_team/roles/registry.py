"""角色注册表：加载、查找、过滤角色"""

from __future__ import annotations

import importlib.resources
import re
from pathlib import Path

from agent_team.exceptions import RoleNotFoundError
from agent_team.roles.models import (
    DEFAULT_ROLE_ORDER,
    ROLE_FILE_MAP,
    ROLE_NAMES,
    ROLE_PERMISSIONS,
    Role,
)


class RoleRegistry:
    """角色注册表"""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._load_builtin_roles()

    def _load_builtin_roles(self) -> None:
        """从包内 definitions/ 加载所有角色"""
        definitions_dir = importlib.resources.files("agent_team").joinpath("roles").joinpath("definitions")
        for role_id, filename in ROLE_FILE_MAP.items():
            ref = definitions_dir.joinpath(filename)
            personality = ref.read_text(encoding="utf-8")
            capabilities, questions = self._parse_personality(personality)
            role = Role(
                id=role_id,
                name=ROLE_NAMES[role_id],
                personality=personality,
                permission=ROLE_PERMISSIONS[role_id],
                capabilities=tuple(capabilities),
                signature_questions=tuple(questions),
            )
            self._roles[role_id] = role

    def load_custom_roles(self, custom_dir: Path) -> None:
        """从用户自定义目录覆盖角色定义"""
        if not custom_dir.is_dir():
            return
        for role_id, filename in ROLE_FILE_MAP.items():
            custom_file = custom_dir / filename
            if custom_file.is_file():
                personality = custom_file.read_text(encoding="utf-8")
                capabilities, questions = self._parse_personality(personality)
                role = Role(
                    id=role_id,
                    name=ROLE_NAMES[role_id],
                    personality=personality,
                    permission=ROLE_PERMISSIONS[role_id],
                    capabilities=tuple(capabilities),
                    signature_questions=tuple(questions),
                )
                self._roles[role_id] = role

    def get(self, role_id: str) -> Role:
        """按 ID 获取角色"""
        if role_id not in self._roles:
            available = ", ".join(self._roles.keys())
            raise RoleNotFoundError(f"角色 '{role_id}' 不存在。可用角色: {available}")
        return self._roles[role_id]

    def all(self) -> list[Role]:
        """按默认顺序返回所有角色"""
        return [self._roles[rid] for rid in DEFAULT_ROLE_ORDER if rid in self._roles]

    def filter(self, ids: list[str]) -> list[Role]:
        """按指定 ID 列表过滤角色，保持默认顺序"""
        return [self._roles[rid] for rid in DEFAULT_ROLE_ORDER if rid in ids and rid in self._roles]

    def ids(self) -> list[str]:
        """返回所有角色 ID"""
        return list(self._roles.keys())

    @staticmethod
    def _parse_personality(text: str) -> tuple[list[str], list[str]]:
        """从 Markdown 人格文本中解析核心能力和标志性问题"""
        capabilities: list[str] = []
        questions: list[str] = []

        # 解析核心能力列表
        cap_match = re.search(r"核心能力[：:]?\s*\n((?:\s*[-*]\s*.+\n?)+)", text)
        if cap_match:
            for line in cap_match.group(1).strip().splitlines():
                line = line.strip().lstrip("-*").strip()
                if line:
                    # 提取冒号前的能力名
                    cap_name = line.split("：")[0].split(":")[0].strip()
                    if cap_name:
                        capabilities.append(cap_name)

        # 解析标志性问题和变体（口头禅、标志性问题、核心信念、本能反应、审查清单等）
        patterns = [
            # 「...」格式的问题
            r"(?:标志性问题|口头禅)[：:]?\s*(.+?)(?:\n|$)",
            # 当被问到...时格式
            r"当被问到.+(?:时[，,])?\s*(.+?)(?:\n|$)",
            # 本能反应/核心信念/审查清单 后的「...」内容
            r"(?:本能反应|核心信念|审查清单|第一性原理)[：:]\s*(.+?)(?:\n|$)",
        ]
        for pattern in patterns:
            q_match = re.search(pattern, text)
            if q_match:
                raw = q_match.group(1).strip()
                # 提取「」中的内容
                bracket_content = re.findall(r"「([^」]+)」", raw)
                if bracket_content:
                    questions.extend(bracket_content)
                elif raw:
                    # 没有「」包裹，直接作为问题
                    # 短句可能包含多个「？」分隔的问题
                    parts = re.split(r"[？?]", raw)
                    for p in parts:
                        p = p.strip(" ，,。.、")
                        if p and len(p) > 2:
                            questions.append(p + ("？" if not p.endswith("?") and not p.endswith("？") else ""))
                if questions:
                    break

        return capabilities, questions

    def __len__(self) -> int:
        return len(self._roles)

    def __contains__(self, role_id: str) -> bool:
        return role_id in self._roles
