# 技术债务报告

> 金庸武侠MUD项目技术债务追踪

**生成日期**: 2026-02-23  
**统计范围**: `src/` 源代码目录

---

## 📊 债务概览

| 类别 | 数量 | 优先级 | 影响 |
|:---|:---:|:---:|:---|
| TODO/FIXME 注释 | 26 | P2 | 功能缺失 |
| NotImplementedError | 1 | P1 | 功能未实现 |
| 抽象方法 | 5+ | P2 | 需子类实现 |
| Mock/测试债务 | 2 | P3 | 测试质量 |
| **总计** | **34** | - | - |

---

## 🔴 高优先级债务 (P1)

### 1. 命令系统未实现方法
**文件**: `src/engine/commands/command.py:110`  
**问题**: `execute()` 方法抛出 NotImplementedError  
**影响**: 所有具体命令必须实现该方法，否则运行时崩溃  
**建议**: 这是设计模式（模板方法），保持现状，确保子类实现

```python
def execute(self) -> CommandResult:
    raise NotImplementedError(f"命令 {self.key} 未实现 execute 方法")
```

---

## 🟡 中优先级债务 (P2)

### 2. NPC行为树 TODO (8个)
**文件**: `src/game/npc/behavior_tree.py`

| 行号 | TODO内容 | 功能模块 |
|:---:|:---|:---|
| 219 | 实现移动到巡逻点的逻辑 | AI移动 |
| 238 | 检查当前位置与出生点的距离 | 巡逻范围 |
| 259 | 实现随机移动逻辑 | 空闲行为 |
| 270 | 检查NPC是否在战斗中 | 战斗状态 |
| 281 | 从游戏时间系统获取当前时间 | 时间系统 |
| 293 | 检查范围内是否有玩家 | 感知系统 |
| 313 | 检查是否离家太远 | 活动范围 |

**建议**: 需要实现完整的NPC AI行为系统

### 3. NPC对话系统 TODO (4个)
**文件**: `src/game/npc/dialogue.py`

| 行号 | TODO内容 | 功能 |
|:---:|:---|:---|
| 281 | 检查背包 | 物品条件检查 |
| 318 | 给予物品 | 物品转移 |
| 341 | 解锁任务 | 任务系统集成 |
| 356 | 记录到世界状态 | 世界状态管理 |

### 4. NPC派系关系 TODO (2个)
**文件**: `src/game/npc/reputation.py:257-262`

```python
# TODO: 实现派系关系
def get_faction_reputation(self, faction: str) -> int:
    pass
    
def modify_faction_reputation(self, faction: str, delta: int) -> None:
    pass
```

**功能**: 实现江湖门派/势力之间的派系关系系统

### 5. 物品系统 TODO
**文件**: `src/game/typeclasses/item.py:113`

```python
def can_pickup(self, character: "Character") -> tuple[bool, str]:
    # TODO: 实现负重检查
    return True, ""
```

**功能**: 实现角色负重系统

### 6. 房间出口锁 TODO
**文件**: `src/game/typeclasses/room.py:348`

```python
async def can_pass(self, character: "Character") -> tuple[bool, str]:
    # TODO: 解析锁字符串，检查条件
```

**功能**: 实现出口锁/钥匙系统

### 7. 装备套装效果 TODO
**文件**: `src/game/typeclasses/equipment.py:417`

```python
def _calculate_set_bonus(self, equipped_items: list) -> dict:
    # TODO: 根据套装件数计算效果
```

**功能**: 实现套装属性加成计算

### 8. 武学系统 TODO
**文件**: `src/game/typeclasses/wuxue.py:298`

```python
# TODO: 通过kungfu_key获取Kungfu对象
```

**功能**: 实现武学查找/缓存机制

### 9. 战斗计算器 TODO (2个)
**文件**: `src/game/combat/calculator.py`

| 行号 | TODO内容 |
|:---:|:---|
| 95 | 获取防御者当前使用的武学类型 |
| 154 | 从招式数据读取命中修正 |

### 10. 战斗AI TODO (2个)
**文件**: `src/game/combat/ai.py`

| 行号 | TODO内容 |
|:---:|:---|
| 165 | 实现基于克制关系的智能选择 |
| 194 | 根据实际招式属性选择 |

### 11. 战斗系统 TODO (2个)
**文件**: `src/game/combat/core.py`

| 行号 | TODO内容 | 功能 |
|:---:|:---|:---|
| 169 | 优化为按实际时间结算 | 实时战斗 |
| 283 | 实现内功施法 | 内功系统 |

### 12. 任务系统 TODO (2个)
**文件**: `src/game/quest/core.py`

| 行号 | TODO内容 |
|:---:|:---|
| 346 | 实现物品发放 |
| 351 | 实现武学奖励 |

### 13. 命令系统 TODO (2个)
**文件**: `src/engine/commands/handler.py`

| 行号 | TODO内容 |
|:---:|:---|
| 85 | 从调用者位置获取可用命令 |
| 86 | 从调用者自身获取可用命令 |

**功能**: 实现动态命令集合（根据位置和状态）

### 14. 命令锁检查 TODO
**文件**: `src/engine/commands/command.py:85`

```python
# TODO: 实现完整的锁检查逻辑
```

**功能**: 实现命令执行的条件检查系统

---

## 🟢 低优先级债务 (P3)

### 15. GUI未完成方法
**文件**: `src/gui/main_window.py`

```python
def setup_menus(self) -> None:  # pass
    pass

def closeEvent(self, event) -> None:  # pass
    pass
```

**说明**: GUI框架已搭建，具体功能待实现

### 16. 事件调度后端抽象方法
**文件**: `src/engine/events/backends.py`

这些是抽象基类方法，需要具体后端实现（Qt/Tkinter/...）

### 17. 单元测试中的Mock问题
**文件**: `tests/unit/test_character.py`

```python
# test_default_status - 期望(100,100)实际(275,275)
# test_add_exp_with_level_up - 未升级
```

**影响**: 2个测试失败（预存问题，与name属性无关）

---

## 📈 债务分布

### 按模块分布
```
npc/          14 项 (41%)  ← 最多
combat/        7 项 (21%)
typeclasses/   5 项 (15%)
commands/      4 项 (12%)
quest/         2 项 (6%)
```

### 按类型分布
```
AI/行为        9 项 (26%)
系统功能       8 项 (24%)
计算/公式      6 项 (18%)
检查/验证      5 项 (15%)
未完成代码     4 项 (12%)
```

---

## 🎯 清偿建议

### 短期 (1-2周)
1. **实现负重系统** (`item.py:113`)
   - 影响：核心游戏体验
   - 工作量：2-3小时

2. **实现出口锁系统** (`room.py:348`)
   - 影响：地图设计灵活性
   - 工作量：3-4小时

### 中期 (2-4周)
3. **完成NPC AI行为树** (8个TODO)
   - 影响：NPC智能程度
   - 工作量：1-2周

4. **实现战斗计算完善** (4个TODO)
   - 影响：战斗平衡性
   - 工作量：2-3天

### 长期 (1-2月)
5. **派系关系系统**
6. **任务奖励系统**
7. **内功施法系统**

---

## 🔍 隐藏债务

### 潜在性能问题
- **对象缓存**: 未实现LRU淘汰机制，长时间运行可能OOM
- **战斗日志**: 无限增长，需要定期清理
- **事件调度器**: 未限制最大事件数

### 设计债务
- **类型安全**: 多处使用 `Any` 类型，失去类型检查
- **错误处理**: 部分异常处理过于宽泛
- **状态管理**: 角色状态分散，缺乏统一状态机

### 测试债务
- **覆盖率**: 部分边界条件未覆盖
- **并发测试**: 缺乏多线程/协程并发测试
- **性能测试**: 缺乏负载测试

---

## 📋 追踪清单

- [ ] 创建GitHub Issues追踪每项TODO
- [ ] 设定优先级标签 (P1/P2/P3)
- [ ] 分配开发者
- [ ] 设定完成期限
- [ ] 代码审查确保债务不增加

---

*最后更新: 2026-02-23*
