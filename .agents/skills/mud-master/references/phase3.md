# 阶段三：玩法系统实现（第6-8周）

> 当前进度注记（先看根目录文档）：
> - 当前状态：已完成（source of truth: `DEVELOPMENT_PLAN.md` / `TODO.md`, 2026-02-26）
> - 本文档保留为阶段蓝图回顾、扩展设计和验收索引，不表示当前仍待开发。
> - 若继续修改阶段三能力，优先读取现有源码与测试，再把本文档当作设计参考。

## 当前实现锚点

- `src/game/combat/core.py`
- `src/game/combat/calculator.py`
- `src/game/combat/buff.py`
- `src/game/combat/ai.py`
- `src/game/combat/transaction.py`
- `src/game/quest/core.py`
- `src/game/quest/world_state.py`
- `src/game/quest/karma.py`
- `src/game/npc/core.py`
- `src/game/npc/behavior_tree.py`
- `src/game/npc/behavior_nodes.py`
- `src/game/npc/dialogue.py`
- `src/game/npc/reputation.py`

## 模块清单

| 顺序 | 模块 | 依赖 | 当前状态 |
|:---|:---|:---|:---|
| 1 | 战斗系统 | 阶段二完成 | 已完成 |
| 2 | 任务系统 | 阶段二完成 | 已完成 |
| 3 | NPC系统 | 阶段二完成 | 已完成 |
| 4 | 自然语言命令 | 阶段一完成 | 已完成 |

## 阶段目标回顾

实现核心游戏玩法：战斗、任务、NPC交互与自然语言命令能力。

## 阶段验收标准

- [x] 战斗系统已落地并通过核心测试
- [x] 任务系统可追踪与结算
- [x] NPC行为、对话与好感度系统已实现
- [x] 自然语言相关能力已纳入玩法层

## 若继续扩展阶段三

1. 先查看当前实现集中在哪些现有文件，而不是按设计期拆分模块重建结构。
2. 任何战斗或任务改动都优先补对应单元测试和集成测试。
3. 如果蓝图里提到的子模块当前不存在，先判断它是未来拆分目标还是当前真实缺口。
