# Amazon Product Finder - 项目指令

## 项目概述

亚马逊辅助选品系统。Flask Web 应用，支持多数据源采集（Rainforest API + Playwright）、智能评分、趋势监控、数据导入、价格预警、AI 分析。

## 技术栈

- **后端**: Python 3 + Flask
- **数据库**: SQLite (`db/products.db`)
- **数据采集**: Rainforest API（主） + Playwright 直爬（降级）
- **AI**: OpenAI 兼容 API（智谱 GLM）
- **前端**: 内嵌模板（单文件 SPA + Chart.js）
- **测试**: pytest + Playwright E2E

## 项目结构

```
src/
├── web.py              # Web 服务 + 前端模板（单文件）
├── main.py             # CLI 入口
├── collectors/         # 数据采集器
│   ├── rainforest.py   # Rainforest API
│   └── playwright_scraper.py  # Playwright 直爬
├── analyzer/
│   ├── scorer.py       # 评分引擎
│   ├── profit.py       # 利润分析
│   └── ai_analyzer.py  # AI 分析
├── models/
│   └── product.py      # 数据模型
└── utils/
    └── fba.py          # FBA 费用计算器
scripts/
└── init_db.py          # 数据库管理 + CRUD
tests/
└── test_e2e.py         # Playwright E2E 测试
```

## 开发规范

### 安全（CRITICAL）

- `config.yaml` 包含 API 密钥，已在 `.gitignore` 中排除，**绝不提交**
- 新增配置项必须同步更新 `config.example.yaml`
- 禁止在代码中硬编码密钥，全部通过 `config.yaml` 读取

### 代码风格

- Python，遵循 PEP 8
- 优先不可变模式，避免原地修改
- 函数 < 50 行，文件 < 800 行
- `web.py` 例外：作为单文件 SPA 允许较大体积，但新功能优先拆分到独立模块

### 数据库

- SQLite，通过 `scripts/init_db.py` 管理 schema
- 数据库文件 `db/*.db` 已在 `.gitignore` 中排除
- Schema 变更需在 `init_db.py` 中维护迁移逻辑

## 工作流（Superpowers + OpenSpec）

本项目的开发流程结合 Superpowers 技能和 OpenSpec 变更管理：

### 流程总览

```
需求 → openspec-explore → openspec-propose → writing-plans
     → using-git-worktrees → openspec-apply-change
         → test-driven-development（每个任务）
         → requesting-code-review
     → verification-before-completion → openspec-archive-change
     → finishing-a-development-branch
```

### 阶段 1：需求探索

- 使用 **openspec-explore** 探索需求和想法
- 澄清验收标准和技术约束
- 产出：清晰的需求描述

### 阶段 2：变更提案

- 使用 **openspec-propose** 生成完整变更提案
- 包含：spec.md + design.md + tasks.md
- 人工确认后再进入实现

### 阶段 3：实现计划

- 使用 **writing-plans** 细化任务分解
- 每个任务包含：精确文件路径、代码变更、验证步骤
- 任务粒度：每个任务可独立验证

### 阶段 4：实现执行

- 使用 **using-git-worktrees** 创建隔离工作空间
- 使用 **openspec-apply-change** 逐任务执行
- 每个任务内部遵循：
  - **test-driven-development**: 先写失败测试 → 最小实现 → 重构
  - **requesting-code-review**: 任务完成后审查
  - Critical 问题阻塞后续任务

### 阶段 5：完成验证

- **verification-before-completion**: 运行所有测试，验证功能
- **openspec-archive-change**: 归档完成的变更
- **finishing-a-development-branch**: 合并/PR/清理

### 技能优先级

| 场景 | 优先使用 | 说明 |
|------|---------|------|
| 新功能开发 | openspec-propose → writing-plans | 先规格再计划 |
| Bug 修复 | systematic-debugging → test-driven-development | 先定位再修 |
| 代码审查 | requesting-code-review / receiving-code-review | 双向审查 |
| 探索想法 | openspec-explore | 苏格拉底式对话 |
| 多任务并行 | dispatching-parallel-agents | 独立任务并发 |

### 任务管理

- 每个开发任务必须使用 TodoWrite 跟踪进度
- 任务状态：pending → in_progress → completed
- 同一时间只有一个任务 in_progress

## 常用命令

```bash
# 安装依赖
uv pip install -r requirements.txt

# 启动开发服务器
python src/web.py

# 运行测试
pytest tests/ -v

# E2E 测试
python -m pytest tests/test_e2e.py -v

# 数据库初始化
python scripts/init_db.py
```

## 当前开发阶段

- Phase 1-3.5: 已完成
- Phase 4: 供应链分析 / 关键词挖掘 / 评论情感分析（待开发）
- Phase 5: 多用户 / Chrome 插件 / 企微集成（待开发）
