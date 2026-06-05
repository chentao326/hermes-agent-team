#!/bin/bash
set -e

# ─────────────────────────────────────────────
#  Hermes Agent Team — 安装脚本
#  9 人虚拟技术团队 × 4 平台
# ─────────────────────────────────────────────
#  用法:
#    ./install.sh             交互式选择
#    ./install.sh --all       一键全装
#    ./install.sh --hermes    仅 Hermes
#    ./install.sh --claude    仅 Claude Code
#    ./install.sh --codex     仅 Codex.app + CLI
#    ./install.sh --help      显示帮助
# ─────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
CONFIG="$HERMES_HOME/config.yaml"

# ── 颜色 ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── 横幅 ──
banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}Hermes Agent Team${NC} — 9 人虚拟技术团队    ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  CEO·PM·项目经理·架构师·后端·前端·UX·QA·审查  ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

# ── 帮助 ──
show_help() {
    banner
    echo "用法:  ./install.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --all       一键安装所有已安装平台"
    echo "  --hermes    仅安装 Hermes Agent（personalities + skill）"
    echo "  --claude    仅安装 Claude Code（9 custom agents）"
    echo "  --codex     仅安装 Codex.app skills + CLI 提示"
    echo "  --help      显示此帮助"
    echo ""
    echo "不带参数运行 = 交互式菜单选择"
    exit 0
}

# ── 平台检测 ──
detect_platforms() {
    HAS_HERMES=false
    HAS_CLAUDE=false
    HAS_CODEX_APP=false
    HAS_CODEX_CLI=false

    [ -f "$CONFIG" ] && HAS_HERMES=true
    command -v claude &>/dev/null && HAS_CLAUDE=true
    [ -d "$HOME/.codex/skills" ] && HAS_CODEX_APP=true
    command -v codex &>/dev/null && HAS_CODEX_CLI=true
}

show_detected() {
    echo -e "${BOLD}检测到的平台:${NC}"
    $HAS_HERMES   && echo -e "  ${GREEN}✓${NC} Hermes Agent  ($CONFIG)"          || echo -e "  ${YELLOW}✗${NC} Hermes Agent  (未安装)"
    $HAS_CLAUDE   && echo -e "  ${GREEN}✓${NC} Claude Code   ($(which claude))"    || echo -e "  ${YELLOW}✗${NC} Claude Code   (未安装)"
    $HAS_CODEX_APP && echo -e "  ${GREEN}✓${NC} Codex.app     ($HOME/.codex)"      || echo -e "  ${YELLOW}✗${NC} Codex.app     (未安装)"
    $HAS_CODEX_CLI && echo -e "  ${GREEN}✓${NC} Codex CLI     ($(which codex))"    || echo -e "  ${YELLOW}✗${NC} Codex CLI     (未安装)"
    echo ""
}

# ── install_hermes ──
install_hermes() {
    echo -e "${BOLD}── 安装 Hermes Agent ──${NC}"

    if [ ! -f "$CONFIG" ]; then
        echo -e "  ${RED}✗${NC} 未找到 Hermes config，跳过"
        return
    fi

    # personalities
    if grep -q "pjm: 你是一位资深技术项目经理" "$CONFIG" 2>/dev/null; then
        echo -e "  ${YELLOW}⚠${NC}  角色定义已存在，跳过"
    else
        echo "  📝 写入 9 个角色定义..."
        python3 -c "
import yaml
with open('$CONFIG', 'r') as f:
    config = yaml.safe_load(f)
personalities = config.get('agent', {}).get('personalities', {})
if 'pjm' in personalities:
    print('Already installed')
else:
    roles = {
        'ceo': '你是一位技术出身的 CEO，拥有创业经验和商业敏锐度。你的核心能力： - 战略决策：从市场趋势、竞争格局、团队能力出发做战略判断 - 资源分配：评估投入产出比（ROI），决定「做什么」和「不做什么」 - 商业模式：分析变现路径、单位经济模型、增长飞轮 - 风险管理：识别商业风险、技术风险、团队风险，制定应对策略 - 组织建设：团队搭建、文化塑造、激励机制 沟通风格：高层视角，用商业语言翻译技术价值。善于提问而非给答案。 标志性问题：「这个项目的商业价值是什么？」「为什么是现在？」「如果只做一件事，做什么？」',
        'pm': '你是一位资深产品经理，拥有10年以上互联网产品经验。你的核心能力： - 需求分析：从用户痛点出发，区分真需求和伪需求，用量化数据支撑判断 - 竞品调研：快速梳理市场格局，找出差异化切入点 - PRD撰写：输出结构化需求文档，包含用户故事、验收标准、优先级排序 - 路线图规划：平衡短期交付与长期愿景，用 MoSCoW 或 RICE 框架排优先级 - 数据驱动：关注核心指标（留存、转化、NPS），用数据验证假设 沟通风格：简洁直接，先说结论再展开。善用「用户故事」的格式表达需求。 当被问到「这个功能要不要做」时，你会先问：目标用户是谁？解决什么痛点？衡量指标是什么？',
        'pjm': '你是一位资深技术项目经理，拥有 CSM/PSM 认证和8年以上敏捷团队管理经验。你的核心能力： - 进度管理：甘特图思维，关键路径分析，里程碑跟踪，燃尽图解读 - 风险管理：风险识别（技术/资源/依赖/外部），概率×影响矩阵，应对策略 - 敏捷实践：Scrum/Kanban 执行，站会、Sprint Planning、Retro 引导 - 资源协调：人员技能匹配，任务负载均衡，跨团队依赖管理 - 复盘总结：Sprint Retro（Start/Stop/Continue），5-Why 根因分析，改进项量化跟踪 沟通风格：结构化、数据驱动。状态汇报格式：进度摘要 → 风险高亮 → 阻碍项 → 下一步。 核心信念：90%的项目问题来自沟通而非技术；风险不报不会消失，只会变大。',
        'architect': '你是一位系统架构师，擅长分布式系统设计和技术决策。你的核心能力： - 架构设计：从业务需求推导技术架构，输出架构图、模块划分、接口定义 - 技术选型：基于团队能力、生态成熟度、性能要求做 trade-off 分析，不追新 - 非功能需求：优先考虑可扩展性、可靠性、安全性、可维护性 - 技术评审：识别单点故障、瓶颈、过度设计，给出具体改进建议 - 演进策略：设计可演进的架构，避免大爆炸式重写 沟通风格：结构化表达，善用对比表格和决策矩阵。每个建议都附带权衡说明。 口头禅：「这个方案在100倍流量下会怎样？」「有没有更简单的方案？」',
        'backend': '你是一位资深后端工程师，精通服务端开发。你的核心能力： - API设计：RESTful / GraphQL，关注接口契约、版本管理、错误处理 - 数据库：SQL/NoSQL 选型，索引优化，查询性能分析，数据迁移策略 - 系统设计：微服务拆分、消息队列、缓存策略、分布式事务 - 性能优化：profiling、慢查询分析、连接池调优、内存管理 - 工程实践：单元测试、CI/CD、日志监控、灰度发布 沟通风格：务实、代码先行。讨论方案时会直接给出示例代码和数据库 schema。 关注点：这个接口的 QPS 是多少？缓存 key 怎么设计？幂等性怎么保证？',
        'frontend': '你是一位资深前端工程师，专注用户体验和前端工程化。你的核心能力： - UI/UX 实现：将设计稿高保真还原，关注交互细节、动画流畅度、无障碍访问 - 组件设计：可复用、可组合的组件架构，关注 props 设计、状态管理、性能 - 工程化：构建优化、代码分割、懒加载、bundle 分析 - 跨端适配：响应式布局、多端兼容、性能预算 - 技术栈：React/Vue/Next.js，TypeScript，CSS-in-JS / Tailwind 沟通风格：视觉化表达，喜欢对比截图和交互流程。关注用户体验细节。 口头禅：「这个交互在移动端会怎样？」「首屏加载时间是多久？」',
        'ux-designer': '你是一位资深 UX 设计师，拥有8年以上产品设计经验。你的核心能力： - 用户研究：用户访谈、用户画像（Persona）、用户旅程地图、A/B 测试设计 - 交互设计：信息架构（IA）、流程图、线框图、交互原型，关注操作效率与认知负荷 - 可用性评估：启发式评估（Nielsen\'s 10 Heuristics）、认知走查、可用性测试方案 - 设计系统：组件规范、交互模式库、设计 token、跨平台一致性 - 无障碍设计：WCAG 2.1 标准，键盘导航、屏幕阅读器适配、色彩对比度 沟通风格：视觉化表达，善用对比、流程图和场景描述。从用户视角出发。 设计的第一性原理：解决用户问题，而非堆砌功能。好的设计是隐形的。',
        'qa': '你是一位资深测试工程师，专注质量保障。你的核心能力： - 测试策略：根据风险制定测试金字塔，平衡自动化与手工测试 - 用例设计：边界值、等价类、场景组合、异常路径全覆盖 - 自动化测试：单元测试、集成测试、E2E 测试框架选型和 CI 集成 - Bug 分析：精准复现步骤、根因定位、影响范围评估 - 质量度量：缺陷密度、测试覆盖率、逃逸率，用数据推动质量改进 沟通风格：严谨细致，用事实说话。Bug 报告格式：复现步骤 → 预期结果 → 实际结果 → 影响评估。 本能反应：看到任何新功能，第一反应是「边界条件是什么？异常情况怎么处理？」',
        'reviewer': '你是一位资深代码审查专家，专注代码质量和安全。你的核心能力： - 代码审查：逻辑正确性、代码风格、设计模式、可读性、可维护性 - 安全检查：OWASP Top 10、注入攻击、敏感信息泄露、权限校验 - 性能审查：N+1 查询、内存泄漏、不必要的渲染、算法复杂度 - 最佳实践：SOLID 原则、DRY/KISS、合适的设计模式而非过度设计 - 测试审查：测试覆盖是否充分、边界条件是否考虑、Mock 是否合理 沟通风格：建设性而非批判性。每个问题给出具体改进建议和代码示例。 审查清单：这个 PR 会不会引入安全漏洞？有没有破坏现有功能？代码是否易于理解和维护？',
    }
    for name, desc in roles.items():
        config['agent']['personalities'][name] = desc
    with open('$CONFIG', 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
    print('Done')
" 2>&1
        echo -e "  ${GREEN}✓${NC}  角色定义写入完成"
    fi

    # skill
    SKILL_DIR="$HERMES_HOME/skills/software-development/agent-team-workflow"
    if [ -d "$SKILL_DIR" ]; then
        echo -e "  ${YELLOW}⚠${NC}  Skill 已存在: $SKILL_DIR"
    elif [ -d "$SCRIPT_DIR/skills/agent-team-workflow" ]; then
        echo "  📝 安装 agent-team-workflow skill..."
        mkdir -p "$(dirname "$SKILL_DIR")"
        cp -r "$SCRIPT_DIR/skills/agent-team-workflow" "$SKILL_DIR"
        echo -e "  ${GREEN}✓${NC}  Skill 安装完成"
    fi

    echo -e "  ${GREEN}→${NC}  使用: /personality ceo | pm | pjm | architect | backend | frontend | ux-designer | qa | reviewer"
    echo -e "  ${GREEN}→${NC}  重启: hermes gateway restart"
    echo ""
}

# ── install_claude ──
install_claude() {
    echo -e "${BOLD}── 安装 Claude Code ──${NC}"

    if ! command -v claude &>/dev/null; then
        echo -e "  ${YELLOW}⚠${NC}  Claude Code 未安装，跳过"
        return
    fi

    CLAUDE_AGENTS="$HOME/.claude/agents"
    CLAUDE_COMMANDS="$HOME/.claude/commands"
    mkdir -p "$CLAUDE_AGENTS" "$CLAUDE_COMMANDS"

    if [ -d "$SCRIPT_DIR/claude-agents" ]; then
        cp "$SCRIPT_DIR/claude-agents/"*.md "$CLAUDE_AGENTS/"
        cp "$SCRIPT_DIR/claude-commands/"*.md "$CLAUDE_COMMANDS/" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC}  9 个 custom agents 已安装"
        echo -e "  ${GREEN}→${NC}  使用: @ceo | @pm | @pjm | @architect | @backend | @frontend | @ux-designer | @qa | @reviewer"
        echo -e "  ${GREEN}→${NC}  协作: /team-review"
    fi
    echo ""
}

# ── install_codex ──
install_codex() {
    echo -e "${BOLD}── 安装 Codex ──${NC}"

    # Codex.app
    if [ -d "$HOME/.codex/skills" ]; then
        if [ -d "$SCRIPT_DIR/codex-skills" ]; then
            for skill in "$SCRIPT_DIR/codex-skills"/*/; do
                skill_name=$(basename "$skill")
                cp -r "$skill" "$HOME/.codex/skills/$skill_name" 2>/dev/null || true
            done
            echo -e "  ${GREEN}✓${NC}  Codex.app — 9 个 agent skills 已安装"
            echo -e "  ${GREEN}→${NC}  使用: /ceo | /pm | /pjm | /architect | /backend | /frontend | /ux | /qa | /reviewer"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC}  Codex.app 未安装，跳过"
    fi

    # Codex CLI
    if command -v codex &>/dev/null; then
        echo -e "  ${GREEN}✓${NC}  Codex CLI — 角色函数脚本: $SCRIPT_DIR/codex-agents.sh"
        echo -e "  ${GREEN}→${NC}  加载: source $SCRIPT_DIR/codex-agents.sh"
        echo -e "  ${GREEN}→${NC}  使用: codex-ceo '...' | codex-pm '...' | codex-pjm '...' | codex-team-review '...'"
    else
        echo -e "  ${YELLOW}⚠${NC}  Codex CLI 未安装，跳过"
    fi
    echo ""
}

# ── 总览 ──
show_summary() {
    echo -e "${BOLD}═══════════════════════════════════════════${NC}"
    echo -e "${BOLD}  角色命令速查${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════${NC}"
    echo ""
    echo "  Hermes:     /personality ceo | pm | pjm | architect | backend | frontend | ux-designer | qa | reviewer"
    echo "  Claude Code: @ceo | @pm | @pjm | @architect | @backend | @frontend | @ux-designer | @qa | @reviewer"
    echo "  Codex.app:  /ceo | /pm | /pjm | /architect | /backend | /frontend | /ux | /qa | /reviewer"
    echo "  Codex CLI:  codex-ceo '...' | codex-pjm '...' | codex-team-review '...'"
    echo ""
}

# ── 交互菜单 ──
interactive_menu() {
    banner
    show_detected

    # 统计可安装平台
    local count=0
    local opts=()
    $HAS_HERMES   && { count=$((count+1)); opts+=("[1] Hermes Agent   (/personality role)"); }
    $HAS_CLAUDE   && { count=$((count+1)); opts+=("[2] Claude Code    (@role 调用)"); }
    $HAS_CODEX_APP && { count=$((count+1)); opts+=("[3] Codex.app      (/role 调用)"); }
    $HAS_CODEX_CLI && { count=$((count+1)); opts+=("[4] Codex CLI      (codex-role 函数)"); }

    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}没有检测到可安装的平台。请先安装 Hermes / Claude Code / Codex。${NC}"
        exit 0
    fi

    echo -e "${BOLD}选择安装目标:${NC}"
    echo "  [0] 全部安装 (All)"
    for opt in "${opts[@]}"; do echo "  $opt"; done
    echo "  [q] 退出"
    echo ""

    read -p "请输入选项 [0-4/q]: " choice
    echo ""

    case "$choice" in
        0) install_all ;;
        1) install_hermes ;;
        2) install_claude ;;
        3) install_codex ;;
        4) install_codex ;;
        q|Q) echo "已取消"; exit 0 ;;
        *) echo -e "${RED}无效选项${NC}"; exit 1 ;;
    esac

    show_summary
}

# ── 全装 ──
install_all() {
    echo -e "${BOLD}═══ 一键安装全部平台 ═══${NC}"
    echo ""
    install_hermes
    install_claude
    install_codex
    show_summary
}

# ── 入口 ──
banner

# 解析参数
case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --all)
        detect_platforms
        install_all
        ;;
    --hermes)
        detect_platforms
        install_hermes
        ;;
    --claude)
        detect_platforms
        install_claude
        ;;
    --codex)
        detect_platforms
        install_codex
        ;;
    "")
        detect_platforms
        interactive_menu
        ;;
    *)
        echo -e "${RED}未知选项: $1${NC}"
        echo "使用 --help 查看帮助"
        exit 1
        ;;
esac
