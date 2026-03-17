# 阶段一：引擎核心搭建（第1-3周）

> 当前进度注记（先看根目录文档）：
> - 当前状态：已完成（source of truth: `DEVELOPMENT_PLAN.md` / `TODO.md`, 2026-02-26）
> - 本文档保留为阶段蓝图回顾、扩展设计和验收索引，不表示当前仍待开发。
> - 若继续修改阶段一能力，优先读取现有源码与测试，而不是按本文重新起脚手架。

## 当前实现锚点

- `src/utils/config.py`
- `src/utils/logging.py`
- `src/engine/database/connection.py`
- `src/engine/database/models.py`
- `src/engine/core/typeclass.py`
- `src/engine/objects/manager.py`
- `src/engine/commands/command.py`
- `src/engine/commands/cmdset.py`
- `src/engine/commands/handler.py`
- `src/engine/commands/default.py`
- `src/engine/events/scheduler.py`
- `src/engine/events/qt_scheduler.py`
- `src/engine/core/engine.py`

## 模块清单

| 顺序 | 模块 | 依赖 | 当前状态 |
|:---|:---|:---|:---|
| 1 | 项目骨架（目录、配置、日志） | 无 | 已完成 |
| 2 | SQLite数据库基础设施 | 1 | 已完成 |
| 3 | ORM模型与实体基类 | 2 | 已完成 |
| 4 | Typeclass动态类系统 | 3 | 已完成 |
| 5 | ObjectManager对象管理器 | 4 | 已完成 |
| 6 | CmdSet命令集合系统 | 5 | 已完成 |
| 7 | 命令解析流水线 | 6 | 已完成 |
| 8 | EventScheduler事件调度 | 7 | 已完成 |
| 9 | GameEngine整合 | 8 | 已完成 |
| 10 | 基础命令实现 | 9 | 已完成 |

## 阶段目标回顾

建立单机版 MUD 引擎的基础框架，实现对象管理、命令处理、事件调度三大核心系统，并具备基础交互能力。

## 阶段验收标准

- [x] 引擎核心模块已落地
- [x] 命令行基础交互已实现
- [x] 核心测试已覆盖并通过

## 若继续扩展阶段一

1. 先定位现有实现文件与相关测试。
2. 再把本文档当作设计意图和验收约束。
3. 若本文中的目录或文件名与当前仓库不一致，以当前目录树为准。
