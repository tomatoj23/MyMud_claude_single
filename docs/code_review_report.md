# 代码审查报告

> 审查日期: 2026-03-16
> 审查范围: 全项目代码、文档、测试

---

## 一、严重问题（P0）

### 1.1 HTML 注入漏洞

- 文件: `src/gui/main_window.py:241`
- 问题: `content` 未经 HTML 转义直接拼入 `<span>` 标签，QTextBrowser 会解析其中的 HTML
- 影响: 恶意或意外的标签（如 `<img onerror=...>`）可被执行
- 修复: 使用 `html.escape(content)` 转义后再拼接

```python
# 当前
html = f'<span style="color: {color};">{content}</span>'

# 修复
import html as html_mod
html = f'<span style="color: {color};">{html_mod.escape(content)}</span>'
```

### 1.2 asyncio.iscoroutinefunction() 已弃用

- 文件: `src/engine/events/qt_scheduler.py` (行 119, 143, 171, 230)
- 文件: `src/engine/events/backends.py` (行 112, 136, 212, 241)
- 问题: `asyncio.iscoroutinefunction()` 在 Python 3.14 中已弃用
- 影响: 运行时产生 DeprecationWarning，未来版本将移除
- 修复: 全部替换为 `inspect.iscoroutinefunction()`

### 1.3 版本号不同步

- 文件: `src/__init__.py:7` 为 `"0.1.0"`，`pyproject.toml` 为 `"0.2.0"`
- 修复: 统一为 `"0.2.0"`

### 1.4 冷却时间公式缺陷

- 文件: `src/game/combat/core.py:586`
- 问题: `reduction = agility * AGILITY_FACTOR`，当敏捷足够高时 `1.0 - reduction < 0.3`，被 `max(0.3, ...)` 兜底，导致所有高敏捷角色冷却完全相同
- 影响: 敏捷属性在高数值区间失去区分度
- 建议修复:

```python
reduction = min(agility * self.AGILITY_FACTOR, 0.7)
cooldown = base * (1.0 - reduction)
```

---

## 二、高优先级问题（P1）

### 2.1 GUI 输出区无限增长

- 文件: `src/gui/main_window.py:242`
- 问题: `_output_browser.append(html)` 无上限，长时间运行内存持续膨胀
- 建议: 设置最大行数（如 5000），超出时用 `QTextCursor` 删除旧内容

### 2.2 closeEvent 异步清理不可靠

- 文件: `src/gui/main_window.py` closeEvent 方法
- 问题: `loop.create_task(engine.stop())` 在窗口关闭后 Qt 事件循环可能已退出，task 不一定执行完
- 建议: 在 `main()` 的 shutdown 流程中用 `loop.run_until_complete()` 统一处理

### 2.3 MessageBus 订阅泄漏

- 文件: `src/gui/main_window.py` _connect_signals / closeEvent
- 问题: 订阅仅在 closeEvent 中取消；若窗口因异常销毁，订阅永不清理
- 建议: 在 `destroyed` 信号或 `__del__` 中加保底清理

### 2.4 ConfigManager 线程安全缺口

- 文件: `src/utils/config.py` __init__ 方法
- 问题: `_initialized` 标志在锁外检查，存在 TOCTOU 竞态
- 建议: 将检查移入锁内

### 2.5 日志 Handler 重复添加

- 文件: `src/utils/logging.py` get_logger()
- 问题: 每次调用都添加 handler，多次获取同一 logger 导致日志重复输出
- 建议: 检查 `logger.handlers` 是否已有同类 handler 再添加

### 2.6 ObjectManager dirty save 竞态

- 文件: `src/engine/objects/manager.py` save_all()
- 问题: 遍历 dirty_ids 时，`is_dirty()` 检查和 `save()` 之间其他协程可能修改对象
- 建议: 使用 `asyncio.Lock` 保护，或 save 时做 snapshot

### 2.7 Scheduler _cancelled_events 无限增长

- 文件: `src/engine/events/scheduler.py`
- 问题: `_cancelled_events` 集合只增不减
- 建议: 事件执行后从集合中移除

---

## 三、中优先级问题（P2）

### 3.1 多处模块实现不完整

| 文件 | 未完成内容 |
|------|-----------|
| `src/utils/lock_parser.py` | 所有条件检查均 `return True, ""`，未实际实现 |
| `src/utils/config_loader.py` | 多处 TODO 注释 |
| `src/game/npc/behavior_nodes.py` | MovementController 未完成 |
| `src/game/quest/core.py` | CharacterQuestMixin 截断 |
| `src/game/world/loader.py` | _unload_loop() 未完成 |

### 3.2 战斗系统 AI 实例重复创建

- 文件: `src/game/combat/core.py:236`
- 问题: 每个 tick 为每个 NPC 创建新 `CombatAI()` 实例
- 建议: 缓存 AI 实例或使用单例

### 3.3 NPC 对话系统运行时崩溃

- 文件: `src/game/npc/dialogue.py`
- 问题: `start_dialogue()` 调用 `character.npc_relations.get_favor()`，但 Character 类无此属性
- 影响: 运行时 AttributeError

### 3.4 BUFF 系统无持久化

- 文件: `src/game/combat/buff.py`
- 问题: Buff 仅存于内存，角色重载后丢失
- 建议: 添加序列化/反序列化机制

### 3.5 武学反克矩阵不完整

- 文件: `src/game/typeclasses/wuxue.py:152-161`
- 问题: NEIGONG 和 QINGGONG 的反克列表为空，无法被克制也无法克制其他类型

### 3.6 装备集合奖励命名错误

- 文件: `src/game/combat/set_bonuses.py:116`
- 问题: 变量名 `GAibang_ARMOR_SET` 应为 `GAIBANG_ARMOR_SET`

### 3.7 缺少配置文件

- 项目根目录无 `config.yaml` 或 `config.development.yaml`
- 系统完全依赖硬编码默认值

---

## 四、低优先级问题（P3）

### 4.1 代码重复

- 回调包装逻辑在 `qt_scheduler.py`、`backends.py`、`scheduler.py` 三处重复
- 消息发送在 `Command.msg()`、`MessageHandler.msg()`、`TypeclassBase.msg()` 各自实现

### 4.2 API 命名不一致

- `ObjectManager.load()`（async）和 `get()`（sync）语义易混淆
- Scheduler 参数顺序在父子类间不一致: `schedule(callback, delay)` vs `schedule(delay, callback)`

### 4.3 测试覆盖缺口

- GUI 层仅 10 个测试，覆盖率约 5%
- 缺少数据库边界测试（连接池耗尽、并发写冲突）
- 缺少 `tests/README.md` 测试文档

### 4.4 文档与代码不一致

- 架构文档提到 `ScenePanel`、`CharacterPanel`、`CombatPanel`，但这些组件尚未实现
- `docs/specs/phase4_gui_spec.md` 描述的 panels/themes 目录为空

### 4.5 config_loader 浅拷贝问题

- 文件: `src/utils/config_loader.py` get_all()
- 问题: `self._config.copy()` 仅浅拷贝，嵌套 dict 仍为可变引用
- 建议: 使用 `copy.deepcopy()`

### 4.6 异常链缺失

- 文件: `src/utils/exceptions.py`
- 问题: 异常未使用 `raise ... from e` 模式，丢失原始 traceback 上下文

### 4.7 GameTime 硬编码为真实时间

- 文件: `src/game/npc/behavior_nodes.py:24`
- 问题: 使用 `datetime.now().hour` 而非游戏时间，无法测试且破坏游戏时间推进

### 4.8 寻路无缓存

- 文件: `src/game/world/pathfinding.py`
- 问题: 每次寻路从头计算，无 LRU 缓存
- 影响: 大世界场景下性能问题

### 4.9 战斗命中率公式偏弱

- 文件: `src/game/combat/calculator.py:145-159`
- 问题: 基础 90% 命中率过高，敏捷差异仅 0.5%/点影响
- 影响: 100 点敏捷差距仅 50% 命中率变化，鼓励堆力量而非策略

### 4.10 暴击率硬编码

- 文件: `src/game/combat/calculator.py:38`
- 问题: 5% 基础暴击率无法通过属性或装备提升
- 建议: 暴击率应随属性缩放

### 4.11 角色属性无上限

- 文件: `src/game/typeclasses/character.py`
- 问题: 属性值可无限增长，无最大值限制
- 影响: 潜在的整数溢出或平衡崩坏

### 4.12 敏捷属性偏弱

- 问题: 敏捷影响冷却（最多 30% 减少）和命中（0.5%/点），相比力量/体质收益过低
- 建议: 增加闪避机制或提高敏捷系数

---

## 五、建议修复优先级

| 优先级 | 问题编号 | 预估工作量 |
|--------|---------|-----------|
| 立即修复 | 1.1 HTML 转义 | 5 分钟 |
| 立即修复 | 1.2 iscoroutinefunction | 10 分钟 |
| 立即修复 | 1.3 版本号同步 | 1 分钟 |
| 本周 | 1.4, 2.1-2.7 | 各 30-60 分钟 |
| Phase 5 前 | 3.1-3.7 | 各 1-4 小时 |
| 持续改进 | 4.1-4.12 | 按需处理 |

---

## 六、架构分析

### 6.1 总体架构评估

项目采用三层架构，层间依赖方向正确：

```
GUI (PySide6 + qasync)
  ↓ MessageBus (pub/sub)
Engine (asyncio)
  ↓ SQLAlchemy async
Data (SQLite WAL)
```

- 无循环依赖：Engine 不导入 Game/GUI，Game 不导入 GUI
- GUI → Engine 通过 `engine.process_input()` 发送命令
- Engine → GUI 通过 `MessageBus.emit()` 推送消息
- 层间边界清晰，符合设计意图

### 6.2 Engine 层内部依赖图

```
messages.py (独立)
    ↓
typeclass.py → database/models.py
    ↓
objects/manager.py → typeclass.py, models.py
    ↓
commands/command.py → messages.py
    ↓
commands/cmdset.py → command.py
    ↓
commands/handler.py → cmdset.py, command.py
    ↓
events/scheduler.py (独立)
events/backends.py (独立)
events/qt_scheduler.py → scheduler.py, backends.py
    ↓
core/engine.py → 以上所有模块（编排器）
```

engine.py 是唯一导入多个子系统的模块，作为编排器角色合理。无子系统反向导入 engine.py。

### 6.3 初始化与关闭顺序

初始化顺序（`GameEngine.initialize()`）：
```
1. DatabaseManager.initialize()     — 连接 SQLite，建表
2. ObjectManager.initialize()       — 初始化缓存
3. CommandHandler.initialize()      — 注册默认命令
4. EventScheduler（注入或新建）      — 就绪但未启动
```

关闭顺序（`GameEngine.stop()`）：
```
1. _running = False                 — 停止接受输入
2. 取消 auto-save task
3. ObjectManager.save_all()         — 保存脏对象
4. EventScheduler.stop()            — 取消所有待执行事件
5. DatabaseManager.close()          — 关闭数据库连接
```

问题：
- 关闭时未清理 ObjectManager 缓存（L1/L2），引擎重启后可能残留过期 weakref
- 关闭时未清理 CommandHandler 状态（影响较小，因为无状态）

### 6.4 GUI 启动流程

```
main()
  ├─ QApplication()
  ├─ qasync.QEventLoop(app) → asyncio.set_event_loop()
  └─ async_main()
       ├─ load_config()
       ├─ FlexibleEventScheduler(backend="hybrid")
       ├─ create_engine(config)
       ├─ engine._injected_scheduler = scheduler  ← 访问私有属性
       ├─ engine.initialize()
       ├─ engine.start()
       ├─ _setup_default_session()  ← 创建默认房间+玩家
       ├─ MainWindow(engine)
       │    └─ _connect_signals()  ← 订阅 MessageBus
       ├─ player.message_bus = engine.message_bus  ← 手动接线
       ├─ window.show()
       └─ signals.game_started.emit()
```

问题：
- `engine._injected_scheduler` 访问私有属性，应通过构造函数参数或公开 API
- `player.message_bus = ...` 手动接线，应由引擎自动完成
- 任何步骤失败则整体失败，无回滚机制

### 6.5 GUI ↔ Engine 通信模式

命令流（GUI → Engine）：
```
用户输入 → _on_submit_command()
  → asyncio.ensure_future(_execute_command())
    → engine.process_input(player, text)
      → CommandHandler.handle()
        → Command.execute()
```

消息流（Engine → GUI）：
```
Engine/Game 系统 → MessageBus.emit(message)
  → MainWindow._on_message(message)
    → signals.message_received.emit(type, content)
      → _on_message_received()
        → _output_browser.append(html)
```

问题：
- 命令执行是 fire-and-forget，无直接反馈通道
- `asyncio.ensure_future()` 已弃用（Python 3.10+），应用 `asyncio.create_task()`
- 命令 task 未被追踪，无法取消或等待完成
- 无命令超时机制，挂起的命令会永久阻塞

### 6.6 单例管理

项目中存在以下全局单例：

| 单例 | 位置 | 重置机制 |
|------|------|---------|
| `_global_message_bus` | `messages.py` | `set_message_bus()` 可替换 |
| `_engine` | `engine.py` | 无显式重置方法 |
| `TypeclassMeta.registry` | `typeclass.py` | 类变量，跨测试持久 |
| `ConfigManager` | `config.py` | `reset()` 方法（标注仅测试用） |
| `LoggingManager` | `logging.py` | 无重置机制 |

问题：
- 测试依赖 `reset_singletons` autouse fixture 清理全局状态，属于 workaround
- `TypeclassMeta.registry` 在类定义时自动填充，无法选择性清理
- 建议：为所有单例添加显式 `reset()` 方法，或改用依赖注入

### 6.7 Game 层 Typeclass 扩展模式

```
TypeclassBase (engine)
  ├── Character (game)
  │     ├── CharacterEquipmentMixin  — equipment_* 前缀方法
  │     └── CharacterWuxueMixin      — wuxue_* 前缀方法
  ├── NPC (game)
  │     └── extends Character
  ├── Room (game)
  ├── Item (game)
  └── Equipment (game)
```

MRO 线性，无菱形继承问题。Mixin 通过 `super().__init__(*args, **kwargs)` 协作式继承。

问题：
- Mixin 无显式接口/Protocol 定义，契约仅靠命名约定
- Equipment mixin 缓存失效依赖手动调用 `_equipment_invalidate_cache()`
- Quest mixin（`CharacterQuestMixin`）实现截断，未混入 Character

### 6.8 Game 子系统耦合分析

```
紧耦合（应降低）:
  Combat → Character    直接修改 HP/MP
  NPC → BehaviorTree    直接调用 tick()
  Quest → Character     直接调用方法

松耦合（良好）:
  Game → GUI            仅通过 MessageBus
  Game → Engine         通过接口
  Dialogue → Quest      通过注册表
  Equipment ↔ Wuxue     无依赖
```

关键发现：
- 战斗系统的 `CombatTransaction` 仅做内存快照，非数据库事务，不具备真正的原子性
- Game 层命令实现缺失：`src/game/commands/` 仅有 debug 命令，无玩家操作命令（攻击、移动、对话等）
- MessageBus 在 Game 层使用不足：战斗、NPC、任务系统未主动发送消息到 MessageBus

### 6.9 事件循环与线程模型

```
主线程（唯一线程）:
  Qt 事件循环 ← qasync 桥接 → asyncio 事件循环
    ├─ GUI 事件处理（信号/槽）
    ├─ Engine 异步任务（命令处理、自动保存）
    ├─ Scheduler 事件（QTimer / asyncio.sleep）
    └─ 数据库 I/O（aiosqlite，实际在线程池）
```

优势：单线程模型避免了锁和竞态问题。

风险：
- 长时间运行的引擎操作（大批量保存、复杂寻路）会阻塞 UI 响应
- 无 worker 线程或线程池用于 CPU 密集型任务
- 建议：对耗时操作使用 `loop.run_in_executor()` 卸载到线程池

### 6.10 缓存策略

ObjectManager 三级缓存：

| 层级 | 存储 | 淘汰策略 | 问题 |
|------|------|---------|------|
| L1 | `weakref.ref[TypeclassBase]` | GC 自动回收 | 回收时机不可预测 |
| L2 | `dict[int, ObjectModel]` | 手动 `_invalidate_query_cache()` | 无自动淘汰 |
| Query | `dict[str, (list[int], float)]` | TTL 5秒 | 任何对象变更清空全部缓存（过于激进） |

Query 缓存失效过于粗粒度：`_invalidate_query_cache()` 无论传入什么对象都清空整个缓存。应实现基于查询参数的选择性失效。

### 6.11 Qt 信号映射

GameStateSignals 定义了 9 个信号：

| 信号 | 是否使用 | 连接目标 |
|------|---------|---------|
| `character_hp_changed(int, int)` | 是 | `_on_hp_changed` |
| `character_mp_changed(int, int)` | 是 | `_on_mp_changed` |
| `character_exp_changed(int, int)` | 否 | 未连接 |
| `character_level_changed(int)` | 否 | 未连接 |
| `room_changed(str, str)` | 是 | `_on_room_changed` |
| `message_received(str, str)` | 是 | `_on_message_received` |
| `equipment_changed()` | 否 | 未连接 |
| `game_started()` | 是 | `_on_game_started` |
| `game_stopped()` | 是 | `_on_game_stopped` |

3 个信号（exp、level、equipment）已定义但从未使用，属于死代码。

### 6.12 错误传播策略

当前项目中存在 5 种不同的错误处理模式，缺乏统一策略：

| 子系统 | 模式 | 问题 |
|--------|------|------|
| Database | 抛出 `DatabaseError` | 无重试逻辑 |
| ObjectManager | 捕获并返回 None/空 | 调用方无法区分"无结果"和"出错" |
| Command | 捕获并返回 `CommandResult(False, msg)` | 良好 |
| Scheduler | 捕获并 `logger.exception()` | 用户不可见 |
| MessageBus | 捕获并 `print()` | 未使用 logger，不一致 |

建议统一为：
- 数据库错误：重试 + 指数退避
- 对象加载错误：日志 + 降级（当前已实现）
- 命令错误：返回错误结果给用户（当前已实现）
- 事件错误：日志 + 继续（当前已实现，但应通知用户）
- MessageBus 错误：改用 logger

---

## 七、架构改进建议

### 7.1 高优先级

1. **统一错误处理策略**：MessageBus 中的 `print()` 改为 `logger`，为所有子系统建立一致的错误传播规范

2. **补全 Game 命令层**：实现玩家操作命令（attack、move、talk、equip 等），这是 Game 层与 Engine 层的关键桥梁

3. **Game 层集成 MessageBus**：战斗、NPC、任务系统应主动通过 MessageBus 发送消息，否则 GUI 无法显示实时更新

4. **GUI 关闭流程加固**：在 `main()` 的 shutdown 路径中用 `loop.run_until_complete(engine.stop())` 确保引擎完全停止

5. **命令 task 追踪与超时**：用 dict 追踪活跃命令 task，添加超时取消机制

### 7.2 中优先级

6. **Scheduler 注入改为公开 API**：`engine._injected_scheduler` → 构造函数参数或 `engine.set_scheduler()`

7. **Query 缓存选择性失效**：基于对象 ID / location_id 做精确失效，而非清空全部

8. **长操作卸载到线程池**：对批量保存、寻路等耗时操作使用 `loop.run_in_executor()`

9. **CombatTransaction 改为数据库级事务**：当前内存快照不具备真正原子性

10. **清理未使用的 Qt 信号**：移除 `character_exp_changed`、`character_level_changed`、`equipment_changed` 或实现其功能

### 7.3 低优先级

11. **单例改依赖注入**：逐步将 ConfigManager、LoggingManager 等改为通过构造函数注入

12. **Mixin 添加 Protocol 定义**：为 Equipment/Wuxue mixin 定义显式接口

13. **添加引擎生命周期事件**：Engine 应在 start/stop 时通过 MessageBus 发送系统消息

14. **GUI 输出区虚拟化**：实现滚动缓冲区，限制最大行数

15. **命令队列**：支持命令排队和宏，而非立即执行

---
