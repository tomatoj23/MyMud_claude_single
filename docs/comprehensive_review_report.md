# 全面审查报告 (2026-03-17)

> 审查范围: 源代码、文档、配置、测试
> 审查基于: 代码审查修复 + 测试套件修复之后的状态

---

## 一、源代码问题

### P0 — 关键 (1 项)

| # | 文件 | 行 | 问题 |
|---|------|---|------|
| 1 | `src/game/npc/behavior_tree.py` | 116 | `print()` 应改为 `logger.exception()` |

### P1 — 高优先级 (3 项)

| # | 文件 | 问题 |
|---|------|------|
| 2 | 多文件 (12处) | 裸 `except Exception:` 无日志记录 |
| 3 | `src/utils/lock_parser.py` | 4处 TODO 桩返回占位值 |
| 4 | 多文件 | `Optional[T]` 与 `T \| None` 混用 |

**裸 except 位置**:
- `behavior_tree.py:135`, `behavior_nodes.py:130,202,231`
- `dialogue.py:414,437`, `loader.py:131`
- `scheduler.py:329,370,382`, `engine.py:230,258`
- `transaction.py:122,158`

### P2 — 中优先级 (5 项)

| # | 文件 | 问题 |
|---|------|------|
| 5 | `combat/core.py:111-117` | 冷却常量硬编码 (BASE_COOLDOWN 等) |
| 6 | `combat/ai.py:84-89` | AI 阈值硬编码 (LOW_HP_THRESHOLD 等) |
| 7 | `config.py:336,361` | 异常捕获过宽 (应捕获具体类型) |
| 8 | `database/connection.py:92,152,254` | 异常捕获过宽 |
| 9 | `objects/manager.py:162,340` | 错误日志缺少上下文 |

### P3 — 低优先级 (4 项)

| # | 文件 | 问题 |
|---|------|------|
| 10 | `behavior_tree.py:101` | ActionNode 缺少 docstring |
| 11 | `character.py:18-19` | 空 TYPE_CHECKING 块 |
| 12 | `world/loader.py:64` | `_unload_task` 未跟踪清理 |
| 13 | `combat/ai.py:144` | 英文异常消息 (应统一中文) |

---

## 二、文档问题

### 需要更新 (3 项)

| 优先级 | 文件 | 问题 |
|--------|------|------|
| P1 | `TODO.md` | 最后更新日期过旧 (2026-02-23)，测试数量过时 |
| P1 | `TECHNICAL_DEBT.md` | 版本号仍为 v0.1.0-alpha，应为 v0.2.0 |
| P2 | `DEVELOPMENT_PLAN.md` | Phase 4 状态显示"待开始"但 MVP 已完成 |

### 需要调整 (2 项)

| 优先级 | 文件 | 问题 |
|--------|------|------|
| P2 | `pyproject.toml` | target-version 缺少 py313; mypy python_version 应为 3.13 |
| P3 | `docs/code_review_report.md` | 引用已修复的 P0 问题 |

### 状态良好

✅ README.md, CLAUDE.md, docs/README.md, quickstart.md, current_project_spec.md
✅ .agents/AGENTS.md, mud-master/SKILL.md, kimi-cli.yaml, data/balance.yml

---

## 三、测试问题

### 统计

- 测试文件: 72 个 (45 单元 + 27 集成)
- 测试方法: 1,783 个
- 代码行数: ~29,887 行

### 剩余问题

#### A. 弱断言 (仍有 ~104 处 `assert X is not None`)

主要集中在:
- `test_gui_smoke.py` (14处) — 仅检查组件存在
- `test_set_bonus.py` (10处) — 仅检查对象创建
- `test_engine.py` (12处) — 仅检查引擎/对象非空
- `test_comprehensive_gameplay.py` (6处)
- `test_scheduler.py` (4处)
- `test_database.py` (3处)
- `test_behavior_tree.py` (3处)

#### B. 裸 except 子句 (24 处)

| 文件 | 数量 |
|------|------|
| `test_api_chaos.py` | 7 |
| `test_edge_cases_advanced.py` | 4 |
| `test_performance_stress.py` | 3 |
| `test_chaos_recovery.py` | 1 |
| `test_chaos_player_behavior.py` | 1 |
| `test_comprehensive_gameplay.py` | 1 |
| `test_concurrent_multiplayer.py` | 1 |
| `test_data_migration.py` | 1 |
| `test_edge_case_explosion.py` | 1 |
| 其他 | 4 |

#### C. 弱断言模式 (2 处)

- `test_config.py:400` — `assert result is True or result is None`
- `test_config.py:412` — `assert result is True or result is None`

#### D. 测试隔离问题

- `conftest.py:32-50` — 模块级引擎 fixture 使用全局变量，可能导致状态污染
- `conftest.py:62-70` — 清理代码静默忽略错误

#### E. 覆盖不足的文件

| 文件 | 测试数 | 建议 |
|------|--------|------|
| `test_gui_integration.py` | 4 | 增加功能测试 |
| `test_dynamic_cmdset.py` | 5 | 增加边界测试 |
| `test_command_lock.py` | 5 | 增加并发测试 |
| `test_player_journey.py` | 6 | 增加端到端场景 |

---

## 四、建议优先级

### 立即处理

1. **behavior_tree.py print → logger** (P0, 5分钟)
2. **TODO.md 更新日期和测试数量** (P1, 10分钟)
3. **TECHNICAL_DEBT.md 版本号** (P1, 5分钟)

### 本周处理

4. **12处裸 except 添加日志** (P1, 每处5分钟)
5. **pyproject.toml 版本配置** (P2, 10分钟)
6. **combat 硬编码常量移入配置** (P2, 30分钟)
7. **DEVELOPMENT_PLAN.md Phase 4 状态** (P2, 10分钟)

### 持续改进

8. **加强 ~104 处弱断言** (P2, 大量工作)
9. **测试中 24 处裸 except** (P2, 每处5分钟)
10. **统一 Optional → T | None** (P3, 全局替换)
11. **补充测试覆盖** (P3, 持续)
