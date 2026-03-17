# Phase 4 GUI 子规格说明

> 适用阶段：阶段四 GUI 客户端开发
>
> 文档状态：Active
>
> 编制日期：2026-03-11

## 1. 文档目的

本文档用于细化 [当前项目规格说明](/D:/My_Projects/MUD_Python/docs/specs/current_project_spec.md) 中的 Phase 4 范围，定义 GUI 客户端阶段的具体目标、实现边界、集成契约、验收标准与测试要求。

本文档是当前 GUI 开发的执行规格，不是视觉设计稿，也不是未来完整 UI 架构蓝图。

对应的可执行任务清单见 [phase4_gui_task_list.md](/D:/My_Projects/MUD_Python/docs/specs/phase4_gui_task_list.md)。

## 2. 当前阶段定位

Phase 4 的目标不是重新设计引擎，而是在不破坏既有核心系统的前提下，为单机版金庸武侠文字 MUD 补齐一个稳定、可用、可扩展的桌面 GUI 壳层。

GUI 层必须服务于现有引擎，而不是独立演化成第二套游戏运行框架。

## 3. Phase 4 信息源优先级

本阶段开发、评审与验收时，信息源优先级如下：

1. [TODO.md](/D:/My_Projects/MUD_Python/TODO.md)
2. [docs/tech_debt_report.md](/D:/My_Projects/MUD_Python/docs/tech_debt_report.md)
3. [current_project_spec.md](/D:/My_Projects/MUD_Python/docs/specs/current_project_spec.md)
4. [phase4.md](/D:/My_Projects/MUD_Python/.agents/skills/mud-master/references/phase4.md)
5. [gui.md](/D:/My_Projects/MUD_Python/.agents/skills/mud-master/references/gui.md)
6. 归档文档与前瞻设计文档

如果文档与真实代码冲突，以当前代码锚点为准。

## 4. 当前真实基线

截至 2026-03-15，GUI 相关现状如下：

- GUI 主窗口已实现完整启动闭环，包含 `main()` 入口、qasync 事件循环集成、引擎初始化与默认会话创建
- GUI 已具备输出区（QTextBrowser）、输入区（QLineEdit + QPushButton）、状态区（HP/MP 进度条、房间名、状态标签）
- MessageBus 已接入 GUI，消息按类型着色显示（error/combat 红色、dialogue 蓝色、notify 绿色、system 灰色）
- 输入框已接通 `GameEngine.process_input()`，支持回车和按钮提交，执行中禁用输入防重复
- 关闭窗口时优雅停止引擎、取消 MessageBus 订阅、状态栏提示"正在关闭..."
- 引擎支持调度器注入，GUI 模式使用 `FlexibleEventScheduler(backend="hybrid")`，`start()/stop()` 自动检测 async/sync
- GUI smoke tests（6 个）和集成测试（4 个）已建立，覆盖窗口创建、消息转发、输入执行、关闭停止引擎
- `GUIManager` 持有玩家强引用，通过 `_setup_default_session()` 创建默认房间和玩家

当前尚未完成的部分（Backlog）：

- 规划中的 `panels/`、`themes/`、`async_bridge.py` 等结构尚未成为当前真实目录
- 右侧面板（地图/任务）尚未填充内容
- 主题系统尚未实现
- 存档/读档 GUI 尚未实现

## 5. 当前明确问题

以下问题已在 Phase 4 MVP 中解决（2026-03-15）：

- ~~[pyproject.toml](/D:/My_Projects/MUD_Python/pyproject.toml#L45) 暴露了 `jinyong-mud = src.gui.main_window:main`，但当前 [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py) 中没有 `main()` 启动入口~~ → 已补齐 `main()` 入口
- ~~`make run` 当前指向 `python -m src.gui.main_window`，但模块尚未形成完整启动路径~~ → 已形成完整启动路径
- ~~GUI 目前主要是布局骨架，尚未体现输入、输出、状态、关闭流程的完整协作~~ → 四条链路已打通
- ~~测试报告中 `gui/` 覆盖仍然接近 5%，说明 GUI 尚未进入稳定交付状态~~ → 已建立 10 个 GUI 测试（6 smoke + 4 integration）

## 6. Phase 4 目标

### 6.1 必须达成的目标

- 提供可运行的桌面 GUI 启动入口
- 建立 `QApplication / qasync / GameEngine / MainWindow` 的稳定生命周期
- 建立玩家输入到 `GameEngine.process_input()` 的可用链路
- 建立 `MessageBus` 到 GUI 输出区与状态区的订阅更新链路
- 支持基础角色状态、房间信息、系统消息的可视化
- 关闭窗口时可优雅停止引擎，避免明显资源泄露或脏状态

### 6.2 应优先达成的目标

- 将主窗口中的职责边界整理清楚
- 为后续面板拆分保留扩展点，但不提前过度拆分
- 提供最小主题/样式切换骨架
- 提供基础错误提示和日志可见性

### 6.3 可以延后的目标

- 复杂主题系统
- 高级快捷键体系
- 丰富动画与视觉打磨
- 可插拔面板生态
- GUI 内建调试面板

## 7. 用户闭环规格

Phase 4 至少需要保证以下用户路径成立。

### 7.1 启动闭环

1. 用户执行 `make run` 或 `jinyong-mud`
2. GUI 应成功创建 Qt 应用实例与事件循环
3. 引擎初始化并进入运行状态
4. 主窗口展示，应用进入可交互状态

### 7.2 输入闭环

1. 用户在 GUI 输入框中输入命令
2. GUI 将输入转发给引擎输入入口
3. 命令执行结果通过消息总线或显式结果返回进入 GUI
4. 输出区显示反馈，必要时刷新状态区或房间区

### 7.3 状态闭环

1. 引擎或对象状态发生变化
2. 状态变更经消息总线或显式更新接口传到 GUI
3. GUI 中至少同步以下内容：角色状态、房间名称/描述、普通消息流

### 7.4 退出闭环

1. 用户关闭窗口
2. GUI 停止新输入
3. 引擎执行优雅停止
4. 相关任务、定时器、数据库资源按既有引擎流程关闭

## 8. 集成契约

### 8.1 启动契约

Phase 4 必须补齐一个真实可运行的 `main()` 或等价启动入口，其职责包括：

- 创建 `QApplication`
- 建立 `qasync` 事件循环桥接
- 创建并初始化 `GameEngine`
- 创建 `MainWindow`
- 将引擎、消息总线、GUI 信号与窗口生命周期连接起来
- 进入 Qt 事件循环

如果未来需要拆出 `async_bridge.py`，也必须先以当前入口跑通，再考虑拆分。

### 8.2 主窗口契约

[MainWindow](/D:/My_Projects/MUD_Python/src/gui/main_window.py#L48) 当前应继续作为主窗口壳层，至少承担以下职责：

- 管理窗口级布局
- 承载输出区、输入区、状态区的最小组件
- 连接 GUI 信号与引擎/消息总线
- 处理窗口关闭生命周期

主窗口不应直接承担大量业务规则计算。

### 8.3 输入契约

GUI 输入层必须以 [GameEngine.process_input](/D:/My_Projects/MUD_Python/src/engine/core/engine.py#L197) 作为统一入口，不允许在 GUI 层重复实现命令解析逻辑。

### 8.4 输出契约

命令结果和系统事件应优先通过 [MessageBus](/D:/My_Projects/MUD_Python/src/engine/core/messages.py#L129) 输出，再映射为 GUI 展示行为。

GUI 至少应处理以下消息类别：

- `system`
- `info`
- `error`
- `combat`
- `status`
- `prompt`

### 8.5 调度契约

GUI 模式下的调度必须与 Qt 事件循环兼容。应优先复用 [FlexibleEventScheduler](/D:/My_Projects/MUD_Python/src/engine/events/qt_scheduler.py#L18) 及其后端机制，而不是在 GUI 层另起新的定时调度体系。

### 8.6 配置契约

GUI 的窗口尺寸、主题、字体等配置应优先来自 [GuiConfig](/D:/My_Projects/MUD_Python/src/utils/config.py#L58)，不应散落在多个硬编码位置。

## 9. 模块与文件策略

当前阶段优先使用以下真实文件作为开发入口：

- [main_window.py](/D:/My_Projects/MUD_Python/src/gui/main_window.py)
- [engine.py](/D:/My_Projects/MUD_Python/src/engine/core/engine.py)
- [messages.py](/D:/My_Projects/MUD_Python/src/engine/core/messages.py)
- [qt_scheduler.py](/D:/My_Projects/MUD_Python/src/engine/events/qt_scheduler.py)
- [backends.py](/D:/My_Projects/MUD_Python/src/engine/events/backends.py)
- [config.py](/D:/My_Projects/MUD_Python/src/utils/config.py)

只有在以下条件满足时，才建议从 `main_window.py` 继续拆分：

- 单文件职责已明显超出维护阈值
- 新模块边界已由真实调用关系支撑
- 拆分不会引入平行实现或假目录

因此，`panels/`、`themes/manager.py`、`async_bridge.py` 在当前阶段属于可选演进路径，而不是先验必须目录。

## 10. 非目标

以下内容不属于当前 Phase 4 必交内容：

- 完整视觉设计系统
- 内容编辑器或调试器 GUI
- 存档管理界面
- Mod/热重载界面
- 多窗口复杂工作台
- 针对未来内容系统的提前 UI 预埋

## 11. 验收标准

### 11.1 Must Have

- 应用存在真实可运行入口
- 主窗口可显示并保持稳定
- 输入命令后能看到输出反馈
- 基础状态信息可见
- 消息总线可驱动 GUI 更新
- 窗口关闭时引擎能优雅停止

### 11.2 Should Have

- 主要界面区域职责清晰
- 错误信息有明确反馈
- 主题与样式有最小配置能力
- GUI 关键路径具备基础测试

### 11.3 Nice to Have

- 更细的面板拆分
- 快捷键与交互增强
- 更丰富的提示与状态显示

## 12. 测试要求

Phase 4 完成前，应至少补齐以下测试层次：

- 主窗口创建 smoke test
- GUIManager 生命周期测试
- MessageBus 到 GUI 信号的订阅转发测试
- 输入提交到 `GameEngine.process_input()` 的集成测试
- 关闭窗口时的引擎停止行为测试
- 若使用 Qt 调度后端，则应补至少一个 Qt 兼容调度测试

验证建议顺序：

1. `make lint`
2. `make test`
3. 必要时执行 GUI 相关定向测试
4. 手工验证启动、输入、输出、退出四条主路径

## 13. 推荐实施顺序

1. 补齐真实启动入口与事件循环桥接
2. 让 `MainWindow` 接通 `GameEngine` 与 `MessageBus`
3. 补齐最小输入区、输出区、状态区闭环
4. 补 GUI 生命周期与消息转发测试
5. 再根据真实复杂度决定是否拆分 `panels/` 或 `themes/`

## 14. 主要风险

- Qt 事件循环与 `asyncio` 生命周期归属不清，导致任务泄漏或退出异常
- 过早按蓝图拆分 GUI 目录，导致当前实现碎片化
- 在 GUI 层复制命令解析或业务状态逻辑，造成双轨实现
- 缺少 GUI 测试，导致后续改动很难回归
- 启动入口与打包入口不一致，造成“看起来能运行、实际无法启动”的假完成状态

## 15. 维护规则

当 Phase 4 进度显著推进时，应优先更新以下内容：

- 当前真实基线
- 当前明确问题
- 验收标准
- 推荐实施顺序

如果未来 Phase 4 完成并进入 Phase 5，应将本文档状态调整为已完成，并把 GUI 当前真实结构回写到总 spec。
