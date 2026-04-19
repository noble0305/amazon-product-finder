# 开发工作流使用指南

本项目采用 **Superpowers + OpenSpec** 结合的开发工作流。本文档说明如何在日常开发中使用这套流程。

## 概念介绍

### Superpowers

[Superpowers](https://github.com/obra/superpowers) 是一套 AI 编码代理的方法论，通过可组合的技能（Skills）强制执行结构化开发流程。核心理念是：**不急于写代码，先搞清楚要做什么，再按纪律执行。**

### OpenSpec

OpenSpec 是一套变更管理系统，通过结构化的规格文档管理需求变更的完整生命周期：提案 → 设计 → 任务 → 实现 → 归档。

### 结合思路

| 关注点 | 工具 | 职责 |
|--------|------|------|
| **做什么** | OpenSpec | 需求探索、规格定义、变更追踪、归档 |
| **怎么做** | Superpowers | TDD、代码审查、Git 管理、质量保证 |

---

## 完整工作流

```
 ┌─────────────────────────────────────────────────────┐
 │  1. openspec-explore     需求探索（苏格拉底式提问）    │
 │  2. openspec-propose     生成变更提案（spec+design+tasks）│
 │  3. writing-plans        细化实现计划                  │
 │  4. using-git-worktrees  创建隔离工作分支              │
 │  5. openspec-apply-change 逐任务执行                  │
 │     ┌─ test-driven-development  每个任务走 TDD ──┐    │
 │     └─ requesting-code-review   完成后代码审查   ─┘    │
 │  6. verification-before-completion  完成前验证        │
 │  7. openspec-archive-change      归档变更             │
 │  8. finishing-a-development-branch 合并/PR/清理       │
 └─────────────────────────────────────────────────────┘
```

---

## 各阶段详解

### 阶段 1：需求探索

**触发方式**：向 AI 描述你想要的功能或改进

**示例对话**：
```
你：我想加一个关键词趋势分析功能
AI：（自动触发 openspec-explore）
    - 你希望分析哪些关键词指标？
    - 数据来源是什么？搜索词还是产品标题？
    - 需要什么形式的展示？图表还是报告？
```

**产出**：清晰的需求描述

### 阶段 2：变更提案

**触发方式**：需求明确后，AI 自动触发

**产出三个文件**（在 `openspec/changes/<变更名>/` 目录下）：
- `specs/spec.md` — 功能规格
- `design.md` — 技术设计
- `tasks.md` — 任务分解

**你需要做的**：阅读并确认提案内容

### 阶段 3：实现计划

**触发方式**：提案确认后自动触发

**产出**：每个任务包含精确的：
- 要修改的文件路径
- 代码变更内容
- 验证步骤

### 阶段 4：隔离开发

**触发方式**：计划确认后自动触发

**动作**：
- 创建 git worktree（隔离工作空间）
- 在新分支上开发
- 不影响 main 分支

### 阶段 5：逐任务实现

**触发方式**：按任务顺序自动执行

**每个任务内部遵循 TDD**：
1. **RED** — 先写一个失败的测试
2. **GREEN** — 写最小代码让测试通过
3. **REFACTOR** — 重构代码，保持测试通过

**每个任务完成后自动代码审查**，Critical 问题会阻塞后续任务。

### 阶段 6：完成验证

**触发方式**：所有任务完成后自动触发

**动作**：
- 运行全量测试
- 验证功能完整性
- 确认无回归

### 阶段 7：归档变更

**触发方式**：验证通过后自动触发

**动作**：将变更记录归档到 OpenSpec 目录

### 阶段 8：分支收尾

**触发方式**：归档完成后自动触发

**提供选项**：
- Merge 到 main
- 创建 Pull Request
- 保留分支继续开发
- 丢弃变更

---

## 常见场景速查

### 场景 1：开发新功能

```
你：帮我做一个 XXX 功能

→ 自动走完整流程（阶段 1-8）
```

### 场景 2：修复 Bug

```
你：XXX 页面点击后报错了，错误信息是 YYY

→ 触发 systematic-debugging（4 阶段根因分析）
→ 触发 test-driven-development（先写失败测试再修复）
```

### 场景 3：多个独立任务

```
你：帮我同时做 A、B、C 三件事

→ 触发 dispatching-parallel-agents（并行派发子代理）
→ 每个子代理独立执行任务
```

### 场景 4：只想讨论想法

```
你：我在想是不是可以加一个 XXX 功能，你觉得呢？

→ 触发 openspec-explore（纯讨论，不写代码）
```

### 场景 5：代码审查

```
你：帮我审查一下最近的代码变更

→ 触发 requesting-code-review（按严重程度报告问题）
```

---

## 技能清单

| 技能 | 类型 | 说明 |
|------|------|------|
| `openspec-explore` | 流程（灵活） | 苏格拉底式需求探索 |
| `openspec-propose` | 流程（灵活） | 生成完整变更提案 |
| `openspec-apply-change` | 流程（灵活） | 按 OpenSpec 任务执行 |
| `openspec-archive-change` | 流程（灵活） | 归档完成的变更 |
| `brainstorming` | 流程（灵活） | 创意讨论和设计验证 |
| `writing-plans` | 流程（灵活） | 生成详细实现计划 |
| `executing-plans` | 流程（灵活） | 带检查点的批量执行 |
| `test-driven-development` | 纪律（严格） | RED-GREEN-REFACTOR 循环 |
| `systematic-debugging` | 纪律（严格） | 4 阶段根因分析 |
| `verification-before-completion` | 纪律（严格） | 完成前强制验证 |
| `requesting-code-review` | 纪律（严格） | 代码审查检查清单 |
| `receiving-code-review` | 纪律（严格） | 处理审查反馈 |
| `using-git-worktrees` | 工具（灵活） | 创建隔离开发分支 |
| `finishing-a-development-branch` | 工具（灵活） | 分支合并/PR/清理 |
| `dispatching-parallel-agents` | 工具（灵活） | 并行子代理调度 |
| `subagent-driven-development` | 工具（灵活） | 子代理快速迭代 |

**严格类型**：必须按流程执行，不可跳过步骤。
**灵活类型**：可根据项目情况调整。

---

## 常用命令

```bash
# 一键安装 + 开发工具
make dev

# 运行全部测试
make test

# 运行单元测试（跳过 E2E）
make test-unit

# 运行测试并生成覆盖率报告
make test-cov

# 代码风格检查
make lint

# 自动格式化
make format

# 启动开发服务器
make run

# 清理缓存
make clean
```

---

## 注意事项

1. **不要跳过 TDD**：先写测试再写实现，这是核心纪律
2. **确认后再执行**：提案和计划阶段需要你确认后才进入实现
3. **密钥安全**：`config.yaml` 已在 `.gitignore` 中，不要提交密钥
4. **任务粒度**：每个任务应可独立验证，不要过大
5. **代码审查**：Critical 级别的问题必须修复后才能继续
