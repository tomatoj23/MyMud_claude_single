# 测试套件修复记录

> 修复日期: 2026-03-17
> 基于: `docs/test_suite_analysis.md` 分析报告
> 修改文件: 17 个测试文件 + 1 个测试基类
> 删除文件: 13 个
> 验证结果: 748/751 通过 (3 个预存问题)

---

## 一、合并重复测试文件 (12 组)

### 1.1 Coverage 文件合并 (11 个)

| 源文件 (已删除) | 目标文件 | 合并测试数 |
|----------------|---------|-----------|
| `test_buff_coverage.py` | `test_buff.py` | 2 |
| `test_combat_core_coverage.py` | `test_combat.py` | 45 |
| `test_combat_ai_coverage.py` | `test_combat_ai.py` | 5 |
| `test_combat_calculator_coverage.py` | `test_combat_calculator.py` | 16 |
| `test_config_coverage.py` | `test_config.py` | 18 |
| `test_item_coverage.py` | `test_item.py` | 25 |
| `test_karma_coverage.py` | `test_karma.py` | 12 |
| `test_object_manager_coverage.py` | `test_object_manager.py` | 16 |
| `test_room_coverage.py` | `test_room.py` | 27 |
| `test_typeclass_coverage.py` | `test_typeclass.py` | 23 |
| `test_world_state_coverage.py` | `test_world_state.py` | 48 |

### 1.2 对话系统合并

- `test_dialogue_system.py` → `test_dialogue.py` (12 tests)

### 1.3 删除重复文件

- `test_player_journey_simple.py` — `test_player_journey.py` 的简化重复

---

## 二、修复破损 Fixture (1 处)

### 2.1 test_dialogue_system.py:35

- **问题**: `return mock_npc` 引用未定义变量
- **修复**: `return npc`

---

## 三、修复 asyncio.run() 反模式 (20 处)

将同步测试方法中的 `asyncio.run(xxx)` 转换为 `async def` + `await xxx` + `@pytest.mark.asyncio`

| 文件 | 修复数 |
|------|-------|
| `test_buff.py` | 13 |
| `test_quest.py` | 5 |
| `test_typeclass.py` | 2 |

---

## 四、加强弱断言 (9 处)

### 4.1 移除无意义断言

| 文件 | 行 | 旧断言 | 新断言 |
|------|---|--------|--------|
| `test_quest.py` | 355 | `"1/3" in ....__str__() or True` | `obj["current"] == 1` |
| `test_room.py` | 220 | `"出口" in desc or True` | `isinstance(desc, str)` + `len(desc) > 0` |
| `test_chaos_architecture.py` | 163 | `isinstance(..., object)` | `... is not None` |
| `test_chaos_architecture.py` | 188 | `valid is False or valid is True` | `isinstance(valid, bool)` + `isinstance(msg, str) or msg is None` |
| `test_chaos_architecture.py` | 244 | `isinstance(errors, list)` 仅 | 增加 `err is not None` 检查 |

### 4.2 加强单独 `is not None` 断言

| 文件 | 行 | 修改 |
|------|---|------|
| `test_commands.py` | 620 | 增加 `hasattr(cmdset, 'match')` |
| `test_dynamic_cmdset.py` | 77, 99, 119 | 增加 `hasattr(cmdset, 'match')` |

---

## 五、修复合并导入问题 (6 个文件)

| 文件 | 缺失导入 |
|------|---------|
| `test_combat.py` | `MagicMock` |
| `test_dialogue.py` | `AsyncMock`, `MagicMock` |
| `test_typeclass.py` | `PropertyMock`; `mock.patch` → `patch` |
| `test_config.py` | `os`, `MagicMock`, `Mock`, `patch`, `ConfigFileHandler` |
| `test_room.py` | `Character` |
| `test_item.py` | (fixture 修复，见下) |

---

## 六、修复 MockManager 缺失方法 (4 处)

`get_contents_sync()` 方法缺失导致大量测试失败。

| 文件 | 位置 |
|------|------|
| `tests/base.py` | 共享 MockManager |
| `tests/unit/test_room.py` | 两个 MockManager 类 |
| `tests/unit/test_item.py` | MockManager + character fixture |

**修复方式**: 为所有 MockManager 添加 `get_contents_sync()` 方法:
```python
def get_contents_sync(self, obj_id):
    return [
        obj for obj in self._cache.values()
        if getattr(getattr(obj, '_db_model', None), 'location_id', None) == obj_id
    ]
```

`test_item.py` 的 `TestItemCanPickup.character` fixture 额外添加:
```python
mock_manager.get_contents_sync = Mock(return_value=[])
```

---

## 七、验证结果

```
751 collected, 748 passed, 3 failed
```

### 3 个失败均为预存问题:

| 测试 | 原因 | 类型 |
|------|------|------|
| `test_room.py::TestRoomDesc::test_at_desc_contains_room_name` | Windows 控制台中文编码 | 环境问题 |
| `test_config.py::TestConfigManagerEnvironment::test_detect_environment_frozen` | 单例状态泄漏 (仅批量运行时) | 测试隔离 |
| `test_combat_ai.py::TestCombatAI::test_ai_decide_with_targets_no_moves` | 单例状态泄漏 (仅批量运行时) | 测试隔离 |

后两个在单独运行时通过。

---

## 八、文件变更清单

### 删除 (13 个)

| # | 文件 |
|---|------|
| 1 | `tests/unit/test_buff_coverage.py` |
| 2 | `tests/unit/test_combat_core_coverage.py` |
| 3 | `tests/unit/test_combat_ai_coverage.py` |
| 4 | `tests/unit/test_combat_calculator_coverage.py` |
| 5 | `tests/unit/test_config_coverage.py` |
| 6 | `tests/unit/test_item_coverage.py` |
| 7 | `tests/unit/test_karma_coverage.py` |
| 8 | `tests/unit/test_object_manager_coverage.py` |
| 9 | `tests/unit/test_room_coverage.py` |
| 10 | `tests/unit/test_typeclass_coverage.py` |
| 11 | `tests/unit/test_world_state_coverage.py` |
| 12 | `tests/unit/test_dialogue_system.py` |
| 13 | `tests/integration/test_player_journey_simple.py` |

### 修改 (18 个)

| # | 文件 | 修改类型 |
|---|------|---------|
| 1 | `tests/base.py` | MockManager 添加 get_contents_sync |
| 2 | `tests/unit/test_buff.py` | 合并 + asyncio 修复 + 导入 |
| 3 | `tests/unit/test_combat.py` | 合并 + 导入 |
| 4 | `tests/unit/test_combat_ai.py` | 合并 |
| 5 | `tests/unit/test_combat_calculator.py` | 合并 |
| 6 | `tests/unit/test_commands.py` | 加强断言 |
| 7 | `tests/unit/test_config.py` | 合并 + 导入 |
| 8 | `tests/unit/test_dialogue.py` | 合并 + 导入 |
| 9 | `tests/unit/test_dynamic_cmdset.py` | 加强断言 |
| 10 | `tests/unit/test_item.py` | 合并 + MockManager 修复 |
| 11 | `tests/unit/test_karma.py` | 合并 |
| 12 | `tests/unit/test_object_manager.py` | 合并 |
| 13 | `tests/unit/test_quest.py` | asyncio 修复 + 弱断言修复 |
| 14 | `tests/unit/test_room.py` | 合并 + MockManager 修复 + 导入 + 弱断言 |
| 15 | `tests/unit/test_typeclass.py` | 合并 + asyncio 修复 + 导入 |
| 16 | `tests/unit/test_world_state.py` | 合并 |
| 17 | `tests/integration/test_chaos_architecture.py` | 弱断言修复 |
