# Phase 4 GUI 执行任务清单

> 对应规格： [phase4_gui_spec.md](/D:/My_Projects/MUD_Python/docs/specs/phase4_gui_spec.md)
>
> 文档状态：Active
>
> 编制日期：2026-03-11

## 1. 文档目的

本文档将 [Phase 4 GUI 子规格说明](/D:/My_Projects/MUD_Python/docs/specs/phase4_gui_spec.md) 落为可执行任务清单，供后续实现、评审和阶段推进直接使用。

本清单遵循以下原则：

- 当前代码优先于未来蓝图目录
- 先打通启动、输入、输出、退出四条主链路
- 先建立 GUI MVP，再考虑大规模面板拆分和视觉增强
- 每个任务都必须有明确的完成定义和验证方式

## 2. 当前约束与前置判断

执行本清单前，应先接受以下事实：

- 当前 GUI 主入口只有 [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [pyproject.toml](/D:/My_Projects/MUD_Python/pyproject.toml#L45) 已声明 `jinyong-mud = src.gui.main_window:main`，但当前还没有 `main()`
- 引擎当前在 [engine.py](/D:/My_Projects/MUD_Python/src/engine/core/engine.py#L140) 中仍实例化基础调度器导入路径，尚未真正切到 Qt 兼容实现
- 命令输入链路需要有效 `caller`，因此 GUI 启动时必须明确“当前玩家/房间”的装配策略
- 当前没有现成的 `tests/gui/` 测试基线

## 3. 执行顺序总览

| 里程碑 | 目标 | 任务编号 | 完成标志 |
|:---|:---|:---|:---|
| M1 | 打通 GUI 启动与调度生命周期 | T4-GUI-001 ~ T4-GUI-003 | 应用可稳定启动并显示窗口 |
| M2 | 打通输入、输出、状态三条交互链 | T4-GUI-004 ~ T4-GUI-007 | 可在 GUI 中输入命令并看到反馈 |
| M3 | 建立 GUI 测试和回归基线 | T4-GUI-008 ~ T4-GUI-010 | GUI 关键路径可验证、可回归 |
| Backlog | 延后项，不阻塞 Phase 4 MVP | B4-GUI-001 ~ B4-GUI-008 | 仅在 M1-M3 稳定后再做 |

## 4. 任务清单

### M1. GUI 启动与生命周期

#### [x] T4-GUI-001 补齐真实 GUI 启动入口

**优先级**: Blocker
**依赖**: 无
**完成日期**: 2026-03-15

**目标**:
让 `python -m src.gui.main_window` 与 `jinyong-mud` 都能走到真实可运行的 GUI 启动路径。

**主要修改文件**:

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [pyproject.toml](/D:/My_Projects/MUD_Python/pyproject.toml)
- [Makefile](/D:/My_Projects/MUD_Python/Makefile)

**任务内容**:

- 在 `src.gui.main_window` 中补齐 `main()` 或等价启动入口
- 创建 `QApplication`
- 接入 `qasync` 事件循环
- 初始化 `GameEngine`
- 通过 `GUIManager` 创建并展示 `MainWindow`
- 保证模块入口、脚本入口和 `make run` 的行为一致

**完成定义**:

- 模块存在真实入口函数
- 控制台脚本入口不再指向缺失函数
- 本地启动后能看到主窗口，而不是导入成功但无界面

**验证方式**:

- `make run`
- 必要时 `python -m src.gui.main_window`
- 手工确认窗口出现且无启动即崩溃

#### [x] T4-GUI-002 统一 GUI 模式下的调度器生命周期

**优先级**: Blocker
**依赖**: T4-GUI-001
**完成日期**: 2026-03-15

**目标**:
让 GUI 模式真正使用 Qt 兼容调度能力，而不是停留在”代码已存在但引擎未接入”的状态。

**主要修改文件**:

- [engine.py](/D:/My_Projects/MUD_Python/src/engine/core/engine.py)
- [scheduler.py](/D:/My_Projects/MUD_Python/src/engine/events/scheduler.py)
- [qt_scheduler.py](/D:/My_Projects/MUD_Python/src/engine/events/qt_scheduler.py)
- [backends.py](/D:/My_Projects/MUD_Python/src/engine/events/backends.py)

**任务内容**:

- 明确 GUI 模式下调度器应选择的实现和后端类型
- 消除当前 `EventScheduler.start()/stop()` 与 `FlexibleEventScheduler.start()/stop()` 生命周期接口不一致的问题
- 允许引擎在 GUI 启动时显式使用 Qt 兼容后端
- 明确非 GUI 模式与 GUI 模式的调度器选择策略

**完成定义**:

- 引擎在 GUI 模式下不再依赖错误的同步生命周期假设
- 调度器启动和停止路径在 GUI 关闭时可正常完成
- 不出现“窗口能打开，但定时/帧/周期事件无法正常协作”的隐性故障

**验证方式**:

- GUI 启动和关闭手工验证
- 增加至少一个调度器生命周期测试
- `make test`

#### [x] T4-GUI-003 定义 GUI 会话上下文与默认玩家装配

**优先级**: High
**依赖**: T4-GUI-001, T4-GUI-002
**完成日期**: 2026-03-15

**目标**:
为 GUI 输入提供一个有效 `caller`，避免窗口可见但命令根本没有执行主体。

**主要修改文件**:

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [engine.py](/D:/My_Projects/MUD_Python/src/engine/core/engine.py)
- 参考 [test_cross_phase_integration.py](/D:/My_Projects/MUD_Python/tests/integration/test_cross_phase_integration.py#L24)
- [test_engine.py](/D:/My_Projects/MUD_Python/tests/integration/test_engine.py#L453)

**任务内容**:

- 明确 GUI 启动时如何创建或加载默认房间与玩家对象
- 在 `GUIManager` 或主窗口层保存当前玩家上下文
- 确保 `process_input(caller, text, session)` 有合法 `caller`
- 定义 session 是否需要最小包装对象；如不需要，也要明确记录

**完成定义**:

- GUI 启动后至少可对默认玩家执行 `look`、`inventory` 等基础命令
- 当前玩家上下文在主窗口生命周期中可持续使用

**验证方式**:

- 手工输入 `look`
- 手工输入 `inventory`
- 至少一个集成测试覆盖 GUI 启动后的默认输入路径

### M2. 输入、输出、状态闭环

#### [x] T4-GUI-004 在主窗口内补齐最小输出区、输入区、状态区

**优先级**: High
**依赖**: T4-GUI-003
**完成日期**: 2026-03-15

**目标**:
先在当前 [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py) 内完成最小可用界面，不强求立即拆分 `panels/`。

**主要修改文件**:

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [config.py](/D:/My_Projects/MUD_Python/src/utils/config.py)

**任务内容**:

- 输出区：用于显示系统消息、命令回显和普通文本
- 输入区：输入框与发送动作
- 状态区：至少展示角色 HP/MP、当前房间名或描述摘要
- 使用 `GuiConfig` 控制窗口尺寸、字体、基础显示参数

**完成定义**:

- 主窗口不再只有空布局骨架
- 用户能明确看到”输出在哪里、输入在哪里、状态在哪里”
- 不依赖未来 `panels/` 目录也能完成 MVP 界面

**验证方式**:

- 手工启动 GUI
- 观察三块区域是否存在并可见

#### [x] T4-GUI-005 将 MessageBus 订阅接入 GUI 显示

**优先级**: High
**依赖**: T4-GUI-004
**完成日期**: 2026-03-15

**目标**:
让命令结果和系统事件能稳定进入 GUI，而不是只停留在控制台或返回值里。

**主要修改文件**:

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [messages.py](/D:/My_Projects/MUD_Python/src/engine/core/messages.py)
- 如有必要，补最小适配层但不要重复造消息系统

**任务内容**:

- 订阅 `MessageBus` 文本消息
- 订阅状态更新消息
- 将消息类型映射到 GUI 输出区和状态区
- 至少覆盖 `system`、`info`、`error`、`combat`、`status`、`prompt`

**完成定义**:

- 命令执行后的反馈能显示在 GUI 中
- 错误消息与普通消息能被区分显示
- 状态更新能触发 GUI 刷新

**验证方式**:

- 手工执行至少 3 条基础命令
- 模拟错误命令，确认错误反馈可见
- 测试 `MessageBus -> GUI` 转发

#### [x] T4-GUI-006 将输入组件接到 `GameEngine.process_input()`

**优先级**: High
**依赖**: T4-GUI-004, T4-GUI-005
**完成日期**: 2026-03-15

**目标**:
形成真正的命令输入闭环，而不是只有输入框界面。

**主要修改文件**:

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [engine.py](/D:/My_Projects/MUD_Python/src/engine/core/engine.py#L219)
- [handler.py](/D:/My_Projects/MUD_Python/src/engine/commands/handler.py)

**任务内容**:

- 回车和发送动作都能触发命令提交
- 将文本发送到 `GameEngine.process_input()`
- 对空输入、重复点击、执行中状态做最小保护
- 明确命令结果是依靠 `MessageBus`、返回值还是两者共同更新 UI

**完成定义**:

- GUI 输入 `look` 后能收到可见反馈
- GUI 输入未知命令后能看到错误反馈
- 输入过程中不会因为重复触发造成明显异常

**验证方式**:

- 手工验证 `look`
- 手工验证 `inventory`
- 手工验证未知命令
- 集成测试覆盖一次成功命令和一次失败命令

#### [x] T4-GUI-007 完善关闭流程、异常反馈与最小运行状态提示

**优先级**: Medium
**依赖**: T4-GUI-006
**完成日期**: 2026-03-15

**目标**:
避免 GUI 进入”能开不能关、出错无反馈”的状态。

**主要修改文件**:

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py#L149)
- [engine.py](/D:/My_Projects/MUD_Python/src/engine/core/engine.py)

**任务内容**:

- 关闭窗口时禁止新输入
- 优雅停止引擎与相关后台任务
- 为初始化失败、命令异常、引擎停止提供最小可见反馈
- 如保留状态栏，应在这里提供运行状态显示

**完成定义**:

- 关闭窗口不会留下明显悬挂任务
- 启动失败或命令异常至少能在 GUI 中提示
- 退出路径与手工关闭路径一致

**验证方式**:

- 手工关闭窗口
- 模拟异常输入或初始化失败场景
- `make test`

### M3. 测试与文档回归

#### [x] T4-GUI-008 建立 GUI smoke test 基线

**优先级**: High
**依赖**: T4-GUI-004
**完成日期**: 2026-03-15

**目标**:
为 GUI 建立第一批最小自动化回归能力。

**主要修改文件**:

- 新建 `tests/unit/test_gui_smoke.py`
- 参考 [test_engine.py](/D:/My_Projects/MUD_Python/tests/integration/test_engine.py)

**任务内容**:

- 主窗口可创建 smoke test
- GUIManager 可创建主窗口 test
- 基本信号对象存在 test

**完成定义**:

- 项目中首次形成 GUI 自动化测试入口
- GUI 基础对象创建不再完全依赖手测

**验证方式**:

- `make test`
- 定向执行 GUI 相关测试

#### [x] T4-GUI-009 建立关键交互集成测试

**优先级**: High
**依赖**: T4-GUI-005, T4-GUI-006, T4-GUI-007
**完成日期**: 2026-03-15

**目标**:
覆盖 GUI 当前最容易回归的三条主路径：消息转发、输入执行、退出关闭。

**主要修改文件**:

- 新建 `tests/integration/test_gui_integration.py`
- 如有必要，少量辅助夹具

**任务内容**:

- `MessageBus -> GUI` 订阅转发测试
- GUI 输入提交到 `process_input()` 的测试
- 窗口关闭触发引擎停止的测试
- 如已接通 Qt 后端，再补一个调度器协作测试

**完成定义**:

- GUI 关键路径不再只有手工验证
- 后续重构主窗口时有最基本保护网

**验证方式**:

- `make test`
- 定向运行 GUI 测试集合

#### [x] T4-GUI-010 回写文档与阶段进度

**优先级**: Medium
**依赖**: T4-GUI-001 ~ T4-GUI-009

**目标**:
在代码落地后，确保 spec、README、TODO 与实际进度重新对齐。

**主要修改文件**:

- [phase4_gui_spec.md](/D:/My_Projects/MUD_Python/docs/specs/phase4_gui_spec.md)
- [current_project_spec.md](/D:/My_Projects/MUD_Python/docs/specs/current_project_spec.md)
- [TODO.md](/D:/My_Projects/MUD_Python/TODO.md)
- [docs/README.md](/D:/My_Projects/MUD_Python/docs/README.md)

**任务内容**:

- 更新当前真实基线
- 更新已完成任务状态
- 记录 GUI 真实入口、真实测试路径和真实文件结构
- 删除或降级明显过时的“未来目录即当前目录”表述

**完成定义**:

- 文档与代码状态重新一致
- 后续不会因为旧计划条目把实现带偏

**验证方式**:

- 人工审阅文档一致性
- `git diff` 检查变更范围

## 5. 建议实施批次

### 批次 A：先打通可运行骨架

- T4-GUI-001
- T4-GUI-002
- T4-GUI-003

**阶段目标**:
窗口可启动，且引擎、调度器、当前玩家上下文都已就位。

### 批次 B：打通最小交互闭环

- T4-GUI-004
- T4-GUI-005
- T4-GUI-006
- T4-GUI-007

**阶段目标**:
能在 GUI 中输入命令、看到输出、观察状态、正常退出。

### 批次 C：补测试和回归基线

- T4-GUI-008
- T4-GUI-009
- T4-GUI-010

**阶段目标**:
GUI 不再只能靠手测推进，且文档状态与实现状态一致。

## 6. 当前不建议提前做的事项

以下条目来自旧的 GUI 计划或长期蓝图，但不应阻塞当前 Phase 4 MVP：

#### [ ] B4-GUI-001 菜单栏完整化
#### [ ] B4-GUI-002 主题切换与自定义主题系统
#### [ ] B4-GUI-003 `panels/` 目录全面拆分
#### [ ] B4-GUI-004 输入历史与自动补全
#### [ ] B4-GUI-005 角色/战斗/对话/日志多面板体系
#### [ ] B4-GUI-006 快捷键体系
#### [ ] B4-GUI-007 拖拽交互
#### [ ] B4-GUI-008 响应式布局与复杂自适应

这些事项只有在 M1-M3 已稳定完成后，才建议重新评估是否进入当前迭代。

## 7. 统一验收口径

Phase 4 MVP 可以视为“进入可交付状态”，至少要满足以下条件：

- GUI 有真实启动入口
- GUI 启动后有默认可交互玩家上下文
- 输入 `look`/`inventory` 有反馈
- 未知命令有错误提示
- 消息总线驱动 GUI 更新
- 关闭窗口时引擎可优雅停止
- 至少存在 GUI smoke test 和关键交互测试

## 8. 推荐验证顺序

1. `make lint`
2. `make test`
3. 手工验证启动链路
4. 手工验证输入/输出链路
5. 手工验证关闭链路

## 9. 维护规则

当某个任务完成时，应同步更新：

- 本任务清单中的勾选状态
- [phase4_gui_spec.md](/D:/My_Projects/MUD_Python/docs/specs/phase4_gui_spec.md)
- 必要时更新 [TODO.md](/D:/My_Projects/MUD_Python/TODO.md)

如果 GUI 真实结构与当前清单假设发生偏移，应优先修正清单，不要继续依赖过期任务描述。