"""Agent Team 自定义异常层级"""


class AgentTeamError(Exception):
    """基础异常"""

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class ConfigError(AgentTeamError):
    """配置错误：缺少 API key、无效配置等"""


class RoleNotFoundError(AgentTeamError):
    """角色未找到"""


class ClaudeAPIError(AgentTeamError):
    """Claude API 调用失败"""

    def __init__(self, message: str, detail: str = "", status_code: int = 0):
        super().__init__(message, detail)
        self.status_code = status_code


class RateLimitError(ClaudeAPIError):
    """API 限流"""


class AuthenticationError(ClaudeAPIError):
    """API 认证失败"""


class ToolExecutionError(AgentTeamError):
    """工具执行失败"""


class WorkflowError(AgentTeamError):
    """工作流级别错误"""
