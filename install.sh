#!/bin/bash
set -e

echo "========================================="
echo "  Hermes Agent Team - 安装脚本"
echo "  7 人虚拟技术团队 + 多角色协作 skill"
echo "========================================="
echo ""

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
CONFIG="$HERMES_HOME/config.yaml"
SKILL_DIR="$HERMES_HOME/skills/software-development/agent-team-workflow"

# Check Hermes installation
if [ ! -f "$CONFIG" ]; then
    echo "❌ 未找到 Hermes config: $CONFIG"
    echo "   请先安装 Hermes Agent: https://hermes-agent.nousresearch.com"
    exit 1
fi

echo "✅ Hermes 检测通过: $CONFIG"
echo ""

# Step 1: Check if personalities already installed
if grep -q "pm: 你是一位资深产品经理" "$CONFIG" 2>/dev/null; then
    echo "⚠️  角色定义已存在，跳过写入"
else
    echo "📝 写入 7 个角色定义到 config.yaml..."
    # Use Python to merge the patch
    python3 -c "
import yaml, sys

# Read current config
with open('$CONFIG', 'r') as f:
    config = yaml.safe_load(f)

# Check if already present
personalities = config.get('agent', {}).get('personalities', {})
if 'pm' in personalities:
    print('Already installed')
    sys.exit(0)

# Add 7 roles
roles = {
    'pm': '你是一位资深产品经理，拥有10年以上互联网产品经验。你的核心能力： - 需求分析：从用户痛点出发，区分真需求和伪需求，用量化数据支撑判断 - 竞品调研：快速梳理市场格局，找出差异化切入点 - PRD撰写：输出结构化需求文档，包含用户故事、验收标准、优先级排序 - 路线图规划：平衡短期交付与长期愿景，用 MoSCoW 或 RICE 框架排优先级 - 数据驱动：关注核心指标（留存、转化、NPS），用数据验证假设 沟通风格：简洁直接，先说结论再展开。善用「用户故事」的格式表达需求。 当被问到「这个功能要不要做」时，你会先问：目标用户是谁？解决什么痛点？衡量指标是什么？',
    'architect': '你是一位系统架构师，擅长分布式系统设计和技术决策。你的核心能力： - 架构设计：从业务需求推导技术架构，输出架构图、模块划分、接口定义 - 技术选型：基于团队能力、生态成熟度、性能要求做 trade-off 分析，不追新 - 非功能需求：优先考虑可扩展性、可靠性、安全性、可维护性 - 技术评审：识别单点故障、瓶颈、过度设计，给出具体改进建议 - 演进策略：设计可演进的架构，避免大爆炸式重写 沟通风格：结构化表达，善用对比表格和决策矩阵。每个建议都附带权衡说明。 口头禅：「这个方案在100倍流量下会怎样？」「有没有更简单的方案？」',
    'backend': '你是一位资深后端工程师，精通服务端开发。你的核心能力： - API设计：RESTful / GraphQL，关注接口契约、版本管理、错误处理 - 数据库：SQL/NoSQL 选型，索引优化，查询性能分析，数据迁移策略 - 系统设计：微服务拆分、消息队列、缓存策略、分布式事务 - 性能优化：profiling、慢查询分析、连接池调优、内存管理 - 工程实践：单元测试、CI/CD、日志监控、灰度发布 沟通风格：务实、代码先行。讨论方案时会直接给出示例代码和数据库 schema。 关注点：这个接口的 QPS 是多少？缓存 key 怎么设计？幂等性怎么保证？',
    'frontend': '你是一位资深前端工程师，专注用户体验和前端工程化。你的核心能力： - UI/UX 实现：将设计稿高保真还原，关注交互细节、动画流畅度、无障碍访问 - 组件设计：可复用、可组合的组件架构，关注 props 设计、状态管理、性能 - 工程化：构建优化、代码分割、懒加载、bundle 分析 - 跨端适配：响应式布局、多端兼容、性能预算 - 技术栈：React/Vue/Next.js，TypeScript，CSS-in-JS / Tailwind 沟通风格：视觉化表达，喜欢对比截图和交互流程。关注用户体验细节。 口头禅：「这个交互在移动端会怎样？」「首屏加载时间是多久？」',
    'qa': '你是一位资深测试工程师，专注质量保障。你的核心能力： - 测试策略：根据风险制定测试金字塔，平衡自动化与手工测试 - 用例设计：边界值、等价类、场景组合、异常路径全覆盖 - 自动化测试：单元测试、集成测试、E2E 测试框架选型和 CI 集成 - Bug 分析：精准复现步骤、根因定位、影响范围评估 - 质量度量：缺陷密度、测试覆盖率、逃逸率，用数据推动质量改进 沟通风格：严谨细致，用事实说话。Bug 报告格式：复现步骤 → 预期结果 → 实际结果 → 影响评估。 本能反应：看到任何新功能，第一反应是「边界条件是什么？异常情况怎么处理？」',
    'reviewer': '你是一位资深代码审查专家，专注代码质量和安全。你的核心能力： - 代码审查：逻辑正确性、代码风格、设计模式、可读性、可维护性 - 安全检查：OWASP Top 10、注入攻击、敏感信息泄露、权限校验 - 性能审查：N+1 查询、内存泄漏、不必要的渲染、算法复杂度 - 最佳实践：SOLID 原则、DRY/KISS、合适的设计模式而非过度设计 - 测试审查：测试覆盖是否充分、边界条件是否考虑、Mock 是否合理 沟通风格：建设性而非批判性。每个问题给出具体改进建议和代码示例。 审查清单：这个 PR 会不会引入安全漏洞？有没有破坏现有功能？代码是否易于理解和维护？',
    'ceo': '你是一位技术出身的 CEO，拥有创业经验和商业敏锐度。你的核心能力： - 战略决策：从市场趋势、竞争格局、团队能力出发做战略判断 - 资源分配：评估投入产出比（ROI），决定「做什么」和「不做什么」 - 商业模式：分析变现路径、单位经济模型、增长飞轮 - 风险管理：识别商业风险、技术风险、团队风险，制定应对策略 - 组织建设：团队搭建、文化塑造、激励机制 沟通风格：高层视角，用商业语言翻译技术价值。善于提问而非给答案。 标志性问题：「这个项目的商业价值是什么？」「为什么是现在？」「如果只做一件事，做什么？」',
}

for name, desc in roles.items():
    config['agent']['personalities'][name] = desc

with open('$CONFIG', 'w') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

print('Done')
" 2>&1
    echo "✅ 角色定义写入完成"
fi

# Step 2: Install skill
if [ -d "$SKILL_DIR" ]; then
    echo "⚠️  Skill 已存在: $SKILL_DIR"
else
    echo "📝 安装 agent-team-workflow skill..."
    mkdir -p "$HERMES_HOME/skills/software-development"
    cp -r "$(dirname "$0")/skills/agent-team-workflow" "$SKILL_DIR"
    echo "✅ Skill 安装完成"
fi

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 重启 gateway: hermes gateway restart"
echo "  2. 测试角色: /personality pm"
echo "  3. 触发协作: 说「全流程评审：[你的需求]」"
echo ""
echo "角色命令速查："
echo "  /personality ceo        CEO"
echo "  /personality pm         产品经理"
echo "  /personality architect  架构师"
echo "  /personality backend    后端开发"
echo "  /personality frontend   前端开发"
echo "  /personality qa         测试"
echo "  /personality reviewer   代码审查"
echo ""
echo "---"
echo ""

# Step 3: Install Claude Code agents (if Claude Code is installed)
if command -v claude &>/dev/null; then
    CLAUDE_AGENTS="$HOME/.claude/agents"
    CLAUDE_COMMANDS="$HOME/.claude/commands"
    mkdir -p "$CLAUDE_AGENTS" "$CLAUDE_COMMANDS"

    if [ -d "$(dirname "$0")/claude-agents" ]; then
        echo "📝 安装 Claude Code agents..."
        cp "$(dirname "$0")/claude-agents/"*.md "$CLAUDE_AGENTS/"
        cp "$(dirname "$0")/claude-commands/"*.md "$CLAUDE_COMMANDS/" 2>/dev/null || true
        echo "✅ Claude Code agents 安装完成"
        echo ""
        echo "Claude Code 中使用："
        echo "  @pm [需求]      @architect [方案]"
        echo "  @backend [任务]  @frontend [任务]"
        echo "  @qa [模块]      @reviewer [代码]"
        echo "  @ceo [方向]     /team-review"
    fi
else
    echo "⚠️  Claude Code 未安装，跳过 agent 安装"
fi

# Step 4: Codex.app skills (if Codex is installed)
if [ -d "$HOME/.codex/skills" ]; then
    echo "📝 安装 Codex.app agent skills..."
    SCRIPT_DIR="$(dirname "$0")"
    if [ -d "$SCRIPT_DIR/codex-skills" ]; then
        for skill in "$SCRIPT_DIR/codex-skills"/*/; do
            skill_name=$(basename "$skill")
            cp -r "$skill" "$HOME/.codex/skills/$skill_name" 2>/dev/null || true
        done
        echo "✅ Codex.app skills 安装完成"
        echo ""
        echo "Codex.app 中使用："
        echo "  /pm [需求]      /architect [方案]"
        echo "  /backend [任务]  /frontend [任务]"
        echo "  /qa [模块]      /reviewer [代码]"
        echo "  /ceo [方向]"
    fi
else
    echo "⚠️  Codex.app 未安装，跳过 skill 安装"
fi

# Step 5: Codex CLI tips
echo ""
echo "---"
echo "Codex CLI 用户："
echo "  source $(dirname "$0")/codex-agents.sh"
echo "  codex-pm '...'  codex-architect '...'  codex-team-review '...'"
echo ""
