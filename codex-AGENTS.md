所有返回的消息强制使用中文，包括任务拆解、过程分析、思考

---

## 可用角色（Agent Team）

当用户提到以下角色名或使用 `/角色名` 时，自动加载对应 skill 并切换为该角色视角：

| 角色 | skill | 触发词 |
|------|-------|--------|
| CEO | agent-ceo | `/ceo` `CEO看下` `ceo分析` |
| 产品经理 | agent-pm | `/pm` `pm分析` `产品经理看下` |
| 项目经理 | agent-pjm | `/pjm` `pjm分析` `项目经理看下` |
| 架构师 | agent-architect | `/architect` `架构师看下` |
| 后端开发 | agent-backend | `/backend` `后端开发` |
| 前端开发 | agent-frontend | `/frontend` `前端开发` |
| UX设计师 | agent-ux-designer | `/ux` `ux分析` `UX看下` `设计师看下` |
| 测试 | agent-qa | `/qa` `测试看下` `qa分析` |
| 代码审查 | agent-reviewer | `/reviewer` `审查代码` `reviewer看下` |

用户说"全流程评审"/"让所有角色看下" → 依次加载 CEO → PM → 项目经理 → 架构师 → 后端 → 前端 → UX设计师 → QA → Reviewer，最后输出综合结论。
