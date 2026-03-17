# 当前项目规格说明

> 适用项目：单机版金庸武侠文字 MUD
>
> 文档状态：Active
>
> 编制日期：2026-03-11

## 1. 文档目的

本文档是面向当前开发阶段的项目规格说明，用于统一产品目标、工程边界、当前阶段范围、验收标准与文档优先级。

它不是对长期开发计划的重复整理，也不是历史归档。本文档的目标是回答四个问题：

1. 这个项目当前到底在做什么。
2. 现在应当优先完成什么，不应提前做什么。
3. 哪些代码结构是现状，哪些只是未来蓝图。
4. 后续开发和审查应以什么标准判断“完成”。

## 2. 规格适用范围

本文档适用于以下工作：

- 当前版本功能规划
- GUI 阶段开发
- 跨模块实现与重构
- 阶段验收与代码审查
- 后续 spec、task、skill 的统一参考基线

本文档不替代详细设计文档、API 文档、历史迁移文档或未来研究文档。

## 3. 信息源优先级

为避免“计划”和“现状”混淆，本文档定义以下优先级。

### 3.1 进度判断优先级

1. [TODO.md](/D:/My_Projects/MUD_Python/TODO.md)
2. [docs/tech_debt_report.md](/D:/My_Projects/MUD_Python/docs/tech_debt_report.md)
3. [DEVELOPMENT_PLAN.md](/D:/My_Projects/MUD_Python/DEVELOPMENT_PLAN.md)
4. [MIGRATION_LOG.md](/D:/My_Projects/MUD_Python/MIGRATION_LOG.md)
5. `docs/archive/` 与研究性文档

### 3.2 实现判断优先级

1. 当前 `src/` 与 `tests/` 中已存在的真实代码
2. 当前有效的架构与规范文档
3. `mud-master` references 中的阶段蓝图与设计参考
4. 归档文档与前瞻性研究文档

### 3.3 冲突处理规则

- 如果某份文档描述的文件路径在仓库中尚不存在，应视为未来规划，不得直接假定为当前实现。
- 如果根目录进度文档和旧设计文档冲突，以较新的进度文档和当前代码为准。
- 如果 API 文档与当前代码不一致，以当前代码行为为准，并在后续补齐文档。

## 4. 项目定位

本项目是一个以金庸武侠世界为背景的单机文字 MUD，核心目标是：

- 提供单机本地运行的武侠 RPG / MUD 体验
- 保留经典 MUD 的对象模型、命令系统、房间探索、战斗与任务结构
- 采用现代 Python 架构与桌面 GUI，而不是传统网络多人服务器
- 在可维护、可测试、可扩展的基础上逐步完成 GUI、内容与存档能力

## 5. 当前开发基线

截至 2026-03-15，项目当前基线为：

- Phase 1 核心引擎：已完成
- Phase 2 游戏系统：已完成
- Phase 3 架构债务治理：已完成
- 架构债务清偿：已完成
- Phase 4 GUI：MVP 已完成（T4-GUI-001~010），Backlog 待后续迭代
- Phase 5 内容系统：未开始
- Phase 6 存档与开发工具：未开始

当前项目不应被视为”从零开始设计”，而应被视为”核心可玩引擎已具备，GUI MVP 已打通，正在补齐后续产品化能力”。

## 6. 当前版本目标

当前版本的主目标是完成 Phase 4 GUI 的可用闭环，使玩家能够通过桌面界面稳定驱动已完成的核心系统。

### 6.1 当前必须完成的能力

- GUI 能稳定启动并承载游戏主循环
- GUI 与 `asyncio` / Qt 事件系统能可靠协作
- 玩家输入能通过 GUI 进入现有命令执行链路
- 游戏输出能通过消息系统稳定显示到 GUI
- GUI 至少具备主输出区、输入区和基础状态展示
- GUI 接入后不能破坏现有核心系统、测试基线和性能优化成果

### 6.2 当前应优先完成的能力

- 主窗口布局稳定化
- 关键面板拆分与职责明确化
- 主题、配置、常用交互入口的最小骨架
- GUI 场景下的错误恢复与日志可见性

### 6.3 当前明确不做的事情

- 多人联网 / 服务端化
- 大规模内容包导入
- LPC/MUDLIB 自动转换落地
- 热重载内容生态
- 云同步、远程服务、LLM 扩展
- 为迎合未来蓝图而提前拆出大量尚无实现支撑的新目录

## 7. 当前真实实现锚点

以下路径应被视为当前实现的主要锚点，后续开发优先在这些入口上扩展或重构，而不是凭未来蓝图新建平行结构。

| 子系统 | 当前锚点 |
|:---|:---|
| GUI 主入口 | [src/gui/main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py) |
| Qt 调度 | [src/engine/events/qt_scheduler.py](/D:/My_Projects/MUD_Python/src/engine/events/qt_scheduler.py) |
| 事件后端 | [src/engine/events/backends.py](/D:/My_Projects/MUD_Python/src/engine/events/backends.py) |
| 命令系统 | [src/engine/commands/command.py](/D:/My_Projects/MUD_Python/src/engine/commands/command.py) |
| 角色系统 | [src/game/typeclasses/character.py](/D:/My_Projects/MUD_Python/src/game/typeclasses/character.py) |
| 房间系统 | [src/game/typeclasses/room.py](/D:/My_Projects/MUD_Python/src/game/typeclasses/room.py) |
| 世界加载 | [src/game/world/loader.py](/D:/My_Projects/MUD_Python/src/game/world/loader.py) |
| 寻路系统 | [src/game/world/pathfinding.py](/D:/My_Projects/MUD_Python/src/game/world/pathfinding.py) |

如果设计文档中出现 `panels/`、`themes/`、`save/`、`area.py`、`menpai.py`、`internal_power.py` 等路径，但当前树中尚不存在，应将其理解为潜在拆分目标，而不是当前既定结构。

## 8. 架构硬约束

以下约束在当前项目中应视为不可随意突破的规格要求。

### 8.1 技术栈约束

- Python 3.11+
- `asyncio` 作为核心异步机制
- PySide6 作为 GUI 框架
- 单机本地运行，不引入多人网络服务器前提

### 8.2 架构约束

- 保持 GUI 层、Engine 层、Game 层、Data 层的分层边界
- 保持 Typeclass 系统、Command 系统、消息总线、事件调度器的核心地位
- 新功能优先复用现有对象模型和服务，不允许平行造轮子
- 允许重构，但重构必须围绕降低耦合、提升可测性和贴合当前实现，而不是追逐目录理想形态

### 8.3 运行时约束

- 不得在 GUI 主线程引入明显阻塞行为
- 不得破坏现有消息分发和事件调度的时序可靠性
- 性能优化能力应保留，不得因 GUI 接入而退化为串行慢路径

## 9. Phase 4 规格

Phase 4 是当前项目的唯一主战场。其目标不是“做一个漂亮壳子”，而是完成桌面 GUI 对现有游戏内核的稳定承载。

Phase 4 的详细执行规格、集成契约与验收标准，见 [phase4_gui_spec.md](/D:/My_Projects/MUD_Python/docs/specs/phase4_gui_spec.md)。

### 9.1 Phase 4 必须满足

- 游戏可从 GUI 入口启动并进入可交互状态
- 命令输入、执行、结果显示形成完整闭环
- GUI 对消息总线输出具备稳定订阅和展示能力
- 核心游戏状态至少有基础可视化承载
- GUI 层错误不会轻易拖垮主循环

### 9.2 Phase 4 验收重点

- 稳定性高于外观复杂度
- 交互闭环高于高级视觉效果
- 与现有内核兼容高于目录拆分完整度
- 可测试、可调试、可定位问题高于一次性堆功能

### 9.3 Phase 4 允许的演进方式

- 先在 [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py) 上完成骨架，再按需要拆分子模块
- 先打通消息与调度，再细化主题、面板和设置体系
- 先保留最小可用窗口，再逐步增强布局与交互

## 10. Phase 5 与 Phase 6 的前置边界

### 10.1 Phase 5 内容系统

Phase 5 仅在 Phase 4 基本稳定后启动。其重点应是：

- 任务、NPC、地图、门派、武功等内容扩充
- 内容组织方式与数据驱动边界清晰化
- 为未来导入工具预留接口，但不提前把导入工具本身做成当前主线

### 10.2 Phase 6 存档与开发工具

Phase 6 仅在 GUI 主流程稳定后启动。其重点应是：

- 存档/读档一致性
- 版本兼容与迁移策略
- 开发者工具、调试能力、验证能力

在 Phase 6 开始前，文档中出现的 `save/serialization/` 等结构应视为设计蓝图，不应在当前阶段无依据落地。

## 11. 质量门槛

后续实现必须满足以下最低质量要求：

- 新增或修改功能时，应保持现有测试基线不过度退化
- 修改公共行为时，应同步补测试或补文档
- 代码必须遵守 [docs/guides/coding_standards.md](/D:/My_Projects/MUD_Python/docs/guides/coding_standards.md)
- Character 的 mixin 能力扩展必须遵守 [docs/standards/mixin_naming.md](/D:/My_Projects/MUD_Python/docs/standards/mixin_naming.md)
- 不得以“未来重构时再整理”为理由长期保留明显重复或平行实现

推荐验证入口：

1. `make lint`
2. `make test`
3. `make check`
4. 若 `make` 不适用，则使用 `python -m tools.dev ...`
5. Windows 环境可回退到 `py -m tools.dev ...`

## 12. 风险清单

当前项目最需要持续控制的风险包括：

- 文档漂移导致实现与规划混淆
- GUI 与异步调度整合造成事件时序问题
- 存档体系启动后带来的兼容性负担
- 内容系统扩展过早，压垮当前 GUI 主线
- 因未来目录蓝图过多而产生平行文件与重复实现

## 13. 非目标

以下内容不是当前 spec 的交付目标：

- 完整商业化产品打包方案
- 联机 / 多用户 / 服务端部署
- 云端同步与远程存储
- 完整内容转换器
- 完整 Mod / 热重载生态
- 大模型驱动玩法系统

## 14. 使用方式

后续开发、任务分解、审查与 skill 执行建议遵循以下方式：

1. 先用本文档判断当前范围和边界。
2. 再用 [TODO.md](/D:/My_Projects/MUD_Python/TODO.md) 确认当前阶段任务。
3. 再查看真实代码锚点，决定修改位置。
4. 仅在需要详细设计时，再查阅 `docs/` 和 `mud-master` references。

如果将来项目阶段明显推进，应优先更新本文档中的“当前开发基线”“当前版本目标”“真实实现锚点”和“非目标”四个部分。
