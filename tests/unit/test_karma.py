"""因果点系统单元测试.

测试KarmaSystem类.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.quest.karma import KarmaSystem, add_karma, check_karma_requirement


class TestKarmaSystem:
    """KarmaSystem类测试."""

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.db = Mock()
        char.db.get = Mock(return_value={})
        char.db.set = Mock()
        return char

    @pytest.fixture
    def karma_system(self, character):
        """创建KarmaSystem实例."""
        return KarmaSystem(character)

    def test_karma_types(self, karma_system):
        """测试因果点类型列表."""
        assert "good" in KarmaSystem.KARMA_TYPES
        assert "evil" in KarmaSystem.KARMA_TYPES
        assert "love" in KarmaSystem.KARMA_TYPES
        assert "loyalty" in KarmaSystem.KARMA_TYPES
        assert "wisdom" in KarmaSystem.KARMA_TYPES
        assert "courage" in KarmaSystem.KARMA_TYPES
        assert len(KarmaSystem.KARMA_TYPES) == 6

    def test_add_karma_new(self, karma_system, character):
        """测试添加新的因果点."""
        karma_system.add_karma("good", 10)
        
        character.db.set.assert_called_once()
        call_args = character.db.set.call_args[0]
        assert call_args[0] == "karma"
        assert call_args[1]["good"] == 10

    def test_add_karma_existing(self, karma_system, character):
        """测试添加到已有因果点."""
        character.db.get = Mock(return_value={"good": 5})
        
        karma_system.add_karma("good", 10)
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["good"] == 15  # 5 + 10

    def test_add_karma_negative(self, karma_system, character):
        """测试添加负因果点."""
        character.db.get = Mock(return_value={"good": 10})
        
        karma_system.add_karma("good", -5)
        
        call_args = character.db.set.call_args[0]
        assert call_args[1]["good"] == 5

    def test_add_karma_with_reason(self, karma_system, character):
        """测试添加因果点并记录原因."""
        character.db.get = Mock(side_effect=[{}, []])
        
        karma_system.add_karma("good", 10, "帮助村民")
        
        # 检查历史记录
        history_call = [call for call in character.db.set.call_args_list 
                       if call[0][0] == "karma_history"]
        assert len(history_call) == 1

    def test_add_karma_invalid_type(self, karma_system):
        """测试添加无效类型的因果点."""
        with pytest.raises(ValueError) as exc_info:
            karma_system.add_karma("invalid", 10)
        
        assert "invalid" in str(exc_info.value)

    def test_get_karma_existing(self, karma_system, character):
        """测试获取已有因果点."""
        character.db.get = Mock(return_value={"good": 15, "evil": 5})
        
        assert karma_system.get_karma("good") == 15
        assert karma_system.get_karma("evil") == 5

    def test_get_karma_nonexistent(self, karma_system, character):
        """测试获取不存在的因果点."""
        character.db.get = Mock(return_value={})
        
        assert karma_system.get_karma("good") == 0

    def test_get_karma_invalid_type(self, karma_system, character):
        """测试获取无效类型的因果点."""
        assert karma_system.get_karma("invalid") == 0

    def test_get_karma_summary(self, karma_system, character):
        """测试获取因果点汇总."""
        character.db.get = Mock(return_value={"good": 10, "evil": 5})
        
        summary = karma_system.get_karma_summary()
        
        assert summary["good"] == 10
        assert summary["evil"] == 5
        # 未设置的类型默认为0
        assert summary["love"] == 0
        assert summary["loyalty"] == 0

    def test_get_karma_history(self, karma_system, character):
        """测试获取因果点历史."""
        history = [{"type": "good", "points": 10, "reason": "帮助"}]
        character.db.get = Mock(return_value=history)
        
        result = karma_system.get_karma_history()
        
        assert result == history

    def test_check_requirement_single_gte(self, karma_system, character):
        """测试单一大于等于条件."""
        character.db.get = Mock(return_value={"good": 15})
        
        result = karma_system.check_requirement({"good": ">=10"})
        
        assert result is True

    def test_check_requirement_single_gte_fail(self, karma_system, character):
        """测试单一大于等于条件失败."""
        character.db.get = Mock(return_value={"good": 5})
        
        result = karma_system.check_requirement({"good": ">=10"})
        
        assert result is False

    def test_check_requirement_single_lte(self, karma_system, character):
        """测试单一小于等于条件."""
        character.db.get = Mock(return_value={"evil": 5})
        
        result = karma_system.check_requirement({"evil": "<=10"})
        
        assert result is True

    def test_check_requirement_single_lte_fail(self, karma_system, character):
        """测试单一小于等于条件失败."""
        character.db.get = Mock(return_value={"evil": 15})
        
        result = karma_system.check_requirement({"evil": "<=10"})
        
        assert result is False

    def test_check_requirement_multiple_all_pass(self, karma_system, character):
        """测试多个条件全部通过."""
        character.db.get = Mock(return_value={"good": 20, "evil": 5})
        
        result = karma_system.check_requirement({
            "good": ">=10",
            "evil": "<=10"
        })
        
        assert result is True

    def test_check_requirement_multiple_one_fail(self, karma_system, character):
        """测试多个条件有一个失败."""
        character.db.get = Mock(return_value={"good": 5, "evil": 5})
        
        result = karma_system.check_requirement({
            "good": ">=10",
            "evil": "<=10"
        })
        
        assert result is False

    def test_check_single_requirement_gt(self, karma_system, character):
        """测试大于条件."""
        character.db.get = Mock(return_value={"wisdom": 15})
        
        assert karma_system.check_single_requirement("wisdom", ">10") is True
        assert karma_system.check_single_requirement("wisdom", ">20") is False

    def test_check_single_requirement_lt(self, karma_system, character):
        """测试小于条件."""
        character.db.get = Mock(return_value={"wisdom": 15})
        
        assert karma_system.check_single_requirement("wisdom", "<20") is True
        assert karma_system.check_single_requirement("wisdom", "<10") is False

    def test_check_single_requirement_eq(self, karma_system, character):
        """测试等于条件."""
        character.db.get = Mock(return_value={"wisdom": 15})
        
        assert karma_system.check_single_requirement("wisdom", "==15") is True
        assert karma_system.check_single_requirement("wisdom", "==10") is False

    def test_check_single_requirement_default_gte(self, karma_system, character):
        """测试默认大于等于条件."""
        character.db.get = Mock(return_value={"wisdom": 15})
        
        assert karma_system.check_single_requirement("wisdom", "10") is True
        assert karma_system.check_single_requirement("wisdom", "20") is False

    def test_get_alignment_daxia(self, karma_system, character):
        """测试大侠阵营."""
        character.db.get = Mock(return_value={"good": 150, "evil": 0})
        
        assert karma_system.get_alignment() == "大侠"

    def test_get_alignment_shanren(self, karma_system, character):
        """测试善人阵营."""
        character.db.get = Mock(return_value={"good": 75, "evil": 0})
        
        assert karma_system.get_alignment() == "善人"

    def test_get_alignment_zhongli(self, karma_system, character):
        """测试中立阵营."""
        character.db.get = Mock(return_value={"good": 20, "evil": 20})
        
        assert karma_system.get_alignment() == "中立"

    def test_get_alignment_erenn(self, karma_system, character):
        """测试恶人阵营."""
        character.db.get = Mock(return_value={"good": 0, "evil": 75})
        
        assert karma_system.get_alignment() == "恶人"

    def test_get_alignment_motou(self, karma_system, character):
        """测试魔头阵营."""
        character.db.get = Mock(return_value={"good": 0, "evil": 150})
        
        assert karma_system.get_alignment() == "魔头"

    def test_get_reputation_title_loyalty(self, karma_system, character):
        """测试忠义声望称号."""
        character.db.get = Mock(return_value={"loyalty": 150, "wisdom": 50, "courage": 50})
        
        assert "忠义" in karma_system.get_reputation_title()

    def test_get_reputation_title_wisdom(self, karma_system, character):
        """测试智慧声望称号."""
        character.db.get = Mock(return_value={"loyalty": 50, "wisdom": 150, "courage": 50})
        
        assert "智" in karma_system.get_reputation_title()

    def test_get_reputation_title_courage(self, karma_system, character):
        """测试勇气声望称号."""
        character.db.get = Mock(return_value={"loyalty": 50, "wisdom": 50, "courage": 150})
        
        assert "勇" in karma_system.get_reputation_title()

    def test_get_reputation_title_low(self, karma_system, character):
        """测试低声望称号."""
        character.db.get = Mock(return_value={})
        
        assert karma_system.get_reputation_title() == "无名小卒"

    def test_get_romance_style_qingsheng(self, karma_system, character):
        """测试情圣感情倾向."""
        character.db.get = Mock(return_value={"love": 150})
        
        assert karma_system.get_romance_style() == "情圣"

    def test_get_romance_style_duoqing(self, karma_system, character):
        """测试多情感情倾向."""
        character.db.get = Mock(return_value={"love": 75})
        
        assert karma_system.get_romance_style() == "多情种子"

    def test_get_romance_style_wuqing(self, karma_system, character):
        """测试无情感情倾向."""
        character.db.get = Mock(return_value={"love": 0})
        
        assert karma_system.get_romance_style() == "无情"

    def test_get_romance_style_lengxue(self, karma_system, character):
        """测试冷血感情倾向."""
        character.db.get = Mock(return_value={"love": -50})
        
        assert karma_system.get_romance_style() == "冷血"

    def test_get_summary_text(self, karma_system, character):
        """测试汇总文本."""
        character.db.get = Mock(return_value={"good": 50, "evil": 10})
        
        text = karma_system.get_summary_text()
        
        assert "阵营" in text
        assert "声望" in text
        assert "感情" in text
        assert "善良" in text
        assert "邪恶" in text


class TestKarmaHelperFunctions:
    """因果点便捷函数测试."""

    def test_add_karma_helper(self):
        """测试add_karma便捷函数."""
        character = Mock()
        character.db = Mock()
        # 返回空dict作为karma，空list作为history
        def mock_get(key, default=None):
            if key == "karma_history":
                return []
            return {}
        character.db.get = Mock(side_effect=mock_get)
        character.db.set = Mock()
        
        add_karma(character, "good", 10, "帮助村民")
        
        character.db.set.assert_called()

    def test_check_karma_requirement_helper(self):
        """测试check_karma_requirement便捷函数."""
        character = Mock()
        character.db = Mock()
        character.db.get = Mock(return_value={"good": 20})
        
        result = check_karma_requirement(character, {"good": ">=10"})
        
        assert result is True
