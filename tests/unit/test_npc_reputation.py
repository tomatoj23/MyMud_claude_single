"""NPC好感度系统单元测试.

测试NPCRelationship类.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.npc.reputation import NPCRelationship


class TestNPCRelationship:
    """NPCRelationship类测试."""

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.db = Mock()
        char.db.get = Mock(return_value={})
        char.db.set = Mock()
        return char

    @pytest.fixture
    def relationship(self, character):
        """创建NPCRelationship实例."""
        return NPCRelationship(character)

    def test_init(self, character):
        """测试NPCRelationship初始化."""
        rel = NPCRelationship(character)
        
        assert rel.character == character

    def test_get_favor_default(self, relationship, character):
        """测试获取默认好感度."""
        character.db.get = Mock(return_value={})
        
        favor = relationship.get_favor("npc1")
        
        assert favor == 0

    def test_get_favor_existing(self, relationship, character):
        """测试获取已有好感度."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 50}
        })
        
        favor = relationship.get_favor("npc1")
        
        assert favor == 50

    def test_modify_favor_new_npc(self, relationship, character):
        """测试为新NPC添加好感度."""
        relationship.modify_favor("npc1", 10)
        
        character.db.set.assert_called()
        call_args = character.db.set.call_args[0]
        assert call_args[0] == "npc_relations"
        assert call_args[1]["npc1"]["favor"] == 10

    def test_modify_favor_existing(self, relationship, character):
        """测试为已有NPC增加好感度."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 20, "history": []}
        })
        
        relationship.modify_favor("npc1", 10)
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["npc1"]["favor"] == 30

    def test_modify_favor_negative(self, relationship, character):
        """测试减少好感度."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 20, "history": []}
        })
        
        relationship.modify_favor("npc1", -10)
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["npc1"]["favor"] == 10

    def test_modify_favor_with_reason(self, relationship, character):
        """测试修改好感度并记录原因."""
        relationship.modify_favor("npc1", 10, "帮助任务")
        
        call_args = character.db.set.call_args[0]
        history = call_args[1]["npc1"]["history"]
        assert len(history) == 1
        assert history[0]["delta"] == 10
        assert history[0]["reason"] == "帮助任务"

    def test_modify_favor_history_limit(self, relationship, character):
        """测试好感度历史记录限制."""
        # 创建21条历史记录
        existing_history = [{"delta": 1, "reason": f"reason_{i}"} for i in range(21)]
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0, "history": existing_history}
        })
        
        relationship.modify_favor("npc1", 10, "新记录")
        
        call_args = character.db.set.call_args[0]
        history = call_args[1]["npc1"]["history"]
        assert len(history) == 20  # 限制为20条

    def test_set_favor(self, relationship, character):
        """测试直接设置好感度."""
        relationship.set_favor("npc1", 100)
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["npc1"]["favor"] == 100

    def test_get_relationship_level_choudi(self, relationship, character):
        """测试仇敌关系等级."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": -150}
        })
        
        level = relationship.get_relationship_level("npc1")
        
        assert level == "仇敌"

    def test_get_relationship_level_lengdan(self, relationship, character):
        """测试冷淡关系等级."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": -75}
        })
        
        level = relationship.get_relationship_level("npc1")
        
        assert level == "冷淡"

    def test_get_relationship_level_mosheng(self, relationship, character):
        """测试陌生关系等级."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0}
        })
        
        level = relationship.get_relationship_level("npc1")
        
        assert level == "陌生"

    def test_get_relationship_level_youshan(self, relationship, character):
        """测试友善关系等级."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 75}
        })
        
        level = relationship.get_relationship_level("npc1")
        
        assert level == "友善"

    def test_get_relationship_level_zunjing(self, relationship, character):
        """测试尊敬关系等级."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 150}
        })
        
        level = relationship.get_relationship_level("npc1")
        
        assert level == "尊敬"

    def test_get_relationship_level_zhijiao(self, relationship, character):
        """测试至交关系等级."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 250}
        })
        
        level = relationship.get_relationship_level("npc1")
        
        assert level == "至交"

    def test_get_favor_status(self, relationship, character):
        """测试获取完整好感度状态."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 75}
        })
        
        status = relationship.get_favor_status("npc1")
        
        assert status["npc_id"] == "npc1"
        assert status["favor"] == 75
        assert status["level"] == "友善"
        assert status["is_hostile"] is False
        assert status["is_friendly"] is True

    def test_is_hostile_true(self, relationship, character):
        """测试是敌对关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": -60}
        })
        
        assert relationship.is_hostile("npc1") is True

    def test_is_hostile_false(self, relationship, character):
        """测试不是敌对关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0}
        })
        
        assert relationship.is_hostile("npc1") is False

    def test_is_friendly_true(self, relationship, character):
        """测试是友好关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 60}
        })
        
        assert relationship.is_friendly("npc1") is True

    def test_is_friendly_false(self, relationship, character):
        """测试不是友好关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0}
        })
        
        assert relationship.is_friendly("npc1") is False

    def test_is_stranger(self, relationship, character):
        """测试是陌生关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0}
        })
        
        assert relationship.is_stranger("npc1") is True

    def test_is_stranger_not(self, relationship, character):
        """测试不是陌生关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 100}
        })
        
        assert relationship.is_stranger("npc1") is False

    def test_can_trade_not_hostile(self, relationship, character):
        """测试非敌对可以交易."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0}
        })
        
        assert relationship.can_trade("npc1") is True

    def test_can_trade_hostile(self, relationship, character):
        """测试敌对不能交易."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": -100}
        })
        
        assert relationship.can_trade("npc1") is False

    def test_can_learn_friendly(self, relationship, character):
        """测试友好可以学习."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 60}
        })
        
        assert relationship.can_learn("npc1") is True

    def test_can_learn_not_friendly(self, relationship, character):
        """测试不友好不能学习."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 0}
        })
        
        assert relationship.can_learn("npc1") is False

    def test_will_help_high_favor(self, relationship, character):
        """测试高好感度会帮助."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 150}
        })
        
        assert relationship.will_help("npc1") is True

    def test_will_help_low_favor(self, relationship, character):
        """测试低好感度不会帮助."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 50}
        })
        
        assert relationship.will_help("npc1") is False

    def test_get_history(self, relationship, character):
        """测试获取历史记录."""
        history = [{"delta": 10, "reason": "帮助"}, {"delta": -5, "reason": "冒犯"}]
        character.db.get = Mock(return_value={
            "npc1": {"favor": 5, "history": history}
        })
        
        result = relationship.get_history("npc1")
        
        assert result == history

    def test_get_all_relations(self, relationship, character):
        """测试获取所有关系."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 50},
            "npc2": {"favor": -30}
        })
        
        relations = relationship.get_all_relations()
        
        assert len(relations) == 2
        assert relations[0]["npc_id"] == "npc1"
        assert relations[1]["npc_id"] == "npc2"

    def test_get_friendly_npcs(self, relationship, character):
        """测试获取友好NPC列表."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 60},  # 友好
            "npc2": {"favor": -60},  # 敌对
            "npc3": {"favor": 80}   # 友好
        })
        
        friendly = relationship.get_friendly_npcs()
        
        assert "npc1" in friendly
        assert "npc3" in friendly
        assert "npc2" not in friendly

    def test_get_hostile_npcs(self, relationship, character):
        """测试获取敌对NPC列表."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 60},   # 友好
            "npc2": {"favor": -60},  # 敌对
            "npc3": {"favor": -80}   # 敌对
        })
        
        hostile = relationship.get_hostile_npcs()
        
        assert "npc2" in hostile
        assert "npc3" in hostile
        assert "npc1" not in hostile

    def test_clear_history(self, relationship, character):
        """测试清空历史记录."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 50, "history": [{"delta": 10}]}
        })
        
        relationship.clear_history("npc1")
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["npc1"]["history"] == []

    def test_reset_favor(self, relationship, character):
        """测试重置好感度."""
        character.db.get = Mock(return_value={
            "npc1": {"favor": 100}
        })
        
        relationship.reset_favor("npc1")
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["npc1"]["favor"] == 0

    def test_clear_all_relations(self, relationship, character):
        """测试清空所有关系."""
        relationship.clear_all_relations()
        
        character.db.set.assert_called_with("npc_relations", {})


class TestNPCRelationshipFaction:
    """NPC关系派系相关测试."""

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.db = Mock()
        char.db.get = Mock(return_value={})
        char.db.set = Mock()
        return char

    @pytest.fixture
    def relationship(self, character):
        """创建NPCRelationship实例."""
        return NPCRelationship(character)

    def test_get_faction_favor(self, relationship):
        """测试获取派系好感度（预留方法）."""
        result = relationship.get_faction_favor("faction1")
        
        # 当前实现返回0
        assert result == 0

    def test_modify_faction_favor(self, relationship):
        """测试修改派系好感度（预留方法）."""
        # 当前实现为空pass，不应抛出异常
        relationship.modify_faction_favor("faction1", 10)
