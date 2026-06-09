"""System prompt 组装器"""

from __future__ import annotations

from agent_team.roles.models import Role


def build_system_prompt(
    role: Role,
    mode: str = "analysis",
) -> str:
    """为指定角色组装 system prompt

    Args:
        role: 角色定义
        mode: 工作流模式 ("analysis" 或 "execute")

    Returns:
        完整的 system prompt 字符串
    """
    parts: list[str] = []

    # Part 1: 角色人格（Markdown 全文）
    parts.append(role.personality.strip())

    # Part 2: 模式约束
    if mode == "analysis":
        parts.append(
            "\n## 工作模式\n"
            "你正在参与一个多角色团队分析。请从你的专业角度分析需求，输出结构化分析。\n"
            "不要写代码。只输出分析、方案、建议。"
        )
    else:  # execute
        parts.append(
            "\n## 工作模式\n"
            "你正在参与团队开发流程。请按照你的角色职责执行任务，可以给出具体方案和代码。"
        )

    # Part 3: 输出格式
    parts.append(
        f"\n## 输出格式\n"
        f"以 `{role.output_marker}` 为标题开始输出。\n"
        f"包含以下部分：\n"
        f"- **核心判断**: 一句话总结你的核心观点\n"
        f"- **关键问题**: 列出需要关注的 2-3 个关键问题\n"
        f"- **具体建议**: 给出可操作的建议列表"
    )

    # Part 4: 全局规则
    parts.append(
        "\n## 规则\n"
        "- 所有输出使用中文\n"
        "- 分析要体现你的角色独特视角，与其他角色形成差异\n"
        "- 有不确定的判断时标注置信度\n"
        "- 与前序角色意见冲突时明确标注 trade-off"
    )

    return "\n".join(parts)


def build_synthesis_prompt() -> str:
    """为综合结论生成 system prompt"""
    return (
        "你是一位项目协调者，负责汇总团队各角色的分析结果，生成综合结论。\n\n"
        "## 输出格式\n"
        "## 综合结论\n\n"
        "包含以下部分：\n"
        "- **核心决策**: 团队达成的共识\n"
        "- **优先级**: P0（必须做）/ P1（应该做）/ P2（可以做）\n"
        "- **风险点**: 列出主要风险和应对建议\n"
        "- **角色分歧**: 不同角色之间的 trade-off（如有）\n"
        "- **下一步**: 具体的行动项和时间线\n\n"
        "## 规则\n"
        "- 所有输出使用中文\n"
        "- 综合各角色的分析，不要偏向某一个角色\n"
        "- 保持客观中立，冲突观点要如实反映"
    )


def build_user_message(
    requirement: str,
    prior_outputs: dict[str, str] | None = None,
    role_name: str | None = None,
) -> str:
    """组装用户消息（需求 + 前序输出上下文）

    Args:
        requirement: 用户需求
        prior_outputs: 前序角色的输出 {role_id: output_text}
        role_name: 当前角色名（用于提示）
    """
    parts: list[str] = []

    if prior_outputs:
        parts.append("## 已有分析（供参考，请在此基础上补充你的专业视角）\n")
        for output_text in prior_outputs.values():
            parts.append(output_text)
            parts.append("\n---\n")
        parts.append("")

    if role_name:
        parts.append(f"现在请从**{role_name}**的角度分析以下需求：\n")

    parts.append(f"## 需求\n{requirement}")

    return "\n".join(parts)


def build_delegate_prompt(
    role: Role,
    task: str,
    context: dict[str, str] | None = None,
) -> str:
    """构建 delegate_task 格式的 prompt（执行模式用）

    按照 SKILL.md 定义的模板：
    你是一名[角色名]：[角色核心能力一句话]。
    执行以下任务时遵循该角色的专业标准和关注点：
    - [具体关注点]
    任务：[具体任务描述]
    """
    parts: list[str] = []

    # 角色身份
    cap_str = "、".join(role.capabilities[:3]) if role.capabilities else "专业分析"
    parts.append(f"你是一名{role.name}：{cap_str}。\n")

    # 关注点（从标志性问题提取）
    if role.signature_questions:
        parts.append("执行以下任务时遵循该角色的专业标准和关注点：")
        for q in role.signature_questions[:3]:
            parts.append(f"- {q}")
        parts.append("")

    # 上下文
    if context:
        parts.append("## 上下文\n")
        for label, text in context.items():
            parts.append(f"### {label}\n{text}\n")

    # 任务
    parts.append(f"## 任务\n{task}")

    return "\n".join(parts)
