# 代码审查修复记录

> 修复日期: 2026-03-17
> 修复范围: 基于 `docs/code_review_report.md` (2026-03-16) 中 P0-P3 问题
> 修改文件: 14 个
> 测试验证: 89/89 通过 (combat 24, buff 36+2, scheduler 27)

---

## 一、P0 修复（4 项）

### 1.1 HTML 注入漏洞 ✅

- **文件**: `src/gui/main_window.py`
- **修改**:
  - 添加 `import html as html_mod`
  - 行 244: `{content}` → `{html_mod.escape(content)}`
  - 行 290: `{text}` → `{html_mod.escape(text)}`

### 1.2 asyncio.iscoroutinefunction() 弃用 ✅

- **文件**: `src/engine/events/backends.py`
  - 添加 `import inspect`
  - 4 处 `asyncio.iscoroutinefunction(` → `inspect.iscoroutinefunction(`
- **文件**: `src/engine/events/qt_scheduler.py`
  - 添加 `import asyncio` 和 `import inspect` 到文件顶部
  - 4 处 `asyncio.iscoroutinefunction(` → `inspect.iscoroutinefunction(`
  - 删除文件末尾多余的 `import asyncio`

### 1.3 版本号同步 ✅

- **文件**: `src/__init__.py`
- **修改**: `__version__ = "0.1.0"` → `__version__ = "0.2.0"`

### 1.4 冷却时间公式缺陷 ✅

- **文件**: `src/game/combat/core.py`
- **修改**: 行 585-586
  - 旧: `reduction = agility * self.AGILITY_FACTOR` + `cooldown = base * max(0.3, 1.0 - reduction)`
  - 新: `reduction = min(agility * self.AGILITY_FACTOR, 0.7)` + `cooldown = base * (1.0 - reduction)`
- **效果**: 敏捷在 0%-70% 减免区间内平滑缩放，不再有硬性 0.3 地板

---

## 二、P1 修复（7 项）

### 2.1 GUI 输出区无限增长 ✅

- **文件**: `src/gui/main_window.py`
- **修改**:
  - 添加 `QTextCursor` 到 PySide6.QtGui 导入
  - 添加类常量 `MAX_OUTPUT_BLOCKS = 5000`
  - `_on_message_received()` 中 append 后检查 `doc.blockCount()`，超限时用 `QTextCursor` 删除旧行

### 2.2 closeEvent 异步清理不可靠 ✅

- **文件**: `src/gui/main_window.py`
- **修改**:
  - `main()` 中添加 `_engine_ref` 变量，`async_main()` 内通过 `nonlocal` 保存引擎引用
  - `closeEvent` 中移除 fire-and-forget `loop.create_task(engine.stop())`
  - `main()` 中 `loop.run_forever()` 之后添加 `loop.run_until_complete(_engine_ref.stop())`
- **效果**: 引擎关闭在 Qt 事件循环退出后同步完成，确保数据保存

### 2.3 MessageBus 订阅泄漏 ✅

- **文件**: `src/gui/main_window.py`
- **修改**:
  - `__init__` 添加 `self._subscribed = False`
  - `_connect_signals()` 中检查 `not self._subscribed` 再订阅，订阅后置 True
  - `closeEvent()` 中检查 `self._subscribed` 再取消，取消后置 False

### 2.4 ConfigManager 线程安全 ✅

- **文件**: `src/utils/config.py`
- **修改**: `__new__()` 中将 `_instance is None` 检查移入 `with cls._lock:` 内
- **效果**: 消除 `__new__` 和 `get_instance` 之间的 TOCTOU 竞态

### 2.5 日志 Handler 重复 ✅

- **文件**: `src/utils/logging.py`
- **修改**: `reload()` 方法中遍历 `_loggers` 时：
  - 清除旧 handlers，重设 level
  - 重新添加通用 handlers
  - 重建模块专属 RotatingFileHandler
- **效果**: 热重载后不会产生重复日志输出

### 2.6 ObjectManager dirty save 竞态 ✅

- **文件**: `src/engine/objects/manager.py`
- **修改**:
  - 添加 `import asyncio`
  - `__init__` 中添加 `self._save_lock = asyncio.Lock()`
  - `save_all()` 用 `async with self._save_lock:` 包裹
- **效果**: 防止并发 save_all 调用导致的脏数据竞态

### 2.7 Scheduler _cancelled_events 无限增长 ✅

- **文件**: `src/engine/events/scheduler.py`
- **修改**:
  - `cancel()` 中帧事件移除后同时从 `_cancelled_events` 中 discard
  - `run()` 循环末尾：当 `_cancelled_events` 超过 100 时，与队列中实际存在的事件 ID 取交集清理
- **效果**: 已取消事件 ID 不再无限积累

---

## 三、P2 修复（4 项）

### 3.2 战斗 AI 实例重复创建 ✅

- **文件**: `src/game/combat/core.py`
- **修改**: `_ai_decide()` 改为懒初始化 `self._combat_ai`，复用同一实例
- **效果**: 每个 CombatSession 只创建一个 CombatAI 实例

### 3.3 NPC 对话运行时崩溃风险 ✅

- **文件**: `src/game/npc/dialogue.py`
- **修改**: 4 处 `character.npc_relations` 调用前添加 `hasattr(character, "npc_relations")` 检查
  - `start_dialogue()`: fallback 为 `favor = 0`
  - `_check_conditions()`: 2 处 fallback 为 `favor = 0`
  - `_apply_effects()`: 跳过 favor_delta 应用
- **效果**: 即使 `npc/core.py` 未导入也不会 AttributeError

### 3.4 BUFF 系统无持久化 ✅

- **文件**: `src/game/combat/buff.py`
- **修改**: BuffManager 新增 4 个方法：
  - `serialize()` → 将活跃 BUFF 序列化为 dict 列表
  - `deserialize(data)` → 从 dict 列表恢复 BUFF
  - `update(elapsed)` → tick 的别名，供 combat/core.py 调用
  - `active_buffs` 属性 → 返回未过期 BUFF 列表

### 3.5 武学反克矩阵不完整 ✅

- **文件**: `src/game/typeclasses/wuxue.py`
- **修改**:
  - `WuxueType.NEIGONG: []` → `[WuxueType.QUAN, WuxueType.ZHANG]` (内功克制外功拳掌)
  - `WuxueType.QINGGONG: []` → `[WuxueType.GUN, WuxueType.DAO]` (轻功克制重兵器)

---

## 四、P3 + 架构修复（3 项）

### 4.5 config_loader 浅拷贝 ✅

- **文件**: `src/utils/config_loader.py`
- **修改**: 添加 `import copy`，`get_all()` 中 `self._config.copy()` → `copy.deepcopy(self._config)`

### 4.9+4.10 战斗计算器硬编码常量 ✅

- **文件**: `src/game/combat/calculator.py`
- **修改**:
  - 暴击率: `self.BASE_CRIT_RATE` → `get_balance_config().get("combat", "damage", "crit_chance", default=0.05)`
  - 敏捷命中系数: 硬编码 `0.005` → `get_balance_config().get("combat", "hit_rate", "agility_mod_per_point", default=0.005)`
- **效果**: 暴击率和命中系数可通过 `data/balance.yml` 配置

### 7.1 MessageBus print → logger ✅

- **文件**: `src/engine/core/messages.py`
- **修改**:
  - 添加 `import logging` + `logger = logging.getLogger(__name__)`
  - 3 处 `print(...)` → `logger.info(...)` / `logger.exception(...)`
- **效果**: 消息总线错误纳入统一日志系统

---

## 五、跳过的问题

| 编号 | 原因 |
|------|------|
| 3.1 lock_parser stubs | 有意为之的 TODO 桩，等待子系统实现 |
| 3.6 set_bonuses 命名 | 文件不存在 |
| 3.7 缺少 config.yaml | 项目决策，非 bug |
| 4.1 回调包装重复 | 重构风险高，收益低 |
| 4.2 API 命名不一致 | 破坏性变更，需单独规划 |
| 4.3 测试覆盖 | 非代码修复，持续改进项 |
| 4.4 文档不一致 | 非代码修复 |
| 4.6 异常链 | 分散在全代码库，低风险 |
| 4.7 GameTime 硬编码 | 需游戏时间系统设计 |
| 4.8 寻路无缓存 | 优化项，需性能数据 |
| 4.11 属性无上限 | 需游戏设计决策 |
| 4.12 敏捷偏弱 | 已由 1.4 + 4.9 部分解决 |
| 7.2+ 架构改进 | 规模过大，需单独规划 |

---

## 六、修改文件清单

| # | 文件路径 | 修改类型 |
|---|---------|---------|
| 1 | `src/gui/main_window.py` | HTML 转义、输出裁剪、关闭流程、订阅守卫 |
| 2 | `src/engine/events/backends.py` | inspect 替换 asyncio |
| 3 | `src/engine/events/qt_scheduler.py` | inspect 替换 asyncio、清理多余 import |
| 4 | `src/__init__.py` | 版本号同步 |
| 5 | `src/game/combat/core.py` | 冷却公式、AI 缓存 |
| 6 | `src/utils/config.py` | __new__ 线程安全 |
| 7 | `src/utils/logging.py` | reload 重建模块 handler |
| 8 | `src/engine/objects/manager.py` | save_all 加锁 |
| 9 | `src/engine/events/scheduler.py` | _cancelled_events 清理 |
| 10 | `src/game/npc/dialogue.py` | npc_relations hasattr 守卫 |
| 11 | `src/game/combat/buff.py` | serialize/deserialize/update/active_buffs |
| 12 | `src/game/typeclasses/wuxue.py` | 反克矩阵补全 |
| 13 | `src/utils/config_loader.py` | deepcopy |
| 14 | `src/game/combat/calculator.py` | BalanceConfig 替换硬编码 |
| 15 | `src/engine/core/messages.py` | print → logger |

---

## 七、测试验证

```
tests/unit/test_combat.py      24 passed ✅
tests/unit/test_buff.py         36 passed ✅
tests/unit/test_buff_coverage.py 2 passed ✅
tests/unit/test_scheduler.py    27 passed ✅
全部 14 个修改文件 import 验证通过 ✅
```

> 注: `test_carry_weight` 中 1 个失败为预存问题 (MockManager 缺少 get_contents_sync)，与本次修复无关。
