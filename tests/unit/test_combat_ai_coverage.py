"""Combat AI 覆盖率补充测试."""
import pytest
from unittest.mock import Mock

from src.game.combat.ai import SmartAI, AggressiveAI, DefensiveAI


class TestSmartAICoverage:
    """补充 SmartAI 未覆盖的分支."""

    @pytest.mark.asyncio
    async def test_smart_ai_no_targets_defends(self):
        """测试 SmartAI 没有目标时返回防御."""
        ai = SmartAI()
        character = Mock()
        character.get_hp.return_value = (50, 100)  # 50%血量
        
        combat = Mock()
        combat.get_alive_enemies.return_value = []
        
        result = await ai.decide(character, combat)
        
        assert result.type == "defend"

    def test_select_target_empty_raises(self):
        """测试 _select_target 空列表时抛出异常."""
        ai = SmartAI()
        
        with pytest.raises(ValueError, match="No targets available"):
            ai._select_target([])

    def test_select_best_move_empty_returns_none(self):
        """测试 _select_best_move 空列表时返回 None."""
        ai = SmartAI()
        target = Mock()
        
        result = ai._select_best_move([], target)
        
        assert result is None


class TestAggressiveAICoverage:
    """补充 AggressiveAI 未覆盖的分支."""

    @pytest.mark.asyncio
    async def test_aggressive_ai_no_targets_defends(self):
        """测试 AggressiveAI 没有目标时返回防御."""
        ai = AggressiveAI()
        character = Mock()
        combat = Mock()
        combat.get_alive_enemies.return_value = []
        
        result = await ai.decide(character, combat)
        
        assert result.type == "defend"


class TestDefensiveAICoverage:
    """补充 DefensiveAI 未覆盖的分支."""

    @pytest.mark.asyncio
    async def test_defensive_ai_no_enemies_defends(self):
        """测试 DefensiveAI 没有敌人时返回防御."""
        ai = DefensiveAI()
        character = Mock()
        character.get_hp.return_value = (80, 100)
        
        combat = Mock()
        combat.get_alive_enemies.return_value = []
        
        result = await ai.decide(character, combat)
        
        assert result.type == "defend"
