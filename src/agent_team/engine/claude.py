"""LLM 客户端兼容层

保留 ClaudeClient 旧类名作为向后兼容别名，
新代码应使用 engine.client_factory.create_client() 创建客户端。
"""

# 旧代码通过 ClaudeClient 引用，这里做兼容桥接
from agent_team.engine.anthropic_client import AnthropicClient as ClaudeClient

__all__ = ["ClaudeClient"]