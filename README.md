# Agent Team

9 人虚拟技术团队 —— 多角色协作 CLI Agent，支持 **Anthropic / OpenAI / DeepSeek / OpenRouter** 等任意 LLM Provider。

```
CEO → PM → 项目经理 → 架构师 → 后端 ←→ 前端 → UX设计师 → 测试 → 审查
```

## 快速开始

```bash
# 安装
git clone https://github.com/chentao326/hermes-agent-team.git
cd hermes-agent-team
uv sync

# 设置 API Key
export ANTHROPIC_API_KEY=sk-ant-...

# 全流程分析（9 角色串行）
uv run agent-team run "做一个 AI 客服 SaaS"

# 单角色提问
uv run agent-team ask architect "这个方案在100倍流量下会怎样？"
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `run <需求>` | 全流程分析（默认分析模式，9 角色串行） |
| `run --mode execute <需求>` | 执行模式（流水线编排+前后端并行开发） |
| `run --roles ceo,pm <需求>` | 只调用指定角色 |
| `ask <角色> <问题>` | 快速单角色提问 |
| `roles` | 列出所有角色和权限 |
| `providers` | 列出所有支持的 LLM Provider |
| `config show` | 显示当前配置 |
| `config init` | 创建默认配置文件 |

全局选项：`--api-key`、`--model`、`--provider`、`--base-url`、`--output`、`--output-file`

## 多 Provider 支持

| Provider | 自动推断 | 默认 Base URL |
|----------|----------|---------------|
| Anthropic Claude | `claude-*` | https://api.anthropic.com |
| OpenAI GPT | `gpt-*`, `o1-*`, `o3-*` | https://api.openai.com/v1 |
| DeepSeek | `deepseek-*` | https://api.deepseek.com/v1 |
| 智谱 GLM | `glm-*` | https://open.bigmodel.cn/api/paas/v4 |
| 月之暗面 Moonshot | — | https://api.moonshot.cn/v1 |
| OpenRouter | — | https://openrouter.ai/api/v1 |
| SiliconFlow | — | https://api.siliconflow.cn/v1 |
| 其他 OpenAI 兼容 | 需指定 --base-url | 自定义 |

### 使用示例

```bash
# Anthropic（默认，自动推断）
agent-team run "需求"

# OpenAI
agent-team run --model gpt-4o --provider openai "需求"

# DeepSeek（自动推断）
agent-team run --model deepseek-chat "需求"

# OpenRouter（指定 provider + base-url）
agent-team run --provider openai --base-url https://openrouter.ai/api/v1 --model anthropic/claude-3.5-sonnet "需求"

# 本地 vLLM / Ollama
agent-team run --provider openai --base-url http://localhost:8000/v1 --model qwen2-7b "需求"
```

API Key 优先级：CLI `--api-key` > 配置文件 > `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` 环境变量

## 安装方式

### 方式一：本地运行

```bash
git clone https://github.com/chentao326/hermes-agent-team.git
cd hermes-agent-team
uv sync
uv run agent-team --help
```

### 方式二：PyPI 安装（发布后）

```bash
pip install agent-team
# 或
uv tool install agent-team
```

## 工作流模式

### 分析模式（默认）

9 个角色串行输出分析，每个角色独立视角：
1. CEO — 商业战略、ROI、市场时机
2. PM — 用户需求、PRD、优先级
3. PJM — 进度管理、风险评估
4. Architect — 系统设计、技术选型
5. Backend — API 设计、数据库、实现
6. Frontend — UI 实现、组件设计、性能
7. UX Designer — 交互设计、可用性
8. QA — 测试策略、质量保障
9. Reviewer — 代码审查、安全、最佳实践

最后由综合结论汇总（核心决策/优先级/风险/下一步）。

### 执行模式

带依赖关系的流水线编排：

```
PM 确认需求 → PJM 制定排期 → Architect 技术方案 → UX 交互方案
    ↓
[Backend 并行开发  ←→  Frontend 并行开发]
    ↓
QA 测试 → Reviewer 审查 → CEO 验收
```

后端和前端并行开发，支持工具调用（Bash/Read/Write）。

## 角色列表

| 角色 ID | 名称 | 权限 | 能力 |
|---------|------|------|------|
| ceo | CEO | 只读 | 战略决策、商业模式、风险 |
| pm | 产品经理 | 只读+Bash | 需求分析、PRD、竞品 |
| pjm | 项目经理 | 只读+Bash | 进度、风险、敏捷 |
| architect | 架构师 | 只读+Bash | 架构设计、技术选型 |
| backend | 后端工程师 | 完整读写 | API、数据库、性能优化 |
| frontend | 前端工程师 | 完整读写 | UI、组件、工程化 |
| ux-designer | UX设计师 | 只读+Bash | 用户研究、交互设计 |
| qa | 测试工程师 | 只读+Bash | 测试策略、自动化 |
| reviewer | 代码审查 | 只读+Bash | 代码质量、安全 |

## 多平台集成

同一个角色定义集，适配 4 个平台：

### Claude Code

```bash
# 安装
cp claude-agents/*.md ~/.claude/agents/
cp claude-commands/team-review.md ~/.claude/commands/

# 使用
@ceo 分析商业价值
/pm 写 PRD
/team-review  # 全流程评审
```

### Codex.app

```bash
cp -r codex-skills/* ~/.codex/skills/
# 使用 /角色名 调用
```

### Codex CLI

```bash
source codex-agents.sh
codex-pm "分析需求"
codex-team-review "做一个 SaaS"
```

### Hermes Agent

```bash
# 合并 config-patch.yaml 到 ~/.hermes/config.yaml
# 安装 skill: cp -r skills/* ~/.hermes/skills/
```

## 项目结构

```
agent-team/
├── pyproject.toml
├── src/agent_team/
│   ├── __init__.py, __main__.py
│   ├── cli/app.py          # Typer CLI 入口
│   ├── config/settings.py  # 分层配置（pydantic-settings）
│   ├── exceptions.py       # 异常层级
│   ├── roles/
│   │   ├── models.py       # Role + PermissionLevel
│   │   ├── registry.py     # 角色注册表
│   │   └── definitions/    # 9 个角色 Markdown
│   ├── engine/
│   │   ├── base.py                   # BaseLLMClient 抽象
│   │   ├── anthropic_client.py       # Anthropic SDK
│   │   ├── openai_compat_client.py   # OpenAI 兼容 API
│   │   ├── client_factory.py         # 工厂 + 自动推断
│   │   ├── prompt_builder.py         # System prompt 组装
│   │   └── tool_executor.py          # Bash/Read/Write
│   ├── workflows/
│   │   ├── base.py         # WorkflowContext/Result
│   │   ├── analysis.py     # 分析模式（串行）
│   │   └── execute.py      # 执行模式（并行）
│   └── output/
│       ├── console.py      # Rich 流式输出
│       ├── json_output.py  # JSON 输出
│       └── markdown_output.py
├── tests/                 # 50 个测试
├── personalities/         # 角色定义（多平台共享）
├── claude-agents/         # Claude Code 配置
├── claude-commands/       # /team-review 命令
├── codex-skills/          # Codex.app 配置
├── codex-agents.sh        # Codex CLI 封装
├── skills/                # Hermes Agent 工作流
└── install.sh             # 传统安装脚本
```

## License

MIT
