"""世界状态管理测试 - 达到100%覆盖率.

覆盖 world_state.py 的所有方法.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.quest.world_state import WorldStateManager


class TestWorldStateManagerInit:
    """测试 WorldStateManager 初始化."""

    def test_init_with_engine(self):
        """测试带引擎初始化."""
        engine = Mock()
        manager = WorldStateManager(engine)
        
        assert manager.engine is engine
        assert manager._states == {}

    def test_init_without_engine(self):
        """测试不带引擎初始化."""
        manager = WorldStateManager()
        
        assert manager.engine is None
        assert manager._states == {}


class TestWorldStateManagerBasic:
    """测试 WorldStateManager 基础操作."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    def test_get_existing(self, manager):
        """测试获取已存在的状态."""
        manager._states["test_key"] = "test_value"
        
        result = manager.get("test_key")
        
        assert result == "test_value"

    def test_get_nonexistent(self, manager):
        """测试获取不存在的状态."""
        result = manager.get("nonexistent")
        
        assert result is None

    def test_get_with_default(self, manager):
        """测试获取不存在的状态时使用默认值."""
        result = manager.get("nonexistent", default="default_value")
        
        assert result == "default_value"

    def test_set(self, manager):
        """测试设置状态."""
        manager.set("key1", "value1")
        
        assert manager._states["key1"] == "value1"

    def test_has_existing(self, manager):
        """测试检查已存在的状态."""
        manager._states["key1"] = "value1"
        
        assert manager.has("key1") is True

    def test_has_nonexistent(self, manager):
        """测试检查不存在的状态."""
        assert manager.has("nonexistent") is False

    def test_delete_existing(self, manager):
        """测试删除已存在的状态."""
        manager._states["key1"] = "value1"
        
        result = manager.delete("key1")
        
        assert result is True
        assert "key1" not in manager._states

    def test_delete_nonexistent(self, manager):
        """测试删除不存在的状态."""
        result = manager.delete("nonexistent")
        
        assert result is False


class TestWorldStateManagerIncrement:
    """测试 WorldStateManager 增量操作."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    def test_increment_new_key(self, manager):
        """测试增量新键."""
        result = manager.increment("counter")
        
        assert result == 1
        assert manager._states["counter"] == 1

    def test_increment_existing(self, manager):
        """测试增量已存在的键."""
        manager._states["counter"] = 5
        
        result = manager.increment("counter")
        
        assert result == 6
        assert manager._states["counter"] == 6

    def test_increment_with_amount(self, manager):
        """测试指定增量."""
        manager._states["counter"] = 10
        
        result = manager.increment("counter", amount=5)
        
        assert result == 15

    def test_increment_with_negative_amount(self, manager):
        """测试负增量."""
        manager._states["counter"] = 10
        
        result = manager.increment("counter", amount=-3)
        
        assert result == 7

    def test_increment_non_numeric_existing(self, manager):
        """测试增量非数字现有值."""
        manager._states["counter"] = "not_a_number"
        
        result = manager.increment("counter", amount=5)
        
        assert result == 5
        assert manager._states["counter"] == 5


class TestWorldStateManagerToggle:
    """测试 WorldStateManager 切换操作."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    def test_toggle_new_key(self, manager):
        """测试切换新键."""
        result = manager.toggle("flag")
        
        assert result is True
        assert manager._states["flag"] is True

    def test_toggle_false_to_true(self, manager):
        """测试从 False 切换到 True."""
        manager._states["flag"] = False
        
        result = manager.toggle("flag")
        
        assert result is True
        assert manager._states["flag"] is True

    def test_toggle_true_to_false(self, manager):
        """测试从 True 切换到 False."""
        manager._states["flag"] = True
        
        result = manager.toggle("flag")
        
        assert result is False
        assert manager._states["flag"] is False

    def test_toggle_truthy_to_false(self, manager):
        """测试从真值切换到 False."""
        manager._states["flag"] = "truthy_string"
        
        result = manager.toggle("flag")
        
        assert result is False


class TestWorldStateManagerPlayerChoice:
    """测试 WorldStateManager 玩家选择相关方法."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    @pytest.fixture
    def character(self):
        """创建模拟角色."""
        char = Mock()
        char.id = "char_123"
        return char

    def test_on_player_choice(self, manager, character):
        """测试记录玩家选择."""
        manager.on_player_choice(character, "choice_1", "option_a")
        
        key = "choice_char_123_choice_1"
        assert key in manager._states
        assert manager._states[key]["choice"] == "option_a"
        assert manager._states[key]["character_id"] == "char_123"

    def test_get_player_choice_existing(self, manager, character):
        """测试获取已存在的选择."""
        key = "choice_char_123_choice_1"
        manager._states[key] = {"choice": "option_b", "character_id": "char_123"}
        
        result = manager.get_player_choice(character, "choice_1")
        
        assert result == "option_b"

    def test_get_player_choice_nonexistent(self, manager, character):
        """测试获取不存在的选择."""
        result = manager.get_player_choice(character, "nonexistent")
        
        assert result is None

    def test_get_player_choice_not_dict(self, manager, character):
        """测试获取非字典类型的选择数据."""
        key = "choice_char_123_choice_1"
        manager._states[key] = "not_a_dict"
        
        result = manager.get_player_choice(character, "choice_1")
        
        assert result is None

    def test_has_made_choice_true(self, manager, character):
        """测试检查已做出的选择."""
        key = "choice_char_123_choice_1"
        manager._states[key] = {"choice": "option_a"}
        
        result = manager.has_made_choice(character, "choice_1")
        
        assert result is True

    def test_has_made_choice_false(self, manager, character):
        """测试检查未做出的选择."""
        result = manager.has_made_choice(character, "not_made")
        
        assert result is False


class TestWorldStateManagerQuestFlag:
    """测试 WorldStateManager 任务标志相关方法."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    def test_set_quest_flag(self, manager):
        """测试设置任务标志."""
        manager.set_quest_flag("quest_1", "started", True)
        
        assert manager._states["quest_quest_1_started"] is True

    def test_set_quest_flag_with_custom_value(self, manager):
        """测试设置任务标志为自定义值."""
        manager.set_quest_flag("quest_1", "progress", 50)
        
        assert manager._states["quest_quest_1_progress"] == 50

    def test_get_quest_flag_existing(self, manager):
        """测试获取已存在的任务标志."""
        manager._states["quest_quest_1_completed"] = True
        
        result = manager.get_quest_flag("quest_1", "completed")
        
        assert result is True

    def test_get_quest_flag_nonexistent(self, manager):
        """测试获取不存在的任务标志."""
        result = manager.get_quest_flag("quest_1", "nonexistent")
        
        assert result is None

    def test_get_quest_flag_with_default(self, manager):
        """测试获取不存在的任务标志时使用默认值."""
        result = manager.get_quest_flag("quest_1", "nonexistent", default=False)
        
        assert result is False

    def test_has_quest_flag_true(self, manager):
        """测试检查已存在的任务标志."""
        manager._states["quest_quest_1_started"] = True
        
        result = manager.has_quest_flag("quest_1", "started")
        
        assert result is True

    def test_has_quest_flag_false(self, manager):
        """测试检查不存在的任务标志."""
        result = manager.has_quest_flag("quest_1", "not_set")
        
        assert result is False


class TestWorldStateManagerGlobalEvent:
    """测试 WorldStateManager 全局事件相关方法."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    def test_set_global_event_active(self, manager):
        """测试设置全局事件为激活状态."""
        manager.set_global_event("event_1", active=True)
        
        assert manager._states["event_event_1"] is True

    def test_set_global_event_inactive(self, manager):
        """测试设置全局事件为非激活状态."""
        manager._states["event_event_1"] = True
        manager.set_global_event("event_1", active=False)
        
        assert manager._states["event_event_1"] is False

    def test_is_event_active_true(self, manager):
        """测试检查激活的事件."""
        manager._states["event_event_1"] = True
        
        result = manager.is_event_active("event_1")
        
        assert result is True

    def test_is_event_active_false(self, manager):
        """测试检查非激活的事件."""
        manager._states["event_event_1"] = False
        
        result = manager.is_event_active("event_1")
        
        assert result is False

    def test_is_event_active_nonexistent(self, manager):
        """测试检查不存在的事件."""
        result = manager.is_event_active("nonexistent")
        
        assert result is False

    def test_is_event_active_truthy(self, manager):
        """测试检查真值事件状态."""
        manager._states["event_event_1"] = "truthy"
        
        result = manager.is_event_active("event_1")
        
        assert result is True

    def test_trigger_event(self, manager):
        """测试触发一次性事件."""
        manager.trigger_event("unique_event")
        
        assert manager._states["triggered_unique_event"] is True

    def test_has_event_triggered_true(self, manager):
        """测试检查已触发的事件."""
        manager._states["triggered_event_1"] = True
        
        result = manager.has_event_triggered("event_1")
        
        assert result is True

    def test_has_event_triggered_false(self, manager):
        """测试检查未触发的事件."""
        result = manager.has_event_triggered("not_triggered")
        
        assert result is False


class TestWorldStateManagerBatchOperations:
    """测试 WorldStateManager 批量操作."""

    @pytest.fixture
    def manager(self):
        """创建 WorldStateManager 实例."""
        return WorldStateManager()

    @pytest.fixture
    def character(self):
        """创建模拟角色."""
        char = Mock()
        char.id = "char_123"
        return char

    def test_get_all_states(self, manager):
        """测试获取所有状态."""
        manager._states = {"key1": "value1", "key2": "value2"}
        
        result = manager.get_all_states()
        
        assert result == {"key1": "value1", "key2": "value2"}
        assert result is not manager._states  # 应该是副本

    def test_clear(self, manager):
        """测试清除所有状态."""
        manager._states = {"key1": "value1", "key2": "value2"}
        
        manager.clear()
        
        assert manager._states == {}

    def test_clear_player_states(self, manager, character):
        """测试清除指定玩家的状态."""
        manager._states = {
            "choice_char_123_choice1": {"choice": "a"},
            "choice_char_123_choice2": {"choice": "b"},
            "choice_char_456_choice1": {"choice": "c"},
            "global_key": "value",
        }
        
        manager.clear_player_states(character)
        
        assert "choice_char_123_choice1" not in manager._states
        assert "choice_char_123_choice2" not in manager._states
        assert "choice_char_456_choice1" in manager._states
        assert "global_key" in manager._states

    def test_export_states_all(self, manager):
        """测试导出所有状态."""
        manager._states = {"key1": "value1", "key2": "value2"}
        
        result = manager.export_states()
        
        assert result == {"key1": "value1", "key2": "value2"}

    def test_export_states_with_prefix(self, manager):
        """测试导出指定前缀的状态."""
        manager._states = {
            "quest_1_flag1": True,
            "quest_1_flag2": False,
            "quest_2_flag1": True,
            "global_key": "value",
        }
        
        result = manager.export_states(prefix="quest_1_")
        
        assert result == {"quest_1_flag1": True, "quest_1_flag2": False}

    def test_import_states_overwrite(self, manager):
        """测试导入状态并覆盖."""
        manager._states = {"existing": "old_value"}
        
        manager.import_states({"new_key": "new_value", "existing": "new_value"}, overwrite=True)
        
        assert manager._states["new_key"] == "new_value"
        assert manager._states["existing"] == "new_value"

    def test_import_states_no_overwrite(self, manager):
        """测试导入状态不覆盖."""
        manager._states = {"existing": "old_value"}
        
        manager.import_states({"new_key": "new_value", "existing": "new_value"}, overwrite=False)
        
        assert manager._states["new_key"] == "new_value"
        assert manager._states["existing"] == "old_value"
