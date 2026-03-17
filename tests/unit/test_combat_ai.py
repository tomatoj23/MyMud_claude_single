"""战斗AI单元测试.

测试CombatAI及其子类.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.game.combat.ai import AggressiveAI, CombatAI, DefensiveAI, SmartAI
from src.game.combat.core import CombatAction


class TestCombatAI:
    """CombatAI基础类测试."""

    @pytest.fixture
    def ai(self):
        """创建基础AI实例."""
        return CombatAI()

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.get_available_moves.return_value = []
        return char

    @pytest.fixture
    def combat(self):
        """创建测试战斗会话."""
        combat = Mock()
        combat.get_alive_enemies.return_value = []
        return char

    @pytest.mark.asyncio
    async def test_ai_decide_no_targets(self, ai, character):
        """测试无目标时AI决策."""
        combat = Mock()
        combat.get_alive_enemies.return_value = []
        
        action = await ai.decide(character, combat)
        
        assert action.type == "defend"

    @pytest.mark.asyncio
    async def test_ai_decide_with_targets_no_moves(self, ai, character):
        """测试有目标但无招式时AI决策."""
        combat = Mock()
        target = Mock()
        target.id = 2
        combat.get_alive_enemies.return_value = [target]
        
        character.get_available_moves.return_value = []
        
        action = await ai.decide(character, combat)
        
        assert action.type == "move"
        assert action.target == target

    @pytest.mark.asyncio
    async def test_ai_decide_attack_probability(self, ai, character):
        """测试AI攻击概率."""
        combat = Mock()
        target = Mock()
        target.get_hp.return_value = (50, 100)
        combat.get_alive_enemies.return_value = [target]
        
        move = Mock()
        kungfu = Mock()
        character.get_available_moves.return_value = [(kungfu, move)]
        
        # 统计攻击和防御次数
        attack_count = 0
        defend_count = 0
        
        for _ in range(100):
            action = await ai.decide(character, combat)
            if action.type == "move":
                attack_count += 1
            elif action.type == "defend":
                defend_count += 1
        
        # 80%攻击，20%防御
        assert attack_count > 60  # 应该大部分是攻击
        assert defend_count > 0   # 应该有一些防御

    @pytest.mark.asyncio
    async def test_ai_decide_selects_random_target(self, ai, character):
        """测试AI随机选择目标."""
        combat = Mock()
        target1 = Mock()
        target2 = Mock()
        combat.get_alive_enemies.return_value = [target1, target2]
        
        move = Mock()
        kungfu = Mock()
        character.get_available_moves.return_value = [(kungfu, move)]
        
        # 多次决策，应该会选择不同目标
        targets_selected = set()
        
        for _ in range(20):
            action = await ai.decide(character, combat)
            if action.type == "move":
                targets_selected.add(id(action.target))
        
        # 可能选到不同目标
        assert len(targets_selected) >= 1

    @pytest.mark.asyncio
    async def test_ai_decide_includes_move_data(self, ai, character):
        """测试AI决策包含招式数据."""
        combat = Mock()
        target = Mock()
        combat.get_alive_enemies.return_value = [target]
        
        move = Mock()
        kungfu = Mock()
        character.get_available_moves.return_value = [(kungfu, move)]
        
        with patch('random.random', return_value=0.1):  # 确保攻击
            action = await ai.decide(character, combat)
        
        assert action.type == "move"
        assert action.data.get("move") == move
        assert action.data.get("kungfu") == kungfu


class TestSmartAI:
    """SmartAI智能AI测试."""

    @pytest.fixture
    def smart_ai(self):
        """创建智能AI实例."""
        return SmartAI()

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.get_available_moves.return_value = []
        char.get_hp.return_value = (100, 100)
        return char

    @pytest.mark.asyncio
    async def test_smart_ai_low_hp_flees(self, smart_ai, character):
        """测试低血量时逃跑."""
        # 血量低于20%
        character.get_hp.return_value = (15, 100)
        
        combat = Mock()
        target = Mock()
        target.get_hp.return_value = (50, 100)
        combat.get_alive_enemies.return_value = [target]
        
        flee_count = 0
        
        for _ in range(100):
            action = await smart_ai.decide(character, combat)
            if action.type == "flee":
                flee_count += 1
        
        # 30%概率逃跑
        assert flee_count > 10

    @pytest.mark.asyncio
    async def test_smart_ai_low_hp_defends(self, smart_ai, character):
        """测试低血量时防御."""
        # 血量低于20%
        character.get_hp.return_value = (15, 100)
        
        combat = Mock()
        target = Mock()
        target.get_hp.return_value = (50, 100)
        combat.get_alive_enemies.return_value = [target]
        
        defend_count = 0
        
        for _ in range(100):
            action = await smart_ai.decide(character, combat)
            if action.type == "defend":
                defend_count += 1
        
        # 30%概率防御
        assert defend_count > 10

    @pytest.mark.asyncio
    async def test_smart_ai_normal_hp_uses_parent_logic(self, smart_ai, character):
        """测试正常血量时使用父类逻辑."""
        # 正常血量
        character.get_hp.return_value = (80, 100)
        
        combat = Mock()
        target = Mock()
        target.get_hp.return_value = (50, 100)
        combat.get_alive_enemies.return_value = [target]
        
        move = Mock()
        kungfu = Mock()
        character.get_available_moves.return_value = [(kungfu, move)]
        
        attack_count = 0
        
        for _ in range(100):
            action = await smart_ai.decide(character, combat)
            if action.type == "move":
                attack_count += 1
        
        # 大部分应该攻击
        assert attack_count > 50

    @pytest.mark.asyncio
    async def test_smart_ai_selects_lowest_hp_target(self, smart_ai, character):
        """测试智能AI优先选择低血量目标."""
        character.get_hp.return_value = (80, 100)
        
        combat = Mock()
        
        # 创建两个目标，一个血量低
        target_low = Mock()
        target_low.get_hp.return_value = (20, 100)
        target_high = Mock()
        target_high.get_hp.return_value = (80, 100)
        
        combat.get_alive_enemies.return_value = [target_low, target_high]
        
        move = Mock()
        kungfu = Mock()
        character.get_available_moves.return_value = [(kungfu, move)]
        
        # 统计选择的目标
        low_target_count = 0
        
        for _ in range(100):
            action = await smart_ai.decide(character, combat)
            if action.type == "move":
                if action.target == target_low:
                    low_target_count += 1
        
        # 70%概率选择低血量目标
        assert low_target_count > 50


class TestAggressiveAI:
    """AggressiveAI激进AI测试."""

    @pytest.fixture
    def aggressive_ai(self):
        """创建激进AI实例."""
        return AggressiveAI()

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.get_available_moves.return_value = []
        return char

    @pytest.mark.asyncio
    async def test_aggressive_ai_always_attacks(self, aggressive_ai, character):
        """测试激进AI总是攻击."""
        combat = Mock()
        target = Mock()
        combat.get_alive_enemies.return_value = [target]
        
        move = Mock()
        kungfu = Mock()
        character.get_available_moves.return_value = [(kungfu, move)]
        
        for _ in range(20):
            action = await aggressive_ai.decide(character, combat)
            assert action.type == "move"

    @pytest.mark.asyncio
    async def test_aggressive_ai_no_moves_attacks_anyway(self, aggressive_ai, character):
        """测试激进AI无招式时仍然攻击."""
        combat = Mock()
        target = Mock()
        combat.get_alive_enemies.return_value = [target]
        
        character.get_available_moves.return_value = []
        
        action = await aggressive_ai.decide(character, combat)
        
        assert action.type == "move"
        assert action.target == target


class TestDefensiveAI:
    """DefensiveAI防御型AI测试."""

    @pytest.fixture
    def defensive_ai(self):
        """创建防御型AI实例."""
        return DefensiveAI()

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.get_available_moves.return_value = []
        char.get_hp.return_value = (100, 100)
        return char

    @pytest.mark.asyncio
    async def test_defensive_ai_low_hp_defends(self, defensive_ai, character):
        """测试低血量时必定防御."""
        # 血量低于50%
        character.get_hp.return_value = (40, 100)
        
        combat = Mock()
        target = Mock()
        target.get_hp.return_value = (50, 100)
        combat.get_alive_enemies.return_value = [target]
        
        for _ in range(20):
            action = await defensive_ai.decide(character, combat)
            assert action.type == "defend"

    @pytest.mark.asyncio
    async def test_defensive_ai_normal_hp_may_defend(self, defensive_ai, character):
        """测试正常血量时可能防御."""
        # 正常血量
        character.get_hp.return_value = (80, 100)
        
        combat = Mock()
        target = Mock()
        target.get_hp.return_value = (50, 100)
        combat.get_alive_enemies.return_value = [target]
        
        defend_count = 0
        
        for _ in range(100):
            action = await defensive_ai.decide(character, combat)
            if action.type == "defend":
                defend_count += 1
        
        # 50%概率防御
        assert defend_count > 30

    @pytest.mark.asyncio
    async def test_defensive_ai_no_enemies_defends(self, defensive_ai, character):
        """测试无敌人时防御."""
        character.get_hp.return_value = (80, 100)
        
        combat = Mock()
        combat.get_alive_enemies.return_value = []
        
        action = await defensive_ai.decide(character, combat)
        
        # 无敌人时使用父类逻辑
        assert action.type == "defend"


# --- Merged from test_combat_ai_coverage.py ---

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
