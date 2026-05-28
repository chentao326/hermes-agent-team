# Hermes Agent Team

为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 打造的 7 人虚拟技术团队 —— 一套预定义的角色人格（persona）和自动化协作工作流。

```
CEO → PM → 架构师 → 后端 ←→ 前端 → 测试 → 审查
```

## 角色列表

| 角色 | 命令 | 定位 |
|------|------|------|
| CEO | `/personality ceo` | 商业战略、资源分配、ROI |
| 产品经理 | `/personality pm` | 需求分析、PRD、优先级 |
| 架构师 | `/personality architect` | 系统设计、技术选型 |
| 后端开发 | `/personality backend` | API、数据库、性能 |
| 前端开发 | `/personality frontend` | UI/UX、组件、工程化 |
| 测试 | `/personality qa` | 测试策略、自动化 |
| 代码审查 | `/personality reviewer` | 审查、安全、最佳实践 |

## 安装

### 方式一：交互式安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/chentao326/hermes-agent-team/main/install.sh | bash
```

脚本会检测你安装了哪些平台，让你选择安装目标。

### 方式二：命令行指定

```bash
# 一键全装
curl -fsSL ... | bash -s -- --all

# 只装指定平台
curl -fsSL ... | bash -s -- --hermes    # Hermes Agent
curl -fsSL ... | bash -s -- --claude    # Claude Code
curl -fsSL ... | bash -s -- --codex     # Codex.app + CLI
```

### 方式三：手动安装

**1. 添加角色定义**

打开 `~/.hermes/config.yaml`，在 `agent.personalities` 下添加 [config-patch.yaml](./config-patch.yaml) 中的内容。

**2. 安装 Skill**

```bash
cp -r skills/agent-team-workflow ~/.hermes/skills/software-development/
```

**3. 重启**

```bash
hermes gateway restart
```

## 使用

### 切换角色

在 Hermes 聊天中（CLI / 飞书 / Telegram 等）：

```
/personality ceo        # 切换到 CEO 视角
/personality pm         # 切换到产品经理
/personality architect  # 切换到架构师
/personality none       # 恢复默认
```

### 多角色协作分析

触发 `agent-team-workflow` skill 后，直接描述需求即可：

```
"全流程评审：做一个 AI 客服 SaaS"
"让 CEO 和 PM 看下这个想法"
"后端和前端一起评估这个技术方案"
```

Agent 会按角色依次输出分析，最后给出综合结论。

### 执行模式

有明确需求需要编码实现时，skill 会调度 delegate_task 派发不同角色的子代理并行工作。

### Claude Code 中使用

安装后，在 Claude Code 中直接用 `@角色名` 调用：

```
@ceo 评估这个项目的商业价值
@pm 分析这个需求的优先级
@architect 评估这个技术方案的扩展性
@backend 实现这个 API 接口
@frontend 实现这个页面的响应式布局
@qa 为这个模块设计测试策略
@reviewer 审查最近的代码变更
```

多角色协作：
```
/team-review   # 自动调用所有角色，生成综合分析报告
```

**手动安装 Claude Code agents：**

```bash
cp claude-agents/*.md ~/.claude/agents/
cp claude-commands/team-review.md ~/.claude/commands/
```

### Codex.app（桌面应用）中使用

安装 skill 后，在 Codex.app 中直接说：

```
/pm 分析这个需求
/architect 设计技术方案
/backend 实现 API 接口
/frontend 实现页面
/qa 写测试用例
/reviewer 审查代码
/ceo 评估商业价值
```

**安装 Codex.app skills：**

```bash
cp -r codex-skills/* ~/.codex/skills/
cp codex-AGENTS.md ~/.codex/AGENTS.md   # 或手动追加内容
```

### Codex CLI 中使用

```bash
source codex-agents.sh        # 加载角色函数
codex-pm "分析这个需求"         # 产品经理视角
codex-architect "设计技术方案"   # 架构师视角
codex-backend "实现 API"       # 后端开发
codex-frontend "实现页面"       # 前端开发
codex-team-review "做一个 AI SaaS"  # 全流程分析
```

## 项目结构

```
hermes-agent-team/
├── README.md
├── LICENSE
├── install.sh                  # 一键安装 Hermes
├── config-patch.yaml           # 角色定义（可直接合并到 config.yaml）
├── codex-skills/               # Codex.app 自定义 skills
│   ├── agent-pm/
│   ├── agent-architect/
│   ├── agent-backend/
│   ├── agent-frontend/
│   ├── agent-qa/
│   ├── agent-reviewer/
│   └── agent-ceo/
├── codex-AGENTS.md             # Codex.app 全局配置示例
├── codex-agents.sh             # Codex CLI 角色函数
├── claude-agents/              # Claude Code 自定义 agents
│   ├── ceo.md
│   ├── pm.md
│   ├── architect.md
│   ├── backend.md
│   ├── frontend.md
│   ├── qa.md
│   └── reviewer.md
├── claude-commands/            # Claude Code 自定义命令
│   └── team-review.md
├── personalities/              # 角色文档
│   ├── ceo.md
│   ├── pm.md
│   ├── architect.md
│   ├── backend.md
│   ├── frontend.md
│   ├── qa.md
│   └── reviewer.md
└── skills/
    └── agent-team-workflow/   # 多角色协作 skill
        └── SKILL.md
```

## License

MIT
