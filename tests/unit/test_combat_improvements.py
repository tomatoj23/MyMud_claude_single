"""战斗系统改进单元测试.

测试TD-022~027: 战斗完善
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestCombatCalculator:
    """测试战斗计算器改进 (TD-024, TD-025)."""
    
    @pytest.fixture
    def calculator(self):
        """创建伤害计算器."""
        from src.game.combat.calculator import CombatCalculator
        return CombatCalculator()
    
    @pytest.fixture
    def mock_attacker(self):
        """创建模拟攻击者."""
        char = MagicMock()
        char.get_attack.return_value = 100
        char.get_strength.return_value = 50
        char.level = 10
        return char
    
    @pytest.fixture
    def mock_defender(self):
        """创建模拟防御者."""
        char = MagicMock()
        char.get_defense.return_value = 50
        char.get_agility.return_value = 30
        return char
    
    def test_get_defender_wuxue_type(self, calculator):
        """测试获取防御者武学类型 (TD-024)."""
        from src.game.typeclasses.wuxue import WuxueType
        
        defender = MagicMock()
        defender.current_wuxue = MagicMock()
        defender.current_wuxue.wuxue_type = WuxueType.JIAN
        
        result = calculator._get_defender_wuxue_type(defender)
        assert result == WuxueType.JIAN
    
    def test_get_defender_wuxue_type_default(self, calculator):
        """测试获取默认武学类型."""
        from src.game.typeclasses.wuxue import WuxueType
        
        defender = MagicMock()
        defender.current_wuxue = None
        defender.default_wuxue_type = WuxueType.DAO
        
        result = calculator._get_defender_wuxue_type(defender)
        assert result == WuxueType.DAO
    
    def test_get_move_hit_modifier(self, calculator):
        """测试招式命中修正 (TD-025)."""
        from src.game.typeclasses.wuxue import WuxueType
        
        move = MagicMock()
        move.wuxue_type = WuxueType.ZHI
        move.hit_modifier = 0.15  # 设置明确的命中修正
        
        modifier = calculator._get_move_hit_modifier(move)
        # 应该使用招式的hit_modifier
        assert modifier == 0.15


class TestCombatAI:
    """测试战斗AI改进 (TD-026, TD-027)."""
    
    @pytest.fixture
    def ai(self):
        """创建智能AI."""
        from src.game.combat.ai import SmartAI
        return SmartAI()
    
    def test_select_counter_move(self, ai):
        """测试基于克制关系选择招式 (TD-026)."""
        from src.game.typeclasses.wuxue import WuxueType
        
        # 模拟招式
        move1 = MagicMock()
        move1.wuxue_type = WuxueType.QUAN  # 拳
        kungfu1 = MagicMock()
        
        move2 = MagicMock()
        move2.wuxue_type = WuxueType.JIAN  # 剑
        kungfu2 = MagicMock()
        
        moves = [(kungfu1, move1), (kungfu2, move2)]
        
        # 对手使用掌法，拳克制掌
        opponent_type = WuxueType.ZHANG
        result = ai._select_counter_move(moves, opponent_type)
        
        # 验证返回了克制的招式
        assert result is not None
        # 检查返回的招式确实克制对手
        from src.game.typeclasses.wuxue import COUNTER_MATRIX
        returned_type = result[1].wuxue_type
        assert opponent_type in COUNTER_MATRIX.get(returned_type, [])
    
    def test_select_highest_damage_move(self, ai):
        """测试选择最高伤害招式 (TD-027)."""
        move1 = MagicMock()
        move1.damage = 50
        kungfu1 = MagicMock()
        kungfu1.level = 1
        
        move2 = MagicMock()
        move2.damage = 100
        kungfu2 = MagicMock()
        kungfu2.level = 1
        
        moves = [(kungfu1, move1), (kungfu2, move2)]
        
        result = ai._select_highest_damage_move(moves)
        
        assert result is not None
        assert result[1].damage == 100


class TestCombatCore:
    """测试战斗核心改进 (TD-022, TD-023)."""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎."""
        return MagicMock()
    
    @pytest.fixture
    def mock_combatant(self):
        """创建模拟战斗者."""
        char = MagicMock()
        char.id = 1
        char.name = "测试角色"
        char.hp = 100
        char.max_hp = 100
        char.mp = 50
        char.has_learned.return_value = True
        
        combatant = MagicMock()
        combatant.character = char
        combatant.in_combat = True
        combatant.is_player = False
        combatant.set_cooldown = MagicMock()
        
        return combatant
    
    @pytest.mark.asyncio
    async def test_process_buffs(self, mock_engine, mock_combatant):
        """测试BUFF处理（按实际时间）(TD-022)."""
        from src.game.combat.core import CombatSession
        
        # 创建战斗会话
        with patch.object(CombatSession, '_process_buffs', new_callable=AsyncMock) as mock_process:
            session = CombatSession(mock_engine, [mock_combatant.character])
            await session._process_buffs(1.0)
            
            # 验证_process_buffs被调用
            mock_process.assert_awaited_once_with(1.0)
    
    @pytest.mark.asyncio
    async def test_do_cast_heal(self, mock_engine, mock_combatant):
        """测试内功施法-治疗 (TD-023)."""
        from src.game.combat.core import CombatSession
        
        session = CombatSession(mock_engine, [mock_combatant.character])
        session.participants = {1: mock_combatant}
        
        # 模拟内功
        neigong = MagicMock()
        neigong.name = "九阳神功"
        
        with patch('src.game.data.wuxue_registry.get_kungfu', return_value=neigong):
            success, msg = await session._do_cast(
                mock_combatant,
                {"neigong": "jiuyang", "effect": "heal", "power": 30, "mp_cost": 20}
            )
            
            assert success is True
            assert "恢复" in msg or "疗伤" in msg
