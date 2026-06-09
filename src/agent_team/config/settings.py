"""配置管理：分层配置（CLI > 环境变量 > 配置文件 > 默认值）

支持多个 LLM provider：
- anthropic: Anthropic Claude（默认）
- openai: OpenAI 及兼容 API（DeepSeek、Moonshot、OpenRouter、vLLM 等）
- 自动根据 model 名推断 provider
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent_team.roles.models import DEFAULT_ROLE_ORDER

DEFAULT_CONFIG_DIR = Path.home() / ".agent-team"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_CUSTOM_ROLES_DIR = DEFAULT_CONFIG_DIR / "roles"


class AgentTeamSettings(BaseSettings):
    """Agent Team 配置"""

    model_config = SettingsConfigDict(
        env_prefix="AGENT_TEAM_",
        env_file=".env",
        extra="ignore",
    )

    # ── API 配置 ──────────────────────────────────────────
    # API Key：兼容 ANTHROPIC_API_KEY 和 OPENAI_API_KEY 环境变量
    api_key: str = Field(default="", description="LLM API Key（Anthropic/OpenAI/其他）")
    # 支持 OPENAI_API_KEY 环境变量自动回退
    openai_api_key: str = Field(default="", description="OpenAI API Key（单独指定时使用）")

    # Provider: "anthropic" | "openai" | 空（自动推断）
    provider: str = Field(default="", description="LLM provider: anthropic/openai，空则自动推断")
    model: str = Field(default="claude-sonnet-4-20250514", description="模型 ID")
    base_url: str = Field(default="", description="自定义 API base URL（用于第三方兼容 API）")
    max_tokens: int = Field(default=4096, description="单次调用最大输出 tokens")
    temperature: float = Field(default=0.7, description="采样温度")

    # ── 工作流配置 ────────────────────────────────────────
    default_mode: str = Field(default="analysis", description="默认工作流模式")
    role_order: list[str] = Field(default_factory=lambda: list(DEFAULT_ROLE_ORDER))
    max_tool_iterations: int = Field(default=10, description="最大工具调用轮次")

    # ── 输出配置 ──────────────────────────────────────────
    output_format: str = Field(default="console", description="输出格式: console/json/markdown")
    output_file: Optional[str] = Field(default=None, description="输出文件路径")

    # ── 路径 ──────────────────────────────────────────────
    custom_roles_dir: Optional[Path] = Field(default=None, description="自定义角色目录")

    def effective_api_key(self) -> str:
        """获取有效的 API Key

        优先级: settings.api_key > provider 对应的环境变量
        """
        if self.api_key:
            return self.api_key

        # 根据 provider 在环境变量中查找
        import os
        provider = self.provider.lower() if self.provider else ""

        if provider == "openai" or (not provider and not self.model.startswith("claude")):
            key = os.environ.get("OPENAI_API_KEY", "")
            if key:
                return key

        # 默认 Anthropic
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            return key

        # 最后回退到 openai_api_key（兼容旧配置）
        return self.openai_api_key


def load_config(config_file: Path | None = None, cli_overrides: dict | None = None) -> AgentTeamSettings:
    """加载配置，支持分层覆盖

    优先级: CLI 参数 > 环境变量 > 配置文件 > 默认值
    """
    file_values: dict = {}

    cfg_path = config_file or DEFAULT_CONFIG_FILE
    if cfg_path.is_file():
        with open(cfg_path, encoding="utf-8") as f:
            file_data = yaml.safe_load(f) or {}
            file_values = {k: v for k, v in file_data.items() if v is not None}

    if cli_overrides:
        for k, v in cli_overrides.items():
            if v is not None:
                file_values[k] = v

    return AgentTeamSettings(**file_values)


def init_config() -> Path:
    """创建默认配置文件和目录"""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_CUSTOM_ROLES_DIR.mkdir(parents=True, exist_ok=True)

    if not DEFAULT_CONFIG_FILE.exists():
        content = """\
# Agent Team 配置文件

# ── LLM Provider ────────────────────────────────
# provider: anthropic / openai / (空=自动推断)
# 留空时根据 model 名称自动推断:
#   claude* → Anthropic, gpt* → OpenAI, deepseek* → DeepSeek
# provider: anthropic

# ── API Key ──────────────────────────────────────
# 也可通过环境变量设置:
#   ANTHROPIC_API_KEY (Anthropic)
#   OPENAI_API_KEY    (OpenAI 及兼容)
# api_key: "sk-ant-..."

# ── 模型配置 ─────────────────────────────────────
# model: "claude-sonnet-4-20250514"
# base_url: ""         # 第三方 API 地址（OpenRouter、vLLM 等）
# max_tokens: 4096
# temperature: 0.7

# ── 工作流 ────────────────────────────────────────
# default_mode: analysis
# output_format: console
"""
        DEFAULT_CONFIG_FILE.write_text(content, encoding="utf-8")

    return DEFAULT_CONFIG_FILE