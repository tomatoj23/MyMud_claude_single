"""战斗系统单元测试.

测试CombatSession, Combatant, CombatAction等核心类.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.game.combat.core import CombatAction, Combatant, CombatResult, CombatSession


class TestCombatResult:
    """CombatResult枚举测试."""

    def test_combat_result_values(self):
        """测试战斗结果值."""
        assert CombatResult.WIN.value == "win"
        assert CombatResult.LOSE.value == "lose"
        assert CombatResult.DRAW.value == "draw"
        assert CombatResult.FLEE.value == "flee"


class TestCombatant:
    """Combatant类测试."""

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.id = 1
        char.name = "测试角色"
        char.get_hp.return_value = (100, 100)
        return char

    def test_combatant_init(self, character):
        """测试Combatant初始化."""
        combatant = Combatant(character, is_player=True)
        
        assert combatant.character == character
        assert combatant.is_player is True
        assert combatant.next_action_time == 0.0
        assert combatant.in_combat is False

    def test_combatant_is_ready_default(self, character):
        """测试默认状态下可以行动."""
        combatant = Combatant(character)
        
        assert combatant.is_ready() is True

    def test_combatant_is_ready_after_cooldown(self, character):
        """测试设置冷却后可以行动检查."""
        combatant = Combatant(character)
        
        # 设置一个很短的冷却时间
        combatant.set_cooldown(0.001)
        assert combatant.is_ready() is False
        
        # 等待冷却结束
        import time
        time.sleep(0.002)
        assert combatant.is_ready() is True

    def test_combatant_set_cooldown(self, character):
        """测试设置冷却时间."""
        combatant = Combatant(character)
        
        now = time.time()
        combatant.set_cooldown(5.0)
        
        assert combatant.next_action_time > now
        assert combatant.next_action_time <= now + 6.0

    def test_combatant_get_remaining_cooldown(self, character):
        """测试获取剩余冷却时间."""
        combatant = Combatant(character)
        
        # 默认情况下没有冷却
        assert combatant.get_remaining_cooldown() == 0.0
        
        # 设置冷却
        combatant.set_cooldown(10.0)
        remaining = combatant.get_remaining_cooldown()
        assert remaining > 9.0  # 应该接近10秒
        assert remaining <= 10.0


class TestCombatAction:
    """CombatAction类测试."""

    def test_combat_action_init(self):
        """测试CombatAction初始化."""
        action = CombatAction("move", None, {"damage": 10})
        
        assert action.type == "move"
        assert action.target is None
        assert action.data == {"damage": 10}

    def test_combat_action_default_data(self):
        """测试CombatAction默认数据为空字典."""
        action = CombatAction("defend")
        
        assert action.type == "defend"
        assert action.data == {}


class TestCombatSession:
    """CombatSession类测试."""

    @pytest.fixture
    def mock_engine(self):
        """创建测试引擎."""
        return Mock()

    @pytest.fixture
    def player_char(self):
        """创建玩家角色."""
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.get_agility.return_value = 20
        char.get_attack.return_value = 50
        char.get_defense.return_value = 30
        char.modify_hp = Mock(return_value=10)
        return char

    @pytest.fixture
    def enemy_char(self):
        """创建敌人角色."""
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        char.get_agility.return_value = 15
        char.get_attack.return_value = 40
        char.get_defense.return_value = 20
        char.modify_hp = Mock(return_value=10)
        return char

    def test_combat_session_init(self, mock_engine, player_char, enemy_char):
        """测试CombatSession初始化."""
        session = CombatSession(
            mock_engine,
            [player_char, enemy_char],
            player_character=player_char
        )
        
        assert session.engine == mock_engine
        assert len(session.participants) == 2
        assert session.active is False
        assert 1 in session.participants  # 玩家
        assert 2 in session.participants  # 敌人
        
        # 检查玩家标记
        assert session.participants[1].is_player is True
        assert session.participants[2].is_player is False

    def test_combat_session_init_no_player(self, mock_engine, player_char, enemy_char):
        """测试CombatSession初始化（无指定玩家）."""
        session = CombatSession(
            mock_engine,
            [player_char, enemy_char]
        )
        
        # 所有人都是NPC
        assert session.participants[1].is_player is False
        assert session.participants[2].is_player is False

    @pytest.mark.asyncio
    async def test_combat_session_start_stop(self, mock_engine, player_char, enemy_char):
        """测试战斗开始和停止."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        
        # 模拟战斗循环快速结束
        with patch.object(session, '_combat_loop', new_callable=AsyncMock) as mock_loop:
            await session.start()
            
            assert session.active is True
            assert player_char.at_combat_start.called
            assert enemy_char.at_combat_start.called
            
            await session.stop(CombatResult.WIN)
            
            assert session.active is False
            assert session.result == CombatResult.WIN
            assert player_char.at_combat_end.called
            assert enemy_char.at_combat_end.called

    def test_can_fight_alive(self, mock_engine, player_char):
        """测试检查存活角色可以战斗."""
        session = CombatSession(mock_engine, [player_char])
        
        player_char.get_hp.return_value = (50, 100)
        assert session._can_fight(player_char) is True

    def test_can_fight_dead(self, mock_engine, player_char):
        """测试检查死亡角色不能战斗."""
        session = CombatSession(mock_engine, [player_char])
        
        player_char.get_hp.return_value = (0, 100)
        assert session._can_fight(player_char) is False

    def test_calculate_cooldown_base(self, mock_engine, player_char):
        """测试基础冷却时间计算."""
        session = CombatSession(mock_engine, [player_char])
        
        # 无招式时使用基础冷却
        cooldown = session._calculate_cooldown(player_char, None)
        assert cooldown >= session.MIN_COOLDOWN
        assert cooldown <= session.BASE_COOLDOWN

    def test_calculate_cooldown_with_move(self, mock_engine, player_char):
        """测试带招式的冷却时间计算."""
        session = CombatSession(mock_engine, [player_char])
        
        move = Mock()
        move.cooldown = 5.0
        
        cooldown = session._calculate_cooldown(player_char, move)
        # 敏捷20，冷却减免约40%
        # 5.0 * 0.6 = 3.0
        assert cooldown >= session.MIN_COOLDOWN
        assert cooldown < 5.0

    def test_calculate_cooldown_agility_effect(self, mock_engine, player_char):
        """测试敏捷对冷却时间的影响."""
        session = CombatSession(mock_engine, [player_char])
        
        # 低敏捷角色
        low_agility_char = Mock()
        low_agility_char.get_agility.return_value = 5
        
        # 高敏捷角色
        high_agility_char = Mock()
        high_agility_char.get_agility.return_value = 40
        
        move = Mock()
        move.cooldown = 0  # 使用基础冷却
        
        low_cd = session._calculate_cooldown(low_agility_char, move)
        high_cd = session._calculate_cooldown(high_agility_char, move)
        
        # 高敏捷应该有更短冷却
        assert high_cd < low_cd

    def test_calculate_cooldown_minimum(self, mock_engine, player_char):
        """测试最小冷却时间限制."""
        session = CombatSession(mock_engine, [player_char])
        
        # 极高敏捷的角色
        super_agility_char = Mock()
        super_agility_char.get_agility.return_value = 100
        
        cooldown = session._calculate_cooldown(super_agility_char, None)
        assert cooldown >= session.MIN_COOLDOWN

    def test_get_alive_enemies(self, mock_engine, player_char, enemy_char):
        """测试获取存活敌人列表."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        
        enemies = session.get_alive_enemies(player_char)
        assert len(enemies) == 1
        assert enemies[0] == enemy_char

    def test_get_alive_enemies_none(self, mock_engine, player_char):
        """测试无敌人时返回空列表."""
        session = CombatSession(mock_engine, [player_char])
        
        enemies = session.get_alive_enemies(player_char)
        assert enemies == []

    def test_is_in_combat(self, mock_engine, player_char):
        """测试检查角色是否在战斗中."""
        session = CombatSession(mock_engine, [player_char])
        
        # 初始不在战斗中
        assert session.is_in_combat(player_char) is False
        
        # 手动设置为战斗中
        session.participants[player_char.id].in_combat = True
        assert session.is_in_combat(player_char) is True

    def test_log(self, mock_engine, player_char):
        """测试战斗日志."""
        session = CombatSession(mock_engine, [player_char])
        
        session._log("测试消息1")
        session._log("测试消息2")
        
        assert "测试消息1" in session.log
        assert "测试消息2" in session.log

    @pytest.mark.asyncio
    async def test_check_end_win(self, mock_engine, player_char, enemy_char):
        """测试战斗胜利判定."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_character=player_char)
        
        # 敌人死亡
        enemy_char.get_hp.return_value = (0, 80)
        
        result = await session._check_end()
        assert result == CombatResult.WIN
        assert session.winner == player_char

    @pytest.mark.asyncio
    async def test_check_end_draw(self, mock_engine, player_char, enemy_char):
        """测试战斗平局判定（双方死亡）."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        
        # 双方死亡
        player_char.get_hp.return_value = (0, 100)
        enemy_char.get_hp.return_value = (0, 80)
        
        result = await session._check_end()
        assert result == CombatResult.DRAW

    @pytest.mark.asyncio
    async def test_check_end_continue(self, mock_engine, player_char, enemy_char):
        """测试战斗继续判定."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        
        # 双方都存活
        result = await session._check_end()
        assert result is None
