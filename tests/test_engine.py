"""引擎模块测试"""


from agent_team.engine.prompt_builder import (
    build_delegate_prompt,
    build_synthesis_prompt,
    build_system_prompt,
    build_user_message,
)
from agent_team.engine.tool_executor import is_read_only_command
from agent_team.roles.registry import RoleRegistry


class TestPromptBuilder:
    """Prompt 组装测试"""

    def test_build_system_prompt_analysis(self):
        registry = RoleRegistry()
        ceo = registry.get("ceo")
        prompt = build_system_prompt(ceo, mode="analysis")

        assert "CEO" in prompt
        assert "分析" in prompt
        assert "不要写代码" in prompt

    def test_build_system_prompt_execute(self):
        registry = RoleRegistry()
        backend = registry.get("backend")
        prompt = build_system_prompt(backend, mode="execute")

        assert "后端工程师" in prompt
        assert "开发流程" in prompt

    def test_build_user_message_simple(self):
        msg = build_user_message("做一个博客系统")
        assert "做一个博客系统" in msg

    def test_build_user_message_with_context(self):
        msg = build_user_message(
            "做一个博客系统",
            prior_outputs={"ceo": "CEO 认为..."},
            role_name="产品经理",
        )
        assert "已有分析" in msg
        assert "产品经理" in msg

    def test_build_delegate_prompt(self):
        registry = RoleRegistry()
        ceo = registry.get("ceo")
        prompt = build_delegate_prompt(
            role=ceo,
            task="评估这个项目的商业价值",
        )
        assert "你是一名CEO" in prompt
        assert "任务" in prompt

    def test_build_delegate_prompt_with_context(self):
        registry = RoleRegistry()
        pjm = registry.get("pjm")
        prompt = build_delegate_prompt(
            role=pjm,
            task="制定项目排期",
            context={"PM需求确认": "需要做XX功能"},
        )
        assert "上下文" in prompt
        assert "PM需求确认" in prompt

    def test_build_synthesis_prompt(self):
        prompt = build_synthesis_prompt()
        assert "综合结论" in prompt
        assert "核心决策" in prompt


class TestToolExecutor:
    """工具执行器测试"""

    def test_is_read_only_command(self):
        assert is_read_only_command("ls -la") is True
        assert is_read_only_command("cat file.txt") is True
        assert is_read_only_command("git log --oneline") is True
        assert is_read_only_command("git diff") is True
        assert is_read_only_command("grep pattern file") is True

    def test_is_not_read_only_command(self):
        assert is_read_only_command("rm -rf /") is False
        assert is_read_only_command("pip install package") is False
        assert is_read_only_command("npm run build") is False

    def test_empty_command(self):
        assert is_read_only_command("") is True
        assert is_read_only_command("   ") is True


class TestConfigSettings:
    """配置测试"""

    def test_default_settings(self):
        from agent_team.config.settings import AgentTeamSettings

        settings = AgentTeamSettings(api_key="test-key")
        assert settings.model == "claude-sonnet-4-20250514"
        assert settings.default_mode == "analysis"
        assert settings.max_tokens == 4096
        assert settings.temperature == 0.7

    def test_settings_override(self):
        from agent_team.config.settings import AgentTeamSettings

        settings = AgentTeamSettings(api_key="test", model="claude-opus-4-20250514")
        assert settings.model == "claude-opus-4-20250514"

    def test_provider_and_base_url(self):
        from agent_team.config.settings import AgentTeamSettings

        settings = AgentTeamSettings(api_key="test", provider="openai", base_url="https://api.deepseek.com/v1")
        assert settings.provider == "openai"
        assert settings.base_url == "https://api.deepseek.com/v1"


class TestClientFactory:
    """客户端工厂和 Provider 推断测试"""

    def test_auto_infer_claude(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.anthropic_client import AnthropicClient
        from agent_team.engine.client_factory import create_client

        settings = AgentTeamSettings(api_key="test", model="claude-sonnet-4-20250514")
        client = create_client(settings)
        assert isinstance(client, AnthropicClient)
        assert client.model_name == "claude-sonnet-4-20250514"

    def test_auto_infer_gpt(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.client_factory import create_client
        from agent_team.engine.openai_compat_client import OpenAICompatClient

        settings = AgentTeamSettings(api_key="test", model="gpt-4o")
        client = create_client(settings)
        assert isinstance(client, OpenAICompatClient)

    def test_auto_infer_deepseek(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.client_factory import create_client
        from agent_team.engine.openai_compat_client import OpenAICompatClient

        settings = AgentTeamSettings(api_key="test", model="deepseek-chat")
        client = create_client(settings)
        assert isinstance(client, OpenAICompatClient)

    def test_auto_infer_glm(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.client_factory import create_client
        from agent_team.engine.openai_compat_client import OpenAICompatClient

        settings = AgentTeamSettings(api_key="test", model="glm-4")
        client = create_client(settings)
        assert isinstance(client, OpenAICompatClient)

    def test_explicit_provider_anthropic(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.anthropic_client import AnthropicClient
        from agent_team.engine.client_factory import create_client

        settings = AgentTeamSettings(api_key="test", provider="anthropic", model="claude-3-5-sonnet-20241022")
        client = create_client(settings)
        assert isinstance(client, AnthropicClient)

    def test_explicit_provider_openai(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.client_factory import create_client
        from agent_team.engine.openai_compat_client import OpenAICompatClient

        settings = AgentTeamSettings(api_key="test", provider="openai", model="gpt-4o")
        client = create_client(settings)
        assert isinstance(client, OpenAICompatClient)

    def test_custom_base_url(self):
        from agent_team.config.settings import AgentTeamSettings
        from agent_team.engine.client_factory import create_client
        from agent_team.engine.openai_compat_client import OpenAICompatClient

        settings = AgentTeamSettings(
            api_key="test",
            model="my-model",
            base_url="https://custom-llm.example.com/v1",
        )
        client = create_client(settings)
        assert isinstance(client, OpenAICompatClient)

    def test_effective_api_key_env(self):
        import os

        from agent_team.config.settings import AgentTeamSettings

        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
        try:
            settings = AgentTeamSettings(model="claude-sonnet-4-20250514")
            assert settings.effective_api_key() == "sk-ant-test-key"
        finally:
            del os.environ["ANTHROPIC_API_KEY"]

    def test_effective_api_key_openai_env(self):
        import os

        from agent_team.config.settings import AgentTeamSettings

        os.environ["OPENAI_API_KEY"] = "sk-openai-test-key"
        try:
            settings = AgentTeamSettings(api_key="", model="gpt-4o")
            assert settings.effective_api_key() == "sk-openai-test-key"
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_provider_presets(self):
        from agent_team.engine.client_factory import PROVIDER_PRESETS

        assert "anthropic" in PROVIDER_PRESETS
        assert "openai" in PROVIDER_PRESETS
        assert "deepseek" in PROVIDER_PRESETS
        assert "moonshot" in PROVIDER_PRESETS
        assert "zhipu" in PROVIDER_PRESETS
        assert "openrouter" in PROVIDER_PRESETS