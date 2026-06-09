"""角色引擎和注册表测试"""

import pytest

from agent_team.roles.models import (
    DEFAULT_ROLE_ORDER,
    PERMISSION_TOOLS,
    PermissionLevel,
    Role,
)
from agent_team.roles.registry import RoleRegistry


class TestPermissionLevel:
    """权限级别测试"""

    def test_read_only(self):
        assert PermissionLevel.READ_ONLY.value == "read_only"

    def test_read_bash(self):
        assert PermissionLevel.READ_BASH.value == "read_bash"

    def test_full(self):
        assert PermissionLevel.FULL.value == "full"

    def test_permission_tools_mapping(self):
        assert PERMISSION_TOOLS[PermissionLevel.READ_ONLY] == []
        assert PERMISSION_TOOLS[PermissionLevel.READ_BASH] == ["bash"]
        assert PERMISSION_TOOLS[PermissionLevel.FULL] == ["bash", "read_file", "write_file"]


class TestRole:
    """Role dataclass 测试"""

    def test_create_role(self):
        role = Role(
            id="test",
            name="测试角色",
            personality="你是一个测试角色",
            permission=PermissionLevel.READ_ONLY,
            capabilities=("分析", "推理"),
            signature_questions=("这是个问题？",),
        )
        assert role.id == "test"
        assert role.name == "测试角色"
        assert role.permission == PermissionLevel.READ_ONLY
        assert not role.has_tools
        assert not role.can_write

    def test_role_output_marker(self):
        role = Role(
            id="ceo",
            name="CEO",
            personality="",
            permission=PermissionLevel.READ_ONLY,
        )
        assert role.output_marker == "## CEO 视角"

    def test_backend_has_write_permission(self):
        role = Role(
            id="backend",
            name="后端工程师",
            personality="",
            permission=PermissionLevel.FULL,
        )
        assert role.has_tools
        assert role.can_write

    def test_role_is_frozen(self):
        role = Role(id="test", name="test", personality="", permission=PermissionLevel.READ_ONLY)
        with pytest.raises(AttributeError):
            role.id = "changed"  # type: ignore


class TestRoleRegistry:
    """RoleRegistry 测试"""

    def test_load_all_roles(self):
        registry = RoleRegistry()
        assert len(registry) == 9

    def test_default_role_order(self):
        registry = RoleRegistry()
        roles = registry.all()
        ids = [r.id for r in roles]
        assert ids == DEFAULT_ROLE_ORDER

    def test_get_specific_role(self):
        registry = RoleRegistry()
        ceo = registry.get("ceo")
        assert ceo.id == "ceo"
        assert ceo.name == "CEO"
        assert ceo.permission == PermissionLevel.READ_ONLY

    def test_get_nonexistent_role_raises(self):
        from agent_team.exceptions import RoleNotFoundError

        registry = RoleRegistry()
        with pytest.raises(RoleNotFoundError):
            registry.get("nonexistent")

    def test_filter_roles(self):
        registry = RoleRegistry()
        filtered = registry.filter(["ceo", "pm", "architect"])
        assert len(filtered) == 3
        assert [r.id for r in filtered] == ["ceo", "pm", "architect"]

    def test_filter_preserves_order(self):
        registry = RoleRegistry()
        filtered = registry.filter(["architect", "ceo"])
        assert [r.id for r in filtered] == ["ceo", "architect"]

    def test_contains(self):
        registry = RoleRegistry()
        assert "ceo" in registry
        assert "nonexistent" not in registry

    def test_role_has_personality(self):
        registry = RoleRegistry()
        ceo = registry.get("ceo")
        assert len(ceo.personality) > 50
        assert "CEO" in ceo.personality

    def test_role_has_capabilities(self):
        registry = RoleRegistry()
        ceo = registry.get("ceo")
        assert len(ceo.capabilities) > 0

    def test_backend_can_write(self):
        registry = RoleRegistry()
        backend = registry.get("backend")
        assert backend.can_write
        assert backend.has_tools

    def test_ceo_read_only(self):
        registry = RoleRegistry()
        ceo = registry.get("ceo")
        assert not ceo.has_tools
        assert not ceo.can_write