"""分析模式工作流：串行 9 角色 + 综合结论"""

from __future__ import annotations

import time

from agent_team.engine.base import BaseLLMClient
from agent_team.engine.client_factory import create_client
from agent_team.engine.prompt_builder import build_system_prompt, build_synthesis_prompt, build_user_message
from agent_team.engine.tool_executor import ToolExecutor
from agent_team.exceptions import WorkflowError
from agent_team.output.base import OutputRenderer
from agent_team.roles.models import DEFAULT_ROLE_ORDER, Role
from agent_team.roles.registry import RoleRegistry
from agent_team.config.settings import AgentTeamSettings
from agent_team.workflows.base import WorkflowContext, WorkflowResult


def _get_tools_for_role(role: Role, provider: str) -> list[dict] | None:
    """根据角色权限和 provider 返回工具定义"""
    from agent_team.engine.anthropic_client import ROLE_TOOLS_ANTHROPIC
    from agent_team.engine.openai_compat_client import ROLE_TOOLS_OPENAI

    if provider == "anthropic":
        return ROLE_TOOLS_ANTHROPIC.get(role.permission.value, None)
    else:
        return ROLE_TOOLS_OPENAI.get(role.permission.value, None)


class AnalysisWorkflow:
    """分析模式：按顺序调用各角色分析，最后生成综合结论

    流程:
    1. 遍历角色序列
    2. 每个角色收到：原始需求 + 前序角色输出摘要
    3. 流式输出每个角色分析
    4. 最后综合所有输出生成结论
    """

    def __init__(
        self,
        client: BaseLLMClient,
        registry: RoleRegistry,
        renderer: OutputRenderer,
        settings: AgentTeamSettings,
        tool_executor: ToolExecutor | None = None,
        provider: str = "anthropic",
    ):
        self.client = client
        self.registry = registry
        self.renderer = renderer
        self.settings = settings
        self.tool_executor = tool_executor or ToolExecutor()
        self.provider = provider

    def run(
        self,
        requirement: str,
        role_filter: list[str] | None = None,
    ) -> WorkflowResult:
        """执行分析模式工作流"""
        start_time = time.time()
        context = WorkflowContext(requirement=requirement)

        if role_filter:
            roles = self.registry.filter(role_filter)
            if not roles:
                available = ", ".join(self.registry.ids())
                raise WorkflowError(f"没有匹配的角色。可用角色: {available}")
        else:
            roles = self.registry.all()

        total = len(roles)
        self.renderer.render_header(requirement, "analysis", self.client.model_name)

        for i, role in enumerate(roles, 1):
            context.current_role = role.id
            self.renderer.render_role_start(role, i, total)

            try:
                prior = self._truncate_prior_outputs(context.role_outputs, max_roles=3)
                output, tokens = self._call_role(role, requirement, prior if prior else None, mode="analysis")
                context.role_outputs[role.id] = output
                context.metadata[f"{role.id}_tokens"] = tokens
            except Exception as e:
                context.metadata[f"{role.id}_error"] = str(e)
                self.renderer.render_error(e)

            self.renderer.render_role_end(role)

        # 综合结论
        synthesis = ""
        synthesis_tokens = 0
        if len(context.role_outputs) >= 2:
            try:
                synthesis, synthesis_tokens = self._call_synthesis(context.role_outputs, requirement)
                self.renderer.render_synthesis(synthesis)
            except Exception as e:
                self.renderer.render_error(e)

        elapsed = time.time() - start_time
        total_tokens = sum(v for k, v in context.metadata.items() if k.endswith("_tokens")) + synthesis_tokens
        self.renderer.render_completion(elapsed, total_tokens)

        return WorkflowResult(
            requirement=requirement,
            role_outputs=dict(context.role_outputs),
            synthesis=synthesis,
            total_tokens=total_tokens,
            elapsed_seconds=elapsed,
            mode="analysis",
            errors=[v for k, v in context.metadata.items() if k.endswith("_error")],
        )

    def _call_role(
        self,
        role: Role,
        requirement: str,
        prior_outputs: dict[str, str] | None,
        mode: str = "analysis",
    ) -> tuple[str, int]:
        """调用单个角色（含工具调用循环）"""
        system_prompt = build_system_prompt(role, mode=mode)
        user_message = build_user_message(requirement=requirement, prior_outputs=prior_outputs, role_name=role.name)
        tools = _get_tools_for_role(role, self.provider)

        messages: list[dict] = [{"role": "user", "content": user_message}]
        full_text = ""
        total_tokens = 0

        for _ in range(self.settings.max_tool_iterations):
            text, tool_calls, input_tokens = self.client.stream_chat(
                system=system_prompt,
                messages=messages,
                tools=tools,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
                on_chunk=self.renderer.render_role_chunk,
            )
            full_text += text
            total_tokens += input_tokens

            if not tool_calls:
                break

            # 工具调用循环
            tool_results = []
            for tc in tool_calls:
                result = self._run_tool(tc["name"], tc["input"])
                tool_results.append(result)

            # 追加工具调用结果到消息
            result_messages = self.client.build_tool_result_messages(tool_calls, tool_results)
            messages.append({"role": "assistant", "content": text} if not tool_calls else messages[-1])
            messages.extend(result_messages)

        return full_text, total_tokens

    def _call_synthesis(self, all_outputs: dict[str, str], requirement: str) -> tuple[str, int]:
        """生成综合结论"""
        system_prompt = build_synthesis_prompt()
        user_parts = [f"## 需求\n{requirement}\n\n## 各角色分析"]
        for role_id, output in all_outputs.items():
            user_parts.append(output)
            user_parts.append("")
        user_message = "\n".join(user_parts)

        text, _, input_tokens = self.client.stream_chat(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            on_chunk=self.renderer.render_role_chunk,
        )
        return text, input_tokens

    def _run_tool(self, name: str, inputs: dict) -> str:
        """执行工具调用（同步封装）"""
        import asyncio

        try:
            return asyncio.run(self.tool_executor.execute(name, inputs))
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.tool_executor.execute(name, inputs))
                return future.result()
        except Exception as e:
            return f"[工具执行错误] {e}"

    def _truncate_prior_outputs(
        self,
        role_outputs: dict[str, str],
        max_roles: int = 3,
        max_chars: int = 15000,
    ) -> dict[str, str]:
        """截断前序输出避免 context 过长"""
        if not role_outputs:
            return {}

        recent_ids = [rid for rid in DEFAULT_ROLE_ORDER if rid in role_outputs][-max_roles:]
        per_role_limit = max_chars // max(len(recent_ids), 1)

        result = {}
        for rid in recent_ids:
            text = role_outputs[rid]
            if len(text) > per_role_limit:
                text = text[:per_role_limit] + f"\n\n... (已截断，原文 {len(text)} 字符)"
            result[rid] = text
        return result