"""因果点系统补充测试 - 达到100%覆盖率.

覆盖 karma.py 中缺失的行:
- 171-174: get_reputation_title 中 wisdom 的 else 分支
- 178-181: get_reputation_title 中 wisdom 的中等值分支
- 185-188: get_reputation_title 中 courage 的中等值分支
- 199: get_romance_style 中 love > 0 且 < 50 的分支
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.quest.karma import KarmaSystem


class TestKarmaReputationTitleBranches:
    """测试声望称号的分支覆盖."""

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

    def test_get_reputation_title_wisdom_low(self, karma_system, character):
        """测试智慧称号 - 低值分支 (10-49)."""
        character.db.get = Mock(return_value={"wisdom": 25})
        
        result = karma_system.get_reputation_title()
        
        assert result == "有见识的人"

    def test_get_reputation_title_courage_low(self, karma_system, character):
        """测试勇气称号 - 低值分支 (10-49)."""
        character.db.get = Mock(return_value={"courage": 25})
        
        result = karma_system.get_reputation_title()
        
        assert result == "有勇气的人"

    def test_get_reputation_title_courage_mid(self, karma_system, character):
        """测试勇气称号 - 中值分支 (50-99)."""
        character.db.get = Mock(return_value={"courage": 75})
        
        result = karma_system.get_reputation_title()
        
        assert result == "勇士"

    def test_get_reputation_title_courage_high(self, karma_system, character):
        """测试勇气称号 - 高值分支 (>=100)."""
        character.db.get = Mock(return_value={"courage": 150})
        
        result = karma_system.get_reputation_title()
        
        assert result == "勇者"

    def test_get_reputation_title_loyalty_low(self, karma_system, character):
        """测试忠义称号 - 低值分支 (10-49)."""
        character.db.get = Mock(return_value={"loyalty": 25})
        
        result = karma_system.get_reputation_title()
        
        assert result == "有信之人"

    def test_get_reputation_title_loyalty_mid(self, karma_system, character):
        """测试忠义称号 - 中值分支 (50-99)."""
        character.db.get = Mock(return_value={"loyalty": 75})
        
        result = karma_system.get_reputation_title()
        
        assert result == "可靠之人"

    def test_get_reputation_title_loyalty_high(self, karma_system, character):
        """测试忠义称号 - 高值分支 (>=100)."""
        character.db.get = Mock(return_value={"loyalty": 150})
        
        result = karma_system.get_reputation_title()
        
        assert result == "忠义之士"

    def test_get_reputation_title_wisdom_mid(self, karma_system, character):
        """测试智慧称号 - 中值分支 (50-99)."""
        character.db.get = Mock(return_value={"wisdom": 75})
        
        result = karma_system.get_reputation_title()
        
        assert result == "聪明人"

    def test_get_reputation_title_wisdom_high(self, karma_system, character):
        """测试智慧称号 - 高值分支 (>=100)."""
        character.db.get = Mock(return_value={"wisdom": 150})
        
        result = karma_system.get_reputation_title()
        
        assert result == "智者"


class TestKarmaRomanceStyleBranches:
    """测试感情倾向的分支覆盖."""

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

    def test_get_romance_style_youqing(self, karma_system, character):
        """测试感情倾向 - 有情之人 (0 < love < 50)."""
        character.db.get = Mock(return_value={"love": 25})
        
        result = karma_system.get_romance_style()
        
        assert result == "有情之人"

    def test_get_romance_style_youqing_edge(self, karma_system, character):
        """测试感情倾向 - 有情之人边界值 (love = 1)."""
        character.db.get = Mock(return_value={"love": 1})
        
        result = karma_system.get_romance_style()
        
        assert result == "有情之人"

    def test_get_romance_style_youqing_edge_49(self, karma_system, character):
        """测试感情倾向 - 有情之人边界值 (love = 49)."""
        character.db.get = Mock(return_value={"love": 49})
        
        result = karma_system.get_romance_style()
        
        assert result == "有情之人"
