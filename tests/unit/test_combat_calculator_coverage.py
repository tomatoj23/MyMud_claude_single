"""Combat Calculator 覆盖率补充测试."""
import pytest
from unittest.mock import Mock, patch

from src.game.combat.calculator import CombatCalculator, DamageResult, CombatContext


class TestCombatCalculatorCoverage:
    """补充 CombatCalculator 未覆盖的分支."""

    def test_get_environment_bonus_no_context(self):
        """测试没有context时的环境加成."""
        calculator = CombatCalculator()
        result = calculator.get_environment_bonus(None)
        
        assert result == {"damage": 1.0, "hit": 1.0}

    def test_get_environment_bonus_no_environment(self):
        """测试没有environment时的环境加成."""
        calculator = CombatCalculator()
        context = Mock()
        context.environment = None
        
        result = calculator.get_environment_bonus(context)
        
        assert result == {"damage": 1.0, "hit": 1.0}

    def test_get_environment_bonus_non_dict_env(self):
        """测试environment不是dict时的环境加成."""
        calculator = CombatCalculator()
        context = Mock()
        room = Mock()
        room.environment = "invalid"  # 不是dict
        context.environment = room
        
        result = calculator.get_environment_bonus(context)
        
        assert result == {"damage": 1.0, "hit": 1.0}

    def test_calculate_hit_rate_extreme_agility_advantage(self):
        """测试极端敏捷优势时的命中率（应被限制在最大值）."""
        character = Mock()
        target = Mock()
        # 极端敏捷差距
        character.get_agility.return_value = 1000
        target.get_agility.return_value = 1
        
        calculator = CombatCalculator()
        hit_rate = calculator.calculate_hit_rate(character, target, None)
        
        # 命中率应该被限制在95%
        assert hit_rate == 0.95

    def test_calculate_damage_with_move_counter(self):
        """测试使用招式时的克制消息."""
        character = Mock()
        target = Mock()
        character.get_attack.return_value = 100
        target.get_defense.return_value = 50
        character.get_agility.return_value = 50
        target.get_agility.return_value = 50
        
        move = Mock()
        move.wuxue_type = Mock()
        move.hit_modifier = 0.0  # 设置命中修正
        
        calculator = CombatCalculator()
        
        # 模拟克制（>1.0）
        with patch('src.game.typeclasses.wuxue.get_counter_modifier', return_value=1.5):
            with patch('random.random', return_value=0.5):  # 命中
                with patch.object(calculator, 'BASE_CRIT_RATE', 0.0):  # 不暴击
                    context = Mock()
                    context.environment = None
                    result = calculator.calculate_damage(character, target, move, context)
                    
                    assert "招式克制" in str(result.messages)

    def test_calculate_damage_countered(self):
        """测试被克制时的消息."""
        character = Mock()
        target = Mock()
        character.get_attack.return_value = 100
        target.get_defense.return_value = 50
        character.get_agility.return_value = 50
        target.get_agility.return_value = 50
        
        move = Mock()
        move.wuxue_type = Mock()
        move.hit_modifier = 0.0  # 设置命中修正
        
        calculator = CombatCalculator()
        
        # 模拟被克制（<1.0）
        with patch('src.game.typeclasses.wuxue.get_counter_modifier', return_value=0.5):
            with patch('random.random', return_value=0.5):  # 命中
                with patch.object(calculator, 'BASE_CRIT_RATE', 0.0):  # 不暴击
                    context = Mock()
                    context.environment = None
                    result = calculator.calculate_damage(character, target, move, context)
                    
                    assert "招式被克" in str(result.messages)

    def test_calculate_damage_with_crit(self):
        """测试暴击时生成暴击消息."""
        character = Mock()
        target = Mock()
        character.get_attack.return_value = 100
        target.get_defense.return_value = 50
        character.get_agility.return_value = 50
        target.get_agility.return_value = 50
        
        calculator = CombatCalculator()
        
        # 强制暴击
        with patch('random.random', side_effect=[0.1, 0.01]):  # 第一次命中，第二次暴击
            context = Mock()
            context.environment = None
            result = calculator.calculate_damage(character, target, None, context)
            
            assert result.is_crit is True
            assert any("暴击" in msg for msg in result.messages)

    def test_calculate_damage_no_crit(self):
        """测试非暴击时没有暴击消息."""
        character = Mock()
        target = Mock()
        character.get_attack.return_value = 100
        target.get_defense.return_value = 50
        character.get_agility.return_value = 50
        target.get_agility.return_value = 50
        
        calculator = CombatCalculator()
        
        # 强制不暴击
        with patch('random.random', side_effect=[0.1, 0.99]):  # 第一次命中，第二次不暴击
            context = Mock()
            context.environment = None
            result = calculator.calculate_damage(character, target, None, context)
            
            assert result.is_crit is False
            assert not any("暴击" in msg for msg in result.messages)

    def test_calculate_damage_minimum_one_edge_case(self):
        """测试伤害最小值为1的边界情况."""
        character = Mock()
        target = Mock()
        # 攻击力极低，防御力极高
        character.get_attack.return_value = 1
        target.get_defense.return_value = 1000
        character.get_agility.return_value = 50
        target.get_agility.return_value = 50
        
        calculator = CombatCalculator()
        
        with patch('random.random', return_value=0.1):  # 命中
            context = Mock()
            context.environment = None
            result = calculator.calculate_damage(character, target, None, context)
            
            # 伤害至少为1
            assert result.damage >= 1

    def test_get_environment_bonus_fog(self):
        """测试雾天环境加成."""
        calculator = CombatCalculator()
        context = Mock()
        room = Mock()
        room.environment = {"weather": "fog"}
        context.environment = room
        
        result = calculator.get_environment_bonus(context)
        
        assert result["hit"] == 0.9

    def test_get_environment_bonus_dark(self):
        """测试黑暗环境加成."""
        calculator = CombatCalculator()
        context = Mock()
        room = Mock()
        room.environment = {"light": 10}
        context.environment = room
        
        result = calculator.get_environment_bonus(context)
        
        assert result["hit"] == 0.8

    def test_get_environment_bonus_high_ground(self):
        """测试高地环境加成."""
        calculator = CombatCalculator()
        context = Mock()
        room = Mock()
        room.environment = {"terrain": "high_ground"}
        context.environment = room
        
        result = calculator.get_environment_bonus(context)
        
        assert result["damage"] == 1.1

    def test_get_environment_bonus_rain(self):
        """测试雨天环境（当前无效果，但代码分支存在）."""
        calculator = CombatCalculator()
        context = Mock()
        room = Mock()
        room.environment = {"weather": "rain"}
        context.environment = room
        
        result = calculator.get_environment_bonus(context)
        
        # 雨天当前没有实现具体效果，但代码分支应该被访问
        assert result["damage"] == 1.0
        assert result["hit"] == 1.0


class TestDamageResultCoverage:
    """补充 DamageResult 未覆盖的分支."""

    def test_damage_result_no_messages(self):
        """测试没有消息时的DamageResult."""
        result = DamageResult(damage=10, is_hit=True, messages=[])
        
        assert result.messages == []

    def test_damage_result_default_messages(self):
        """测试默认消息列表."""
        result = DamageResult(damage=10, is_hit=True)
        
        assert result.messages == []


class TestCombatContext:
    """测试 CombatContext 初始化."""

    def test_combat_context_init(self):
        """测试 CombatContext 初始化."""
        caster = Mock()
        target = Mock()
        environment = Mock()
        
        context = CombatContext(caster, target, environment, round_num=5)
        
        assert context.caster == caster
        assert context.target == target
        assert context.environment == environment
        assert context.round_num == 5
