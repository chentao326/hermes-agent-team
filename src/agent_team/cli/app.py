"""Agent Team CLI 入口"""

from __future__ import annotations

import json

import typer
from rich.console import Console

from agent_team.config.settings import AgentTeamSettings, load_config

app = typer.Typer(
    name="agent-team",
    help="9人虚拟技术团队 CLI Agent - 多角色协作分析，支持 Anthropic/OpenAI/DeepSeek/自定义 API",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def _get_settings(
    api_key: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    base_url: str | None = None,
    output: str | None = None,
    output_file: str | None = None,
) -> AgentTeamSettings:
    """从 CLI 参数加载配置"""
    overrides: dict = {}
    if api_key:
        overrides["api_key"] = api_key
    if model:
        overrides["model"] = model
    if provider:
        overrides["provider"] = provider
    if base_url:
        overrides["base_url"] = base_url
    if output:
        overrides["output_format"] = output
    if output_file:
        overrides["output_file"] = output_file
    return load_config(cli_overrides=overrides if overrides else None)


def _create_client(settings: AgentTeamSettings):
    """创建 LLM 客户端"""
    from agent_team.engine.client_factory import create_client

    api_key = settings.effective_api_key()
    if api_key != settings.api_key:
        # 用了环境变量回退，更新 settings 的 api_key
        settings.api_key = api_key

    return create_client(settings)


# ─── config 子命令 ────────────────────────────────────────

config_app = typer.Typer(help="配置管理", no_args_is_help=True)
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show(
    api_key: str | None = typer.Option(None, "--api-key", help="API Key"),
    model: str | None = typer.Option(None, "--model", help="模型 ID"),
    provider: str | None = typer.Option(None, "--provider", help="LLM provider: anthropic/openai"),
    base_url: str | None = typer.Option(None, "--base-url", help="自定义 API base URL"),
) -> None:
    """显示当前配置"""
    settings = _get_settings(api_key=api_key, model=model, provider=provider, base_url=base_url)
    effective_key = settings.effective_api_key()
    provider_display = settings.provider or "(自动推断)"

    console.print("[bold]Agent Team 配置[/bold]\n")
    console.print(f"  Provider:   {provider_display}")
    console.print(f"  API Key:    {'***' + effective_key[-4:] if len(effective_key) > 4 else '(未设置)'}")
    console.print(f"  模型:       {settings.model}")
    console.print(f"  Base URL:   {settings.base_url or '(默认)'}")
    console.print(f"  最大 tokens: {settings.max_tokens}")
    console.print(f"  温度:       {settings.temperature}")
    console.print(f"  默认模式:   {settings.default_mode}")
    console.print(f"  输出格式:   {settings.output_format}")


@config_app.command("init")
def config_init() -> None:
    """创建默认配置文件 (~/.agent-team/config.yaml)"""
    from agent_team.config.settings import init_config as _init_config

    path = _init_config()
    console.print(f"[bold green]✓[/bold green] 配置文件已创建: {path}")
    console.print("\n[dim]请编辑配置文件设置 API Key:[/]")
    console.print(f"  {path}")


# ─── providers 子命令 ─────────────────────────────────────


@app.command("providers")
def list_providers() -> None:
    """列出所有支持的 LLM provider"""
    from agent_team.engine.client_factory import PROVIDER_PRESETS

    console.print("[bold]支持的 LLM Provider[/bold]\n")
    console.print("  [cyan]名称[/cyan]          [cyan]类型[/cyan]       [cyan]默认 Base URL[/cyan]")
    console.print("  " + "─" * 70)
    for name, preset in PROVIDER_PRESETS.items():
        ptype = preset["provider"].upper() if preset["provider"] == "anthropic" else "OpenAI兼容"
        url = preset.get("base_url", "")
        console.print(f"  {name:15s} {ptype:12s} {url}")


# ─── roles 子命令 ─────────────────────────────────────────


@app.command("roles")
def roles_list() -> None:
    """列出所有可用角色"""
    from agent_team.roles.registry import RoleRegistry

    registry = RoleRegistry()
    console.print("[bold]可用角色[/bold]\n")
    for role in registry.all():
        perm_label = {"read_only": "只读", "read_bash": "只读+Bash", "full": "完整读写"}[role.permission.value]
        caps = "、".join(role.capabilities[:3]) if role.capabilities else ""
        console.print(f"  [cyan]{role.id:12s}[/cyan] {role.name:8s}  权限={perm_label:8s}  能力={caps}")


# ─── ask 子命令 ───────────────────────────────────────────


@app.command("ask")
def ask(
    role_id: str = typer.Argument(..., help="角色 ID (ceo/pm/pjm/architect/backend/frontend/ux-designer/qa/reviewer)"),
    question: str = typer.Argument(..., help="问题内容"),
    api_key: str | None = typer.Option(None, "--api-key", help="API Key"),
    model: str | None = typer.Option(None, "--model", help="模型 ID"),
    provider: str | None = typer.Option(None, "--provider", help="LLM provider: anthropic/openai"),
    base_url: str | None = typer.Option(None, "--base-url", help="自定义 API base URL"),
    no_stream: bool = typer.Option(False, "--no-stream", help="禁用流式输出"),
) -> None:
    """向指定角色提问"""
    from agent_team.output.console import ConsoleRenderer
    from agent_team.roles.registry import RoleRegistry

    settings = _get_settings(api_key=api_key, model=model, provider=provider, base_url=base_url)

    effective_key = settings.effective_api_key()
    if not effective_key:
        console.print("[bold red]错误:[/bold red] 未设置 API Key。请设置环境变量或运行 agent-team config init")
        console.print("  环境变量: [dim]ANTHROPIC_API_KEY[/dim] 或 [dim]OPENAI_API_KEY[/dim]")
        raise typer.Exit(1) from None

    registry = RoleRegistry()
    try:
        role = registry.get(role_id)
    except Exception as e:
        console.print(f"[bold red]错误:[/bold red] {e}")
        raise typer.Exit(1) from None

    renderer = ConsoleRenderer()
    client = _create_client(settings)

    provider_label = settings.provider or "auto"
    client_model = client.model_name
    console.print(f"\n  [bold]{role.name}[/bold] 正在分析... (provider: {provider_label}, model: {client_model})\n")
    console.print("  " + "─" * 50, style="dim")

    try:
        from agent_team.engine.prompt_builder import build_system_prompt, build_user_message

        system_prompt = build_system_prompt(role, mode="analysis")
        user_message = build_user_message(requirement=question, role_name=role.name)

        text, tool_calls, tokens = client.stream_chat(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            on_chunk=renderer.render_role_chunk if not no_stream else None,
        )

        console.print("\n  " + "─" * 50, style="dim")

    except Exception as e:
        console.print(f"\n  [bold red]✗ 错误:[/bold red] {e}")
        raise typer.Exit(1) from None


# ─── run 子命令 ───────────────────────────────────────────


@app.command("run")
def run(
    requirement: str = typer.Argument(..., help="需求描述"),
    mode: str = typer.Option("analysis", "--mode", "-m", help="工作流模式: analysis/execute"),
    roles: str | None = typer.Option(None, "--roles", "-r", help="角色过滤，逗号分隔 (如 ceo,pm,architect)"),
    api_key: str | None = typer.Option(None, "--api-key", help="API Key"),
    model: str | None = typer.Option(None, "--model", help="模型 ID"),
    provider: str | None = typer.Option(None, "--provider", help="LLM provider: anthropic/openai"),
    base_url: str | None = typer.Option(None, "--base-url", help="自定义 API base URL"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出格式: console/json/markdown"),
    output_file: str | None = typer.Option(None, "--output-file", "-f", help="输出文件路径"),
) -> None:
    """运行团队工作流（分析模式或执行模式）"""
    import pathlib

    from agent_team.engine.tool_executor import ToolExecutor
    from agent_team.output.console import ConsoleRenderer
    from agent_team.roles.registry import RoleRegistry
    from agent_team.workflows.analysis import AnalysisWorkflow
    from agent_team.workflows.execute import ExecuteWorkflow

    # 加载配置
    settings = _get_settings(
        api_key=api_key, model=model, provider=provider, base_url=base_url, output=output, output_file=output_file
    )

    effective_key = settings.effective_api_key()
    if not effective_key:
        console.print("[bold red]错误:[/bold red] 未设置 API Key。请设置环境变量或运行 agent-team config init")
        console.print("  环境变量: [dim]ANTHROPIC_API_KEY[/dim] 或 [dim]OPENAI_API_KEY[/dim]")
        raise typer.Exit(1)

    # 解析角色过滤
    role_filter = None
    if roles:
        role_filter = [r.strip() for r in roles.split(",")]

    # 创建客户端和工作流
    registry = RoleRegistry()
    renderer = ConsoleRenderer()
    client = _create_client(settings)
    tool_executor = ToolExecutor()

    # 确定 provider 字符串（用于选择工具格式）

    from agent_team.engine.anthropic_client import AnthropicClient
    is_anthropic = isinstance(client, AnthropicClient)
    provider_str = "anthropic" if is_anthropic else "openai"

    if mode == "execute":
        workflow = ExecuteWorkflow(client, registry, renderer, settings, tool_executor, provider=provider_str)
    else:
        workflow = AnalysisWorkflow(client, registry, renderer, settings, tool_executor, provider=provider_str)

    # 执行
    try:
        result = workflow.run(requirement=requirement, role_filter=role_filter)
    except Exception as e:
        console.print(f"\n  [bold red]✗ 工作流错误:[/bold red] {e}")
        raise typer.Exit(1) from None

    # 额外输出格式
    if settings.output_format == "json":
        output_data = {
            "requirement": result.requirement,
            "mode": result.mode,
            "roles": result.role_outputs,
            "synthesis": result.synthesis,
            "total_tokens": result.total_tokens,
            "elapsed_seconds": result.elapsed_seconds,
        }
        if output_file:
            out_path = pathlib.Path(output_file)
            out_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
            console.print(f"\n  [green]✓[/green] JSON 已写入: {output_file}")
        else:
            console.print(json.dumps(output_data, ensure_ascii=False, indent=2))

    elif settings.output_format == "markdown":
        lines = [f"# Agent Team - {result.mode}模式报告\n"]
        lines.append(f"## 需求\n{result.requirement}\n")
        for rid, output_text in result.role_outputs.items():
            try:
                role_obj = registry.get(rid)
                name = role_obj.name
            except Exception:
                name = rid
            lines.append(f"## {name}\n{output_text}\n")
        if result.synthesis:
            lines.append(f"## 综合结论\n{result.synthesis}\n")
        lines.append(f"\n---\n耗时: {result.elapsed_seconds:.1f}s | tokens: {result.total_tokens:,}")

        md_content = "\n".join(lines)
        if output_file:
            pathlib.Path(output_file).write_text(md_content, encoding="utf-8")
            console.print(f"\n  [green]✓[/green] Markdown 已写入: {output_file}")
        else:
            console.print(md_content)