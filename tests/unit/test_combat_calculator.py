"""战斗数值计算器单元测试.

测试CombatCalculator和DamageResult.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.combat.calculator import CombatCalculator, CombatContext, DamageResult


class TestDamageResult:
    """DamageResult数据类测试."""

    def test_damage_result_defaults(self):
        """测试DamageResult默认值."""
        result = DamageResult()
        
        assert result.damage == 0
        assert result.is_crit is False
        assert result.is_hit is True
        assert result.messages == []

    def test_damage_result_custom_values(self):
        """测试DamageResult自定义值."""
        result = DamageResult(
            damage=100.5,
            is_crit=True,
            is_hit=True,
            messages=["暴击！", "招式克制！"]
        )
        
        assert result.damage == 100.5
        assert result.is_crit is True
        assert result.messages == ["暴击！", "招式克制！"]

    def test_damage_result_post_init_messages(self):
        """测试DamageResult messages初始化为空列表."""
        result = DamageResult(damage=50)
        
        # 应该自动创建空列表
        assert result.messages == []
        # 验证是可变的
        result.messages.append("测试")
        assert result.messages == ["测试"]


class TestCombatCalculator:
    """CombatCalculator类测试."""

    @pytest.fixture
    def attacker(self):
        """创建攻击者."""
        char = Mock()
        char.get_attack.return_value = 100
        char.get_agility.return_value = 25
        return char

    @pytest.fixture
    def defender(self):
        """创建防御者."""
        char = Mock()
        char.get_defense.return_value = 50
        char.get_agility.return_value = 20
        return char

    @pytest.fixture
    def calculator(self):
        """创建计算器实例."""
        return CombatCalculator()

    def test_calculate_hit_rate_base(self, calculator, attacker, defender):
        """测试基础命中率计算."""
        hit_rate = calculator.calculate_hit_rate(attacker, defender, None)
        
        # 基础命中90%，敏捷差5点，每点0.5%，总命中92.5%
        # 限制在0.3-0.95范围
        assert hit_rate == 0.925

    def test_calculate_hit_rate_agility_advantage(self, calculator, attacker, defender):
        """测试敏捷优势提高命中率."""
        # 攻击者敏捷远高于防御者
        attacker.get_agility.return_value = 50
        defender.get_agility.return_value = 10
        
        hit_rate = calculator.calculate_hit_rate(attacker, defender, None)
        
        # 应该接近最大命中率0.95
        assert hit_rate == 0.95

    def test_calculate_hit_rate_agility_disadvantage(self, calculator, attacker, defender):
        """测试敏捷劣势降低命中率."""
        # 攻击者敏捷远低于防御者
        attacker.get_agility.return_value = 10
        defender.get_agility.return_value = 50
        
        hit_rate = calculator.calculate_hit_rate(attacker, defender, None)
        
        # 命中率 = 0.9 + (10-50)*0.005 = 0.7
        assert hit_rate == 0.7

    def test_calculate_hit_rate_minimum_cap(self, calculator, attacker, defender):
        """测试命中率下限."""
        # 极大敏捷劣势
        attacker.get_agility.return_value = 0
        defender.get_agility.return_value = 1000
        
        hit_rate = calculator.calculate_hit_rate(attacker, defender, None)
        
        assert hit_rate == 0.3  # 最小值

    def test_calculate_hit_rate_maximum_cap(self, calculator, attacker, defender):
        """测试命中率上限."""
        # 极大敏捷优势
        attacker.get_agility.return_value = 1000
        defender.get_agility.return_value = 0
        
        hit_rate = calculator.calculate_hit_rate(attacker, defender, None)
        
        assert hit_rate == 0.95  # 最大值

    def test_calculate_damage_hit(self, calculator, attacker, defender):
        """测试伤害计算（命中情况）."""
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.return_value = 0.1  # 确保命中
            mock_random.uniform.return_value = 1.0  # 无浮动
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert result.is_hit is True
            assert result.damage > 0

    def test_calculate_damage_miss(self, calculator, attacker, defender):
        """测试伤害计算（未命中情况）."""
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.return_value = 0.99  # 确保未命中（超过命中率）
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert result.is_hit is False
            assert result.damage == 0

    def test_calculate_damage_with_move(self, calculator, attacker, defender):
        """测试使用招式的伤害计算."""
        move = Mock()
        move.wuxue_type = None  # 简化测试
        move.hit_modifier = 0.0  # 设置命中修正
        move.damage_multiplier = 1.5  # 设置伤害倍率
        
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.return_value = 0.1  # 命中
            mock_random.uniform.return_value = 1.0  # 无浮动
            
            result = calculator.calculate_damage(attacker, defender, move, None)
            
            assert result.is_hit is True
            # 招式有1.5倍率，基础攻击100，防御减免后应该更高
            assert result.damage > 0

    def test_calculate_damage_crit(self, calculator, attacker, defender):
        """测试暴击伤害."""
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.side_effect = [0.01, 0.01]  # 命中且暴击（< 0.05）
            mock_random.uniform.return_value = 1.0
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert result.is_crit is True
            assert result.is_hit is True
            assert result.damage > 0

    def test_calculate_damage_no_crit(self, calculator, attacker, defender):
        """测试非暴击伤害."""
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.side_effect = [0.1, 0.2]  # 命中但不暴击（> 0.05）
            mock_random.uniform.return_value = 1.0
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert result.is_crit is False
            assert result.is_hit is True

    def test_calculate_damage_variance(self, calculator, attacker, defender):
        """测试伤害浮动."""
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.return_value = 0.1  # 命中
            mock_random.uniform.return_value = 1.1  # 10%上浮
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert result.damage > 0

    def test_calculate_damage_with_messages(self, calculator, attacker, defender):
        """测试伤害计算返回消息."""
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.return_value = 0.1  # 命中
            mock_random.uniform.return_value = 1.0
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert isinstance(result.messages, list)

    def test_calculate_damage_minimum_one(self, calculator, attacker, defender):
        """测试最小伤害为1."""
        # 极弱攻击 vs 极强防御
        attacker.get_attack.return_value = 1
        defender.get_defense.return_value = 1000
        
        with patch('src.game.combat.calculator.random') as mock_random:
            mock_random.random.return_value = 0.1
            mock_random.uniform.return_value = 1.0
            
            result = calculator.calculate_damage(attacker, defender, None, None)
            
            assert result.damage >= 1

    def test_get_environment_bonus_empty(self, calculator):
        """测试无环境时的加成."""
        bonus = calculator.get_environment_bonus(None)
        
        assert bonus == {"damage": 1.0, "hit": 1.0}

    def test_get_environment_bonus_no_room(self, calculator):
        """测试无房间时的加成."""
        context = Mock()
        context.environment = None
        
        bonus = calculator.get_environment_bonus(context)
        
        assert bonus == {"damage": 1.0, "hit": 1.0}

    def test_get_environment_bonus_darkness(self, calculator):
        """测试黑暗环境对命中率的影响."""
        room = Mock()
        room.environment = {"light": 20}  # 低光照
        
        context = Mock()
        context.environment = room
        
        bonus = calculator.get_environment_bonus(context)
        
        assert bonus["hit"] < 1.0  # 命中率降低

    def test_get_environment_bonus_normal_light(self, calculator):
        """测试正常光照无惩罚."""
        room = Mock()
        room.environment = {"light": 100}  # 正常光照
        
        context = Mock()
        context.environment = room
        
        bonus = calculator.get_environment_bonus(context)
        
        assert bonus["hit"] == 1.0

    def test_get_environment_bonus_high_ground(self, calculator):
        """测试高地伤害加成."""
        room = Mock()
        room.environment = {"terrain": "high_ground"}
        
        context = Mock()
        context.environment = room
        
        bonus = calculator.get_environment_bonus(context)
        
        assert bonus["damage"] > 1.0  # 伤害增加


from unittest.mock import patch
