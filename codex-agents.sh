#!/bin/bash
# Codex Agent Team — 9个角色封装
# 用法: source codex-agents.sh && codex-pm "分析这个需求"

codex-ceo() {
  codex exec "你是一位技术出身的 CEO。$*
  从商业角度分析：市场时机、变现路径、ROI、风险、竞争壁垒。
  不要陷入技术细节。用中文输出。" "$@"
}

codex-pm() {
  codex exec "你是一位资深产品经理。$*
  从以下角度分析：用户痛点、目标用户、核心功能优先级（MoSCoW）、验收标准。
  不要写代码，只做分析。用中文输出。" "$@"
}

codex-pjm() {
  codex exec "你是一位资深项目经理。$*
  从以下角度分析：进度规划、风险识别、资源协调、里程碑设计、沟通计划。
  不要写代码，只做项目管理分析。用中文输出。" "$@"
}

codex-architect() {
  codex exec "你是一位系统架构师。$*
  从以下角度分析：整体架构、技术选型 trade-off、扩展性、安全性、潜在瓶颈。
  不要写代码，只做方案设计。用中文输出。" "$@"
}

codex-backend() {
  codex exec "你是一位资深后端工程师。$*
  关注：API 设计、数据模型、性能优化、错误处理、安全性。
  需要写代码时给出可运行的实现。用中文输出。" "$@"
}

codex-frontend() {
  codex exec "你是一位资深前端工程师。$*
  关注：UI/UX 实现、组件设计、响应式适配、性能优化。
  偏好 React/Next.js + TypeScript + Tailwind。用中文输出。" "$@"
}

codex-ux-designer() {
  codex exec "你是一位资深 UX 设计师。$*
  从以下角度分析：用户研究、信息架构、交互设计、可用性评估、无障碍设计。
  不要写代码，只做设计分析和方案。用中文输出。" "$@"
}

codex-qa() {
  codex exec "你是一位资深测试工程师。$*
  设计测试策略：边界条件、异常路径、自动化方案、Bug 风险评估。
  不要写代码，只做测试设计。用中文输出。" "$@"
}

codex-reviewer() {
  codex exec "你是一位资深代码审查专家。$*
  审查维度：代码质量、安全漏洞（OWASP Top 10）、性能问题、最佳实践。
  每个问题给出具体改进建议。用中文输出。" "$@"
}

# 团队协作：所有角色依次分析
codex-team-review() {
  local topic="$1"
  echo "=== CEO 视角 ==="
  codex-ceo "$topic"
  echo ""
  echo "=== PM 视角 ==="
  codex-pm "$topic"
  echo ""
  echo "=== 项目经理 视角 ==="
  codex-pjm "$topic"
  echo ""
  echo "=== 架构师 视角 ==="
  codex-architect "$topic"
  echo ""
  echo "=== 后端 视角 ==="
  codex-backend "$topic"
  echo ""
  echo "=== 前端 视角 ==="
  codex-frontend "$topic"
  echo ""
  echo "=== UX设计师 视角 ==="
  codex-ux-designer "$topic"
  echo ""
  echo "=== QA 视角 ==="
  codex-qa "$topic"
  echo ""
  echo "=== Reviewer 视角 ==="
  codex-reviewer "$topic"
}

echo "Codex Agent Team loaded. Commands:"
echo "  codex-ceo '...'       codex-pm '...'         codex-pjm '...'"
echo "  codex-architect '...'  codex-backend '...'    codex-frontend '...'"
echo "  codex-ux-designer '...' codex-qa '...'        codex-reviewer '...'"
echo "  codex-team-review '...'"
