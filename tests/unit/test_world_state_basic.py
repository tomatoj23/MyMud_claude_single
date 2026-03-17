"""世界状态管理单元测试.

测试WorldStateManager类.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.quest.world_state import WorldStateManager


class TestWorldStateManager:
    """WorldStateManager类测试."""

    @pytest.fixture
    def mock_engine(self):
        """创建测试引擎."""
        return Mock()

    @pytest.fixture
    def manager(self, mock_engine):
        """创建WorldStateManager实例."""
        return WorldStateManager(mock_engine)

    def test_manager_init(self, mock_engine):
        """测试WorldStateManager初始化."""
        manager = WorldStateManager(mock_engine)
        
        assert manager.engine == mock_engine
        assert manager._states == {}

    def test_manager_init_no_engine(self):
        """测试无引擎初始化."""
        manager = WorldStateManager()
        
        assert manager.engine is None
        assert manager._states == {}

    def test_get_existing(self, manager):
        """测试获取存在的值."""
        manager._states = {"key1": "value1"}
        
        assert manager.get("key1") == "value1"

    def test_get_nonexistent(self, manager):
        """测试获取不存在的值."""
        assert manager.get("nonexistent") is None

    def test_get_with_default(self, manager):
        """测试获取不存在的值返回默认值."""
        assert manager.get("nonexistent", "default") == "default"

    def test_set(self, manager):
        """测试设置值."""
        manager.set("key1", "value1")
        
        assert manager._states["key1"] == "value1"

    def test_set_overwrite(self, manager):
        """测试覆盖设置值."""
        manager.set("key1", "value1")
        manager.set("key1", "value2")
        
        assert manager._states["key1"] == "value2"

    def test_has_true(self, manager):
        """测试存在键."""
        manager._states["key1"] = "value1"
        
        assert manager.has("key1") is True

    def test_has_false(self, manager):
        """测试不存在键."""
        assert manager.has("nonexistent") is False

    def test_delete_existing(self, manager):
        """测试删除存在的键."""
        manager._states["key1"] = "value1"
        
        result = manager.delete("key1")
        
        assert result is True
        assert "key1" not in manager._states

    def test_delete_nonexistent(self, manager):
        """测试删除不存在的键."""
        result = manager.delete("nonexistent")
        
        assert result is False

    def test_increment_new(self, manager):
        """测试递增不存在的值."""
        result = manager.increment("counter")
        
        assert result == 1
        assert manager._states["counter"] == 1

    def test_increment_existing(self, manager):
        """测试递增已存在的值."""
        manager._states["counter"] = 5
        
        result = manager.increment("counter")
        
        assert result == 6

    def test_increment_with_amount(self, manager):
        """测试指定增量."""
        manager._states["counter"] = 10
        
        result = manager.increment("counter", 5)
        
        assert result == 15

    def test_increment_non_numeric(self, manager):
        """测试递增非数值（应重置为0）."""
        manager._states["counter"] = "string"
        
        result = manager.increment("counter")
        
        assert result == 1

    def test_toggle_true_to_false(self, manager):
        """测试切换真到假."""
        manager._states["flag"] = True
        
        result = manager.toggle("flag")
        
        assert result is False
        assert manager._states["flag"] is False

    def test_toggle_false_to_true(self, manager):
        """测试切换到真."""
        manager._states["flag"] = False
        
        result = manager.toggle("flag")
        
        assert result is True
        assert manager._states["flag"] is True

    def test_toggle_nonexistent(self, manager):
        """测试切换不存在的键."""
        result = manager.toggle("flag")
        
        assert result is True  # 假值取反为真
        assert manager._states["flag"] is True

    def test_toggle_non_bool(self, manager):
        """测试切换非布尔值."""
        manager._states["flag"] = "truthy"
        
        result = manager.toggle("flag")
        
        assert result is False  # 真值取反

    def test_on_player_choice(self, manager):
        """测试记录玩家选择."""
        character = Mock()
        character.id = 123
        
        manager.on_player_choice(character, "save_village", "yes")
        
        assert manager._states["choice_123_save_village"] == {
            "choice": "yes",
            "character_id": 123
        }

    def test_get_player_choice_exists(self, manager):
        """测试获取存在的玩家选择."""
        character = Mock()
        character.id = 123
        
        manager._states["choice_123_decision"] = {
            "choice": "option_a",
            "character_id": 123
        }
        
        result = manager.get_player_choice(character, "decision")
        
        assert result == "option_a"

    def test_get_player_choice_nonexistent(self, manager):
        """测试获取不存在的玩家选择."""
        character = Mock()
        character.id = 123
        
        result = manager.get_player_choice(character, "unknown")
        
        assert result is None

    def test_get_player_choice_invalid_data(self, manager):
        """测试获取格式错误的选择数据."""
        character = Mock()
        character.id = 123
        
        manager._states["choice_123_bad"] = "not_a_dict"
        
        result = manager.get_player_choice(character, "bad")
        
        assert result is None

    def test_has_made_choice_true(self, manager):
        """测试已做出选择."""
        character = Mock()
        character.id = 123
        
        manager._states["choice_123_made"] = {"choice": "yes"}
        
        assert manager.has_made_choice(character, "made") is True

    def test_has_made_choice_false(self, manager):
        """测试未做出选择."""
        character = Mock()
        character.id = 123
        
        assert manager.has_made_choice(character, "not_made") is False

    def test_set_quest_flag(self, manager):
        """测试设置任务标志."""
        manager.set_quest_flag("main_quest", "started", True)
        
        assert manager._states["quest_main_quest_started"] is True

    def test_get_quest_flag_exists(self, manager):
        """测试获取存在的任务标志."""
        manager._states["quest_main_quest_completed"] = True
        
        result = manager.get_quest_flag("main_quest", "completed")
        
        assert result is True

    def test_get_quest_flag_nonexistent(self, manager):
        """测试获取不存在的任务标志."""
        result = manager.get_quest_flag("main_quest", "unknown")
        
        assert result is None

    def test_get_quest_flag_with_default(self, manager):
        """测试获取不存在的任务标志返回默认值."""
        result = manager.get_quest_flag("main_quest", "unknown", False)
        
        assert result is False

    def test_has_quest_flag_true(self, manager):
        """测试存在任务标志."""
        manager._states["quest_main_quest_active"] = True
        
        assert manager.has_quest_flag("main_quest", "active") is True

    def test_has_quest_flag_false(self, manager):
        """测试不存在任务标志."""
        assert manager.has_quest_flag("main_quest", "inactive") is False

    def test_set_global_event(self, manager):
        """测试设置全局事件."""
        manager.set_global_event("dragon_attack", True)
        
        assert manager._states["event_dragon_attack"] is True

    def test_is_event_active_true(self, manager):
        """测试事件激活状态."""
        manager._states["event_festival"] = True
        
        assert manager.is_event_active("festival") is True

    def test_is_event_active_false(self, manager):
        """测试事件未激活."""
        manager._states["event_festival"] = False
        
        assert manager.is_event_active("festival") is False

    def test_is_event_active_nonexistent(self, manager):
        """测试不存在的事件."""
        assert manager.is_event_active("unknown") is False

    def test_trigger_event(self, manager):
        """测试触发一次性事件."""
        manager.trigger_event("boss_defeated")
        
        assert manager._states["triggered_boss_defeated"] is True

    def test_has_event_triggered_true(self, manager):
        """测试事件已触发."""
        manager._states["triggered_secret_found"] = True
        
        assert manager.has_event_triggered("secret_found") is True

    def test_has_event_triggered_false(self, manager):
        """测试事件未触发."""
        assert manager.has_event_triggered("not_triggered") is False

    def test_get_all_states(self, manager):
        """测试获取所有状态."""
        manager._states = {"key1": "value1", "key2": "value2"}
        
        states = manager.get_all_states()
        
        assert states == {"key1": "value1", "key2": "value2"}
        assert states is not manager._states  # 应该是副本

    def test_clear(self, manager):
        """测试清空所有状态."""
        manager._states = {"key": "value"}
        
        manager.clear()
        
        assert manager._states == {}

    def test_clear_player_states(self, manager):
        """测试清空指定玩家的状态."""
        character = Mock()
        character.id = 123
        
        manager._states = {
            "choice_123_decision": {"choice": "yes"},
            "choice_456_other": {"choice": "no"},
            "global_state": "value"
        }
        
        manager.clear_player_states(character)
        
        assert "choice_123_decision" not in manager._states
        assert "choice_456_other" in manager._states
        assert "global_state" in manager._states

    def test_export_states_all(self, manager):
        """测试导出所有状态."""
        manager._states = {"key1": "value1", "key2": "value2"}
        
        exported = manager.export_states()
        
        assert exported == manager._states

    def test_export_states_with_prefix(self, manager):
        """测试导出指定前缀的状态."""
        manager._states = {
            "quest_main_started": True,
            "quest_side_started": True,
            "other_key": "value"
        }
        
        exported = manager.export_states("quest_")
        
        assert "quest_main_started" in exported
        assert "quest_side_started" in exported
        assert "other_key" not in exported

    def test_import_states(self, manager):
        """测试导入状态."""
        states = {"key1": "value1", "key2": "value2"}
        
        manager.import_states(states)
        
        assert manager._states["key1"] == "value1"
        assert manager._states["key2"] == "value2"

    def test_import_states_no_overwrite(self, manager):
        """测试导入状态不覆盖."""
        manager._states["key1"] = "original"
        
        states = {"key1": "new", "key2": "value2"}
        
        manager.import_states(states, overwrite=False)
        
        assert manager._states["key1"] == "original"  # 不覆盖
        assert manager._states["key2"] == "value2"

    def test_import_states_with_overwrite(self, manager):
        """测试导入状态覆盖."""
        manager._states["key1"] = "original"
        
        states = {"key1": "new", "key2": "value2"}
        
        manager.import_states(states, overwrite=True)
        
        assert manager._states["key1"] == "new"  # 覆盖
        assert manager._states["key2"] == "value2"


# --- Merged from test_world_state_coverage.py ---

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


