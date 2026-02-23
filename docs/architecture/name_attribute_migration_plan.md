# 为 Character 添加 name 属性的全面规划

> 本文档详细规划为 Character 类添加 `name` 属性的实施方案，包括现状分析、设计决策、影响范围、执行步骤和风险评估。

**规划日期**: 2026-02-23  
**规划版本**: v1.0  
**状态**: 待审核

---

## 目录

- [一、问题现状](#一问题现状)
- [二、设计决策](#二设计决策)
- [三、影响范围分析](#三影响范围分析)
- [四、详细修改步骤](#四详细修改步骤)
- [五、完整 .key 使用情况分析](#五完整-key-使用情况分析)
- [六、数据迁移策略](#六数据迁移策略)
- [七、风险与缓解](#七风险与缓解)
- [八、工作量估计](#八工作量估计)
- [九、建议执行范围](#九建议执行范围)
- [十、确认清单](#十确认清单)

---

## 一、问题现状

### 1.1 当前状态

| 现状 | 说明 |
|:---|:---|
| `TypeclassBase` 只有 `key` 属性 | 作为对象的唯一标识符 |
| 战斗系统临时改为使用 `.key` | 显示在战斗日志中（临时修复） |
| 测试中使用 Mock 对象 | 给 `char.name` 赋值，实际该属性不存在 |

### 1.2 核心问题

`key` 是机器标识符（如 `"npc_merchant_001"`），不适合直接显示给玩家。战斗日志显示内部ID会破坏游戏沉浸感。

### 1.3 之前的临时修复

之前为快速修复测试失败，将战斗系统中的 `character.name` 改为 `character.key`。这是一个技术债务，需要彻底解决。

---

## 二、设计决策

### 2.1 语义定义

| 属性 | 用途 | 约束 | 示例 |
|:---|:---|:---|:---|
| **`key`** | 机器唯一标识 | 全局唯一、不可变、用于查找 | `"npc_blacksmith_wang"` |
| **`name`** | 人类显示名称 | 可重复、可修改、用于展示 | `"王铁匠"` |

### 2.2 数据存储方案

**选择**: `name` 存储在 `attributes` JSON 字段中，不修改数据库表结构

```json
{
    "name": "王铁匠",
    "level": 10,
    "status": {...}
}
```

**理由**:
- ✅ 无需数据库迁移
- ✅ 与现有属性系统一致
- ✅ 支持动态修改

### 2.3 默认值策略

```python
@property
def name(self) -> str:
    """角色显示名称，默认为 key。"""
    return self.db.get("name") or self.key
```

- 现有对象无 `name` 时，返回 `key` 作为回退
- 确保向后兼容

---

## 三、影响范围分析

### 3.1 需要修改的文件（7个）

| 序号 | 文件 | 修改内容 | 风险等级 |
|:---:|:---|:---|:---:|
| 1 | `src/game/typeclasses/character.py` | 添加 `name` 属性和 getter/setter | 🟢 低 |
| 2 | `src/game/combat/core.py` | 战斗日志从 `.key` 改回 `.name` | 🟢 低 |
| 3 | `src/game/typeclasses/room.py` | 房间显示使用 `name` | 🟡 中 |
| 4 | `src/game/typeclasses/item.py` | 物品显示使用 `name` | 🟡 中 |
| 5 | `src/game/typeclasses/equipment.py` | 装备显示使用 `name` | 🟡 中 |
| 6 | `src/engine/commands/default.py` | 命令输出使用 `name` | 🟡 中 |
| 7 | `src/game/npc/core.py` | NPC 显示使用 `name` | 🟡 中 |

### 3.2 需要更新的测试（3个文件）

| 文件 | 更新内容 |
|:---|:---|
| `tests/unit/test_combat_core_coverage.py` | 将 `enemy_char.key` 改为 `enemy_char.name` |
| `tests/integration/test_player_journey_simple.py` | 验证战斗日志显示 `name` |
| `tests/integration/test_phase2_game_systems.py` | 验证完整战斗场景使用 `name` |

### 3.3 不需要修改的文件

- `TypeclassBase.key` 属性 - 保持不变，继续使用
- `ObjectManager` - 继续使用 `key` 进行查找
- `Command` 类的 `key` - 命令标识符，与角色无关
- `Buff.key` - BUFF标识符，保持不变
- `Move.name` / `Kungfu.name` - 已有 `name` 属性，无需修改

---

## 四、详细修改步骤

### 步骤 1：添加 `name` 属性到 Character 类

**文件**: `src/game/typeclasses/character.py`

**添加代码**:

```python
@property
def name(self) -> str:
    """角色显示名称，默认为 key。"""
    return self.db.get("name") or self.key

@name.setter
def name(self, value: str) -> None:
    """设置角色显示名称。"""
    self.db.set("name", value)
```

**位置**: 在 `typeclass_path` 之后，第一个属性之前

**依赖**: 无

---

### 步骤 2：修改战斗系统使用 `name`

**文件**: `src/game/combat/core.py`

**修改位置**（5处）:

| 行号 | 当前代码 | 修改后 |
|:---:|:---|:---|
| 261 | `target.key` | `target.name` |
| 271 | `target.key` | `target.name` |
| 345 | `combatant.character.key` | `combatant.character.name` |
| 365 | `combatant.character.key` | `combatant.character.name` |
| 368 | `target.key` | `target.name` |
| 370 | `combatant.character.key` 和 `target.key` | `.name` |

---

### 步骤 3：修改其他显示位置（可选但建议）

**文件**: `src/game/typeclasses/room.py`（第199行）

```python
# 当前
desc = f"\n{self.key}\n"
# 改为
desc = f"\n{self.name or self.key}\n"
```

**文件**: `src/game/typeclasses/item.py`（第123行）

```python
# 当前
desc = f"{self.key}\n"
# 改为
desc = f"{self.name or self.key}\n"
```

**文件**: `src/game/typeclasses/equipment.py`（第210行）

```python
# 当前
desc = f"[{self.quality_name}] {self.key}\n"
# 改为
desc = f"[{self.quality_name}] {self.name or self.key}\n"
```

**文件**: `src/engine/commands/default.py`（多行）

```python
# 类似修改：.key -> .name or .key
```

---

### 步骤 4：更新测试

**文件**: `tests/unit/test_combat_core_coverage.py`（第669行）

```python
# 当前
assert f"{enemy_char.key} 使用了物品" in session.log
# 改为
assert f"{enemy_char.name} 使用了物品" in session.log
```

---

### 步骤 5：添加测试验证 `name` 属性

**新建或修改**: `tests/unit/test_character.py`

```python
def test_name_default(self):
    """测试 name 默认值为 key。"""
    char = Character(mock_manager, mock_db_model)
    assert char.name == char.key

def test_name_custom(self):
    """测试自定义 name。"""
    char = Character(mock_manager, mock_db_model)
    char.name = "王铁匠"
    assert char.name == "王铁匠"
    assert char.key != "王铁匠"  # key 不变
```

---

## 五、完整 .key 使用情况分析

### 5.1 分类总览

| 类别 | 数量 | 处理方式 |
|:---|:---:|:---|
| 用于显示（改 `name`） | 9处 | 逐步替换 |
| 用于标识/查找（保持 `key`） | 17处 | **不修改** |
| 特殊情况 | 1处 | 优化回退逻辑 |

### 5.2 详细使用情况

#### 5.2.1 用于显示（建议改为 `name`）— 9处

| 文件 | 行号 | 当前代码 | 用途 | 优先级 |
|:---|:---:|:---|:---|:---:|
| `item.py` | 123 | `f"{self.key}\n"` | 物品描述显示 | P2 |
| `equipment.py` | 210 | `f"[{self.quality_name}] {self.key}"` | 装备描述显示 | P1 |
| `equipment.py` | 332 | `f"装备成功：{item.key}"` | 装备成功消息 | P1 |
| `equipment.py` | 359 | `f"卸下成功：{current.key}"` | 卸下成功消息 | P1 |
| `room.py` | 199 | `f"\n{self.key}\n"` | 房间名称显示 | P1 |
| `room.py` | 212 | `[item.key for item in items]` | 房间内物品列表 | P1 |
| `room.py` | 219 | `[c.key for c in others]` | 房间内角色列表 | P1 |
| `room.py` | 330 | `f" - {self.destination.key}"` | 出口目标显示 | P1 |
| `combat/core.py` | 5处 | `character.key`, `target.key` | 战斗日志显示 | **P0** |

#### 5.2.2 用于标识/查找（保持 `key`）— 17处

这些是作为**机器标识符**使用，**不应该改为 `name`**:

| 文件 | 行号 | 用途 |
|:---|:---:|:---|
| `pathfinding.py` | 131 | 寻路目标比较 `room.key == goal_key` |
| `combat/buff.py` | 48, 123, 138, 238 | BUFF的key标识（Buff类自己的key） |
| `quest/core.py` | 183, 187, 194 | 任务key作为字典键 |
| `npc/dialogue.py` | 251, 256, 312 | 使用 `npc.key` 作为关系字典的键 |
| `npc/core.py` | 165, 175, 185 | 创建NPC时设置key |
| `wuxue.py` | 102, 113, 230, 233, 259, 263, 266, 268 | 武学、招式的key标识 |
| `world/loader.py` | 167, 175 | 字典的 `.keys()` 方法 |
| `reputation.py` | 220, 232 | 字典的 `.keys()` 方法 |
| `world_state.py` | 191 | 字典的 `.keys()` 方法 |
| `dialogue.py` | 146 | 字典的 `.keys()` 方法 |

**关键区分原则**:

```
✅ 应该改 name：显示给玩家看的文本
   - 战斗日志："王铁匠 使用了[打造]"
   - 房间描述："扬州城"
   - 物品名称："精铁剑"

❌ 保持 key：机器内部使用的标识
   - 字典键：active_quests[quest.key]
   - 查找比较：if room.key == goal_key
   - 关系存储：npc_relations[npc.key]
```

#### 5.2.3 特殊情况 — 1处

| 文件 | 行号 | 代码 | 说明 |
|:---|:---:|:---|:---|
| `npc/core.py` | 157 | `return self.dialogue_key or self.key` | 如果没有设置 `dialogue_key`，用 `key` 回退。建议改为 `return self.dialogue_key or self.name or self.key` |

---

## 六、数据迁移策略

### 6.1 现有数据处理

| 场景 | 处理方案 |
|:---|:---|
| 现有对象无 `name` | 返回 `self.key`（通过 `or self.key` 兜底） |
| 创建新对象 | 可同时设置 `key` 和 `name` |
| 改名 | 修改 `name`，`key` 保持不变 |

### 6.2 示例代码

```python
# 创建NPC
npc = await engine.objects.create(
    typeclass_path="src.game.npc.core.NPC",
    key="npc_blacksmith_wang",  # 机器ID
    attributes={
        "name": "王铁匠",  # 显示名
        "npc_type": "merchant"
    }
)

print(npc.key)   # "npc_blacksmith_wang"
print(npc.name)  # "王铁匠"
```

---

## 七、风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|:---|:---:|:---:|:---|
| 遗漏某些 `.key` 使用位置 | 中 | 中 | 全局搜索，逐步替换 |
| 测试失败 | 低 | 中 | 运行完整测试套件，修复断言 |
| 现有存档数据不兼容 | 低 | 低 | `name` 默认为 `key`，向后兼容 |
| 与 `Move.name` 等混淆 | 低 | 低 | 明确区分角色 `name` 和其他 `name` |

### 7.1 回滚方案

如果修改后出现问题：

1. **代码回滚**: Git 回退到修改前
2. **数据恢复**: 无需数据库迁移，无数据损坏风险
3. **紧急修复**: 将 `.name` 改回 `.key` 即可恢复显示

---

## 八、工作量估计

| 任务 | 预计时间 |
|:---|:---:|
| 修改 Character 类 | 10分钟 |
| 修改战斗系统（5处） | 10分钟 |
| 可选：修改其他显示位置（P1级别） | 20分钟 |
| 更新测试 | 15分钟 |
| 运行完整测试验证 | 10分钟 |
| **总计（方案A）** | **约30分钟** |
| **总计（方案B）** | **约1小时** |

---

## 九、建议执行范围

### 方案 A：最小修改（推荐）

- 只执行步骤 1 和 2（Character + 战斗系统）
- 风险最低，达到核心目标
- 其他 `.key` 显示后续逐步优化

**修改文件**:
- `src/game/typeclasses/character.py`
- `src/game/combat/core.py`

### 方案 B：完整修改

- 执行所有步骤（1-5）
- 统一所有显示使用 `name`
- 工作量稍大，但体验更完整

**额外修改文件**:
- `src/game/typeclasses/room.py`
- `src/game/typeclasses/item.py`
- `src/game/typeclasses/equipment.py`
- `src/engine/commands/default.py`
- `src/game/npc/core.py`

---

## 十、确认清单

### 执行前确认

- [ ] 采用方案 A（最小修改）还是方案 B（完整修改）？
- [ ] `name` 存储在 `attributes` 中的方案是否接受？
- [ ] 是否现在就开始执行？

### 执行后验证

- [ ] Character 类新增 `name` 属性通过测试
- [ ] 战斗系统日志显示 `name` 而非 `key`
- [ ] 所有 1329 个测试通过
- [ ] 现有存档数据兼容（显示正常）

---

## 附录：优先级定义

| 优先级 | 说明 | 处理时机 |
|:---:|:---|:---|
| **P0** | 核心功能，影响游戏体验 | 立即处理 |
| **P1** | 主要显示位置，频繁可见 | 当前阶段处理 |
| **P2** | 次要显示，影响较小 | 后续优化 |
| **P3** | 保持现状 | 不修改 |

---

**建议**: 采用**方案 A**（P0级别），只修改 Character 和战斗系统，其他显示优化（P1、P2）可以后续逐步进行。这样风险最低，核心问题（战斗日志显示不友好）得到解决。

---

*文档版本: v1.0*  
*最后更新: 2026-02-23*
