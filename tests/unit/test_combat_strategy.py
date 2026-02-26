"""战斗策略模式测试."""

import pytest
from unittest.mock import MagicMock, patch

from src.game.combat.strategy import (
    ActionResult,
    AttackStrategy,
    CastStrategy,
    FleeStrategy,
    DefendStrategy,
)


class TestActionResult:
    """测试行动结果类"""
    
    def test_default_values(self):
        """测试默认值"""
        result = ActionResult()
        assert result.success is False
        assert result.message == ""
        assert result.damage == 0
        assert result.side_effects == []
    
    def test_custom_values(self):
        """测试自定义值"""
        result = ActionResult(
            success=True,
            message="成功",
            damage=100
        )
        assert result.success is True
        assert result.message == "成功"
        assert result.damage == 100
    
    def test_add_side_effect(self):
        """测试添加副作用"""
        result = ActionResult()
        result.add_side_effect("hp_change", {"old": 100, "new": 80})
        assert len(result.side_effects) == 1
        assert result.side_effects[0]["type"] == "hp_change"


class TestAttackStrategy:
    """测试攻击策略"""
    
    def test_validate_no_target(self):
        """验证失败：无目标"""
        strategy = AttackStrategy()
        session = MagicMock()
        combatant = MagicMock()
        
        valid, msg = strategy.validate(session, combatant, {})
        assert valid is False
        assert "目标" in msg
    
    def test_validate_target_not_in_combat(self):
        """验证失败：目标不在战斗中"""
        strategy = AttackStrategy()
        session = MagicMock()
        session.participants = {}
        combatant = MagicMock()
        target = MagicMock()
        target.id = 123
        
        valid, msg = strategy.validate(session, combatant, {"target": target})
        assert valid is False
        assert "不在战斗中" in msg
    
    def test_validate_success(self):
        """验证成功"""
        strategy = AttackStrategy()
        session = MagicMock()
        target = MagicMock()
        target.id = 123
        target_combatant = MagicMock()
        target_combatant.in_combat = True
        session.participants = {123: target_combatant}
        combatant = MagicMock()
        
        valid, msg = strategy.validate(session, combatant, {"target": target})
        assert valid is True
    
    def test_get_cooldown_with_move(self):
        """测试获取冷却时间（有招式）"""
        strategy = AttackStrategy()
        move = MagicMock()
        move.cooldown = 5.0
        
        cooldown = strategy.get_cooldown({"move": move})
        assert cooldown == 5.0
    
    def test_get_cooldown_default(self):
        """测试获取冷却时间（默认）"""
        strategy = AttackStrategy()
        cooldown = strategy.get_cooldown({})
        assert cooldown == 3.0


class TestCastStrategy:
    """测试内功策略"""
    
    def test_validate_no_neigong(self):
        """验证失败：未指定内功"""
        strategy = CastStrategy()
        session = MagicMock()
        combatant = MagicMock()
        
        valid, msg = strategy.validate(session, combatant, {})
        assert valid is False
        assert "未指定内功" in msg
    
    def test_validate_not_learned(self):
        """验证失败：未学会内功"""
        strategy = CastStrategy()
        session = MagicMock()
        combatant = MagicMock()
        combatant.character.wuxue_has_learned.return_value = False
        
        valid, msg = strategy.validate(session, combatant, {"neigong": "test"})
        assert valid is False
        assert "尚未学会" in msg
    
    def test_validate_not_enough_mp(self):
        """验证失败：内力不足"""
        strategy = CastStrategy()
        session = MagicMock()
        char = MagicMock()
        char.wuxue_has_learned.return_value = True
        char.mp = 10
        combatant = MagicMock()
        combatant.character = char
        
        valid, msg = strategy.validate(session, combatant, {"neigong": "test", "mp_cost": 20})
        assert valid is False
        assert "内力不足" in msg
    
    def test_get_cooldown_heal(self):
        """测试治疗冷却"""
        strategy = CastStrategy()
        assert strategy.get_cooldown({"effect": "heal"}) == 3.0
    
    def test_get_cooldown_buff(self):
        """测试buff冷却"""
        strategy = CastStrategy()
        assert strategy.get_cooldown({"effect": "buff"}) == 2.0
    
    def test_get_cooldown_attack(self):
        """测试攻击冷却"""
        strategy = CastStrategy()
        assert strategy.get_cooldown({"effect": "attack"}) == 4.0
    
    def test_get_mp_cost(self):
        """测试内力消耗"""
        strategy = CastStrategy()
        assert strategy.get_mp_cost({"mp_cost": 30}) == 30
        assert strategy.get_mp_cost({}) == 20


class TestFleeStrategy:
    """测试逃跑策略"""
    
    def test_validate_no_enemies(self):
        """验证失败：无敌人"""
        strategy = FleeStrategy()
        session = MagicMock()
        session.participants = {}
        char = MagicMock()
        char.id = 1
        combatant = MagicMock()
        combatant.character = char
        
        valid, msg = strategy.validate(session, combatant, {})
        assert valid is False
        assert "没有敌人" in msg
    
    def test_get_cooldown(self):
        """测试逃跑冷却"""
        strategy = FleeStrategy()
        assert strategy.get_cooldown({}) == 5.0


class TestDefendStrategy:
    """测试防御策略"""
    
    def test_validate_always_success(self):
        """验证总是成功"""
        strategy = DefendStrategy()
        session = MagicMock()
        combatant = MagicMock()
        
        valid, msg = strategy.validate(session, combatant, {})
        assert valid is True
    
    def test_get_cooldown(self):
        """测试防御冷却"""
        strategy = DefendStrategy()
        assert strategy.get_cooldown({}) == 1.5


class TestStrategyRegistration:
    """测试策略注册"""
    
    def test_strategies_loaded(self):
        """测试策略已加载"""
        from src.game.combat.core import _get_strategies
        
        strategies = _get_strategies()
        assert "kill" in strategies
        assert "cast" in strategies
        assert "flee" in strategies
        assert "defend" in strategies
        
        # 验证类型
        assert isinstance(strategies["kill"], AttackStrategy)
        assert isinstance(strategies["cast"], CastStrategy)
        assert isinstance(strategies["flee"], FleeStrategy)
        assert isinstance(strategies["defend"], DefendStrategy)
