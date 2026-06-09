"""执行模式工作流：PM→PJM→Arch→UX→[BE||FE]→QA→Review→CEO"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from agent_team.config.settings import AgentTeamSettings
from agent_team.engine.base import BaseLLMClient
from agent_team.engine.prompt_builder import build_delegate_prompt, build_system_prompt
from agent_team.engine.tool_executor import ToolExecutor
from agent_team.output.base import OutputRenderer
from agent_team.roles.models import Role
from agent_team.roles.registry import RoleRegistry
from agent_team.workflows.base import WorkflowContext, WorkflowResult

# 执行模式阶段定义
EXECUTE_PHASES: list[dict[str, Any]] = [
    {"id": "pm", "label": "确认需求", "role_ids": ["pm"]},
    {"id": "pjm", "label": "制定排期", "role_ids": ["pjm"]},
    {"id": "architect", "label": "技术方案", "role_ids": ["architect"]},
    {"id": "ux-designer", "label": "交互方案", "role_ids": ["ux-designer"]},
    {"id": "dev", "label": "并行开发", "role_ids": ["backend", "frontend"], "parallel": True},
    {"id": "qa", "label": "测试", "role_ids": ["qa"]},
    {"id": "reviewer", "label": "审查", "role_ids": ["reviewer"]},
    {"id": "ceo", "label": "验收", "role_ids": ["ceo"]},
]


def _get_tools_for_role(role: Role, provider: str) -> list[dict] | None:
    """根据角色权限和 provider 返回工具定义"""
    from agent_team.engine.anthropic_client import ROLE_TOOLS_ANTHROPIC
    from agent_team.engine.openai_compat_client import ROLE_TOOLS_OPENAI

    if provider == "anthropic":
        return ROLE_TOOLS_ANTHROPIC.get(role.permission.value, None)
    else:
        return ROLE_TOOLS_OPENAI.get(role.permission.value, None)


class ExecuteWorkflow:
    """执行模式：带依赖关系的流水线"""

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

    def run(self, requirement: str, role_filter: list[str] | None = None) -> WorkflowResult:
        return asyncio.run(self.run_async(requirement, role_filter))

    async def run_async(self, requirement: str, role_filter: list[str] | None = None) -> WorkflowResult:
        start_time = time.time()
        context = WorkflowContext(requirement=requirement)

        self.renderer.render_header(requirement, "execute", self.client.model_name)
        total_phases = len(EXECUTE_PHASES)
        total_tokens = 0

        for phase_idx, phase in enumerate(EXECUTE_PHASES, 1):
            roles = [self.registry.get(rid) for rid in phase["role_ids"] if rid in self.registry]
            if not roles:
                continue

            task_context = self._build_phase_context(context, phase)

            if phase.get("parallel") and len(roles) > 1:
                outputs = await self._run_parallel(roles, requirement, task_context, phase_idx, total_phases)
                for rid, output in outputs.items():
                    context.role_outputs[rid] = output
            else:
                for role in roles:
                    self.renderer.render_role_start(role, phase_idx, total_phases)
                    task = self._build_task_description(role, requirement, phase)
                    try:
                        output, tokens = await self._call_role_async(
                            role, build_delegate_prompt(role=role, task=task, context=task_context), mode="execute"
                        )
                        context.role_outputs[role.id] = output
                        total_tokens += tokens
                    except Exception as e:
                        self.renderer.render_error(e)
                    self.renderer.render_role_end(role)

        elapsed = time.time() - start_time
        self.renderer.render_completion(elapsed, total_tokens)

        return WorkflowResult(
            requirement=requirement,
            role_outputs=dict(context.role_outputs),
            synthesis="",
            total_tokens=total_tokens,
            elapsed_seconds=elapsed,
            mode="execute",
            errors=[],
        )

    async def _run_parallel(
        self, roles: list[Role], requirement: str, task_context: dict[str, str],
        phase_idx: int, total_phases: int,
    ) -> dict[str, str]:
        results: dict[str, str] = {}

        async def _run_one(role: Role) -> tuple[str, str]:
            self.renderer.render_role_start(role, phase_idx, total_phases)
            task = self._build_task_description(role, requirement, EXECUTE_PHASES[phase_idx - 1])
            try:
                output, _ = await self._call_role_async(
                    role, build_delegate_prompt(role=role, task=task, context=task_context), mode="execute"
                )
                self.renderer.render_role_end(role)
                return role.id, output
            except Exception as e:
                self.renderer.render_error(e)
                self.renderer.render_role_end(role)
                return role.id, f"[错误] {e}"

        tasks = [_run_one(role) for role in roles]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        for result in completed:
            if isinstance(result, Exception):
                continue
            rid, output = result
            results[rid] = output
        return results

    async def _call_role_async(
        self, role: Role, user_message: str, mode: str = "execute"
    ) -> tuple[str, int]:
        """异步调用单个角色"""
        system_prompt = build_system_prompt(role, mode=mode)
        tools = _get_tools_for_role(role, self.provider)

        messages: list[dict] = [{"role": "user", "content": user_message}]
        full_text = ""
        total_tokens = 0

        for _ in range(self.settings.max_tool_iterations):
            text, tool_calls, input_tokens = await self.client.stream_chat_async(
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

            # 执行工具调用
            tool_results = []
            for tc in tool_calls:
                result = await self.tool_executor.execute(tc["name"], tc["input"])
                tool_results.append(str(result))

            result_messages = self.client.build_tool_result_messages(tool_calls, tool_results)
            messages.extend(result_messages)

        return full_text, total_tokens

    def _build_phase_context(self, context: WorkflowContext, phase: dict[str, Any]) -> dict[str, str]:
        ctx: dict[str, str] = {}
        phase_id = phase["id"]

        if phase_id == "pjm" and "pm" in context.role_outputs:
            ctx["产品经理需求确认"] = context.role_outputs["pm"]
        elif phase_id == "architect" and "pm" in context.role_outputs:
            ctx["产品经理需求确认"] = context.role_outputs["pm"]
        elif phase_id == "ux-designer" and "pm" in context.role_outputs:
            ctx["产品经理需求确认"] = context.role_outputs["pm"]
        elif phase_id == "dev":
            if "pm" in context.role_outputs:
                ctx["产品经理需求确认"] = context.role_outputs["pm"]
            if "architect" in context.role_outputs:
                ctx["架构师技术方案"] = context.role_outputs["architect"]
        elif phase_id == "qa":
            if "backend" in context.role_outputs:
                ctx["后端开发产出"] = context.role_outputs["backend"]
            if "frontend" in context.role_outputs:
                ctx["前端开发产出"] = context.role_outputs["frontend"]
        elif phase_id == "reviewer":
            if "backend" in context.role_outputs:
                ctx["后端代码"] = context.role_outputs["backend"]
            if "frontend" in context.role_outputs:
                ctx["前端代码"] = context.role_outputs["frontend"]
        elif phase_id == "ceo":
            for rid, output in context.role_outputs.items():
                try:
                    role = self.registry.get(rid)
                    label = role.name
                except Exception:
                    label = rid
                ctx[label] = self._truncate(output, max_chars=3000)

        return ctx

    def _build_task_description(self, role: Role, requirement: str, phase: dict[str, Any]) -> str:
        task_templates = {
            "pm": f"分析以下需求，输出完整的 PRD（概述→用户故事→MoSCoW 优先级→验收标准→数据指标）：\n\n{requirement}",
            "pjm": "基于产品经理的需求确认，制定项目排期和风险矩阵",
            "architect": "基于产品经理的需求，设计技术架构方案（架构图、模块划分、接口定义、技术选型 trade-off）",
            "ux-designer": "基于产品经理的需求，设计交互方案（信息架构、关键路径、线框描述）",
            "backend": "实现后端代码：API 设计、数据库 schema、核心业务逻辑",
            "frontend": "实现前端代码：组件设计、页面结构、交互逻辑",
            "qa": "基于开发产出，设计测试策略和关键用例",
            "reviewer": "审查开发产出的代码质量、安全性和最佳实践",
            "ceo": "基于所有阶段的产出，做最终验收判断",
        }
        return task_templates.get(role.id, f"从你的角度分析：{requirement}")

    def _truncate(self, text: str, max_chars: int = 3000) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + f"\n\n... (已截断，原文 {len(text)} 字符)"