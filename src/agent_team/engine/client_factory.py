"""LLM 客户端工厂：根据配置自动选择 provider"""

from __future__ import annotations

from agent_team.config.settings import AgentTeamSettings
from agent_team.engine.base import BaseLLMClient
from agent_team.engine.anthropic_client import AnthropicClient
from agent_team.engine.openai_compat_client import OpenAICompatClient
from agent_team.exceptions import ConfigError

# 已知 provider 映射
PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    # Anthropic 系列
    "anthropic": {"provider": "anthropic", "base_url": "https://api.anthropic.com"},
    "claude": {"provider": "anthropic", "base_url": "https://api.anthropic.com"},
    # OpenAI 系列
    "openai": {"provider": "openai", "base_url": "https://api.openai.com/v1"},
    "gpt": {"provider": "openai", "base_url": "https://api.openai.com/v1"},
    # DeepSeek
    "deepseek": {"provider": "openai", "base_url": "https://api.deepseek.com/v1"},
    # 月之暗面
    "moonshot": {"provider": "openai", "base_url": "https://api.moonshot.cn/v1"},
    # 智谱
    "zhipu": {"provider": "openai", "base_url": "https://open.bigmodel.cn/api/paas/v4"},
    # OpenRouter
    "openrouter": {"provider": "openai", "base_url": "https://openrouter.ai/api/v1"},
    # SiliconFlow
    "siliconflow": {"provider": "openai", "base_url": "https://api.siliconflow.cn/v1"},
}


def create_client(settings: AgentTeamSettings) -> BaseLLMClient:
    """根据配置创建 LLM 客户端

    优先级：
    1. settings.provider 显式指定
    2. 根据 settings.model 名称自动推断
    """
    provider = settings.provider
    model = settings.model
    api_key = settings.api_key
    base_url = settings.base_url
    max_tokens = settings.max_tokens
    temperature = settings.temperature

    # 如果显式指定了 provider，就用它
    if provider:
        return _create_by_provider(provider, api_key, model, base_url, max_tokens, temperature)

    # 否则根据 model 名称自动推断
    return _infer_and_create(api_key, model, base_url, max_tokens, temperature)


def _create_by_provider(
    provider: str,
    api_key: str,
    model: str,
    base_url: str | None,
    max_tokens: int,
    temperature: float,
) -> BaseLLMClient:
    provider_lower = provider.lower()

    if provider_lower == "anthropic":
        return AnthropicClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    elif provider_lower == "openai":
        return OpenAICompatClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        # 尝试作为 OpenAI 兼容处理
        if not base_url:
            raise ConfigError(
                f"未知 provider: {provider}。请同时指定 --base-url 或使用以下之一: "
                f"{', '.join(PROVIDER_PRESETS.keys())}"
            )
        return OpenAICompatClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )


def _infer_and_create(
    api_key: str,
    model: str,
    base_url: str | None,
    max_tokens: int,
    temperature: float,
) -> BaseLLMClient:
    """根据 model 名称推断 provider"""
    model_lower = model.lower()

    # Anthropic 模型前缀
    if any(model_lower.startswith(p) for p in ("claude", "anthropic")):
        return AnthropicClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # OpenAI 模型前缀
    if any(model_lower.startswith(p) for p in ("gpt-", "o1-", "o3-", "o4-", "chatgpt")):
        default_url = base_url or "https://api.openai.com/v1"
        return OpenAICompatClient(
            api_key=api_key,
            model=model,
            base_url=default_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # DeepSeek 模型前缀
    if model_lower.startswith("deepseek"):
        default_url = base_url or "https://api.deepseek.com/v1"
        return OpenAICompatClient(
            api_key=api_key,
            model=model,
            base_url=default_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # GLM 模型前缀
    if model_lower.startswith("glm"):
        default_url = base_url or "https://open.bigmodel.cn/api/paas/v4"
        return OpenAICompatClient(
            api_key=api_key,
            model=model,
            base_url=default_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # 默认：当作 OpenAI 兼容（需要 base_url）
    if base_url:
        return OpenAICompatClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # 无法推断且无 base_url，默认走 Anthropic
    return AnthropicClient(
        api_key=api_key,
        model=model,
        base_url=base_url,
        max_tokens=max_tokens,
        temperature=temperature,
    )