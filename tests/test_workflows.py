"""工作流引擎测试"""


from agent_team.config.settings import AgentTeamSettings
from agent_team.roles.registry import RoleRegistry
from agent_team.workflows.analysis import AnalysisWorkflow
from agent_team.workflows.base import WorkflowContext, WorkflowResult
from agent_team.workflows.execute import EXECUTE_PHASES


class TestWorkflowContext:
    """WorkflowContext 测试"""

    def test_create_context(self):
        ctx = WorkflowContext(requirement="测试需求")
        assert ctx.requirement == "测试需求"
        assert ctx.role_outputs == {}
        assert ctx.current_role is None

    def test_update_outputs(self):
        ctx = WorkflowContext(requirement="测试需求")
        ctx.role_outputs["ceo"] = "CEO 分析..."
        assert "ceo" in ctx.role_outputs


class TestWorkflowResult:
    """WorkflowResult 测试"""

    def test_create_result(self):
        result = WorkflowResult(
            requirement="测试",
            role_outputs={"ceo": "分析"},
            synthesis="结论",
            total_tokens=100,
            elapsed_seconds=10.0,
            mode="analysis",
        )
        assert result.mode == "analysis"
        assert len(result.role_outputs) == 1
        assert result.synthesis == "结论"


class TestAnalysisWorkflowTruncation:
    """测试分析模式的输出截断"""

    def _make_workflow(self):
        """创建测试用 workflow"""
        settings = AgentTeamSettings(api_key="test")

        class MockClient:
            @property
            def model_name(self):
                return "test"

        return AnalysisWorkflow(
            client=MockClient(),
            registry=RoleRegistry(),
            renderer=None,  # type: ignore
            settings=settings,
            provider="anthropic",
        )

    def test_truncate_prior_outputs_empty(self):
        workflow = self._make_workflow()
        result = workflow._truncate_prior_outputs({})
        assert result == {}

    def test_truncate_prior_outputs_with_data(self):
        workflow = self._make_workflow()

        role_outputs = {
            "ceo": "CEO 的分析内容" * 100,
            "pm": "PM 的分析内容" * 100,
            "architect": "架构师的分析内容" * 100,
            "backend": "后端的分析内容" * 100,
        }

        result = workflow._truncate_prior_outputs(role_outputs, max_roles=2)
        # 应该只保留最近 2 个角色
        assert len(result) <= 2


class TestExecutePhases:
    """执行模式阶段定义测试"""

    def test_phase_count(self):
        assert len(EXECUTE_PHASES) == 8

    def test_parallel_phase(self):
        dev_phase = EXECUTE_PHASES[4]
        assert dev_phase["id"] == "dev"
        assert dev_phase["parallel"] is True
        assert "backend" in dev_phase["role_ids"]
        assert "frontend" in dev_phase["role_ids"]

    def test_phase_labels(self):
        expected_labels = ["确认需求", "制定排期", "技术方案", "交互方案", "并行开发", "测试", "审查", "验收"]
        actual_labels = [p["label"] for p in EXECUTE_PHASES]
        assert actual_labels == expected_labels